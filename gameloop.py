from typing import *

import keyboard as kb
import pyautogui as pag

import os
import win32api
import win32con
import win32gui
from win32gui import LoadImage, LR_LOADFROMFILE

from PIL import Image, ImageTk
from pynput import mouse
from tkinter import Tk, Label, Toplevel, Canvas
from threading import Thread as th
from traceback import print_exc


class Area: # main window
	def __init__(self, timelines: list, cursor = None, bg_always_on_top: bool = False, minimize_windows: bool = True,
		bg_func: Callable = None, on_death: Callable = None, on_start: Callable = None, cursor_circle_radius: int = 3,
		on_tl_start: Callable = None, on_tl_death: Callable = None):
		self.timelines = timelines

		self.keyboard_thread = th(target=self.check_keyboard, daemon=True)
		self.keyboard_thread.start()

		if minimize_windows:
			os.system("explorer shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}") # minimizes every window like WIN+D

		self.root = Tk()
		self.root.title("WHAT root")

		self.pause_label = Label(self.root, text="PAUSED", font=("Arial", 34), bg="black", fg="white")
		self.pause_label.place(relx=0.5, rely=0.5, anchor="center")
		self.pause_label.place_forget()
		self.cursor_circle_radius = cursor_circle_radius

		if cursor:
			self.cursor = cursor
			self.cursor.set_window( Toplevel(self.root) )
			self.root.config(cursor="none")
		else:
			self.cursor = Cursor()

		self.screen_width = self.root.winfo_screenwidth()
		self.screen_height = self.root.winfo_screenheight()

		self.canvas = Canvas(self.root, width=self.screen_width, height=self.screen_height, bg="black", highlightthickness=0)
		self.canvas.pack()
		self.circle = self.canvas.create_oval(cursor_circle_radius, cursor_circle_radius, cursor_circle_radius, cursor_circle_radius, fill="white")

		self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

		self.root.overrideredirect(1)
		self.root.configure(bg="black")

		self.alpha = 0
		self.alive_time = 0
		self.dead = False
		self.bg_always_on_top = bg_always_on_top

		self.bg_func = bg_func
		self.on_death = on_death
		self.on_start = on_start
		self.on_tl_start = on_tl_start
		self.on_tl_death = on_tl_death

		self.timeline_index = 0
		self.paused = True
		self.pause_count = 0
		self.bg_animation_count = 0
		self.on_set_alpha_tl = 0

		if bg_always_on_top:
			self.root.wm_attributes("-topmost", 1)

		for i, timeline in enumerate(self.timelines):
			timeline.name = i

	def run(self, fps: int = 90): # starts main loop
		if callable(self.on_start):
			self.on_start(self)
		self.paused = False

		self.root.attributes('-alpha', float(self.timelines[0].bg_alpha))
		self.alpha = self.timelines[0].bg_alpha

		self.update(fps)
		self.root.mainloop()

	def update(self, fps: int): # updates every timeline, will be dead when every timeline is dead
		if self.bg_func:
			self.bg_func(self, fps)

		if not self.paused:
			for timeline in self.timelines:
				try:
					self.cursor.update()
					if self.cursor.position and self.cursor_circle_radius:
						self.canvas.coords(self.circle,
							self.cursor.position[0] - self.cursor_circle_radius,
							self.cursor.position[1] - self.cursor_circle_radius,
							self.cursor.position[0] + self.cursor_circle_radius,
							self.cursor.position[1] + self.cursor_circle_radius
							)

					is_dead = timeline.update(fps, self.cursor)

					if not timeline.initialized:
						self.init_timeline(timeline)
						if callable(self.on_tl_start):
							self.on_tl_start(self, fps)

					if not is_dead:
						if self.alpha != timeline.bg_alpha:
							if self.on_set_alpha_tl != self.timeline_index:
								self.root.attributes('-alpha', float(timeline.bg_alpha))
								self.alpha = timeline.bg_alpha
						break
					else:
						self.timeline_index += 1
						if callable(self.on_tl_death):
							self.on_tl_death(self, fps)

				except Exception as e:
					self.dead = True
					self.root.attributes('-alpha', 0.0)
					print_exc()
					return
			else:
				self.root.destroy()
				print("WHAT? END?")
			
		if not self.dead:
			self.alive_time += 1/fps
			self.root.after(int(1/fps*1000), self.update, fps)
		else:
			if callable(self.on_death):
				self.on_death(self, fps)
			self.root.destroy()

	def init_timeline(self, timeline):
		for i, obj in enumerate(timeline.objects):
			obj.set_window( Toplevel(self.root) ) # creates child window for every Window object
			obj.name = i
		timeline.initialized  = True

	def set_bg_alpha(self, alpha: Union[int, float, str]):
		if isinstance(alpha, int) or isinstance(alpha, float):
			if 0 <= alpha <= 1:
				self.alpha = alpha
				self.root.attributes('-alpha', alpha)
				self.on_set_alpha_tl = self.timeline_index
			else:
				raise ValueError(f"'alpha' must be float or integer from 0 to 1, not {alpha} {type(alpha)}")

		elif isinstance(alpha, str):
			if alpha[0] in ['-', '+'] and ( alpha[1:].isdigit() or is_float(alpha[1:]) ):
				new = eval(f'self.alpha{alpha}')
				print(self.alpha, new)

				if new <= 0:
					self.alpha = 0
				else:
					self.alpha = new

			else:
				raise ValueError(f"new_hp must be integer number greater than 0 or relative string number like '+100' or '-30', not {new_hp}")

	def check_keyboard(self): # logs keystrokes
		while 1:
			key = kb.read_event()

			if key.event_type == kb.KEY_DOWN:
				if key.name == 'esc':
					self.dead = True
					return

				if key.name == 'space':
					self.paused = not self.paused
					self.pause_count += 1

					if self.pause_label.winfo_viewable():
						self.pause_label.place_forget()
						self.root.config(cursor="none")
					else:
						self.pause_label.place(relx=0.5, rely=0.5, anchor="center")
						self.root.config(cursor="arrow")


class TimeLine: # it is a scene where contain child windows, you may use several scenes in one Area in sequience, one after another
	def __init__(self, objects: list, bg_alpha: Union[int, float] = 1, wait_time: int = 0, alive_time: int = -1, moments: dict = {},
		on_start: Callable = None, on_death: Callable = None):
		# objects: list of Window objects
		# wait_time: delay time before start in seconds
		self.name = 'independent_timeline'
		self.objects = objects
		self.bg_alpha = bg_alpha
		self.alive_time = 0
		self.wait_time = wait_time
		self.max_alive_time = alive_time
		self.moments = moments

		self.on_start = on_start
		self.on_death = on_death

		self.initialized = False
		self.started = False
		self.dead = False

	def update(self, fps: int, cursor): # returns true when every object is dead
		if self.initialized:
			self.alive_time += 1/fps
			if self.alive_time >= self.max_alive_time and self.max_alive_time != -1:
				return True

			if not self.started:
				if callable(self.on_start):
					self.on_start(fps, cursor)
				self.started = True

			for sec in self.moments.keys():
				if sec <= self.alive_time and self.moments[sec] != 'done':
					if callable(self.moments[sec]):
						self.moments[sec](fps, cursor)
						self.moments[sec] = 'done'
					elif callable(self.moments[sec]) and all([ callable(i) for i in self.moments[sec] ]):
						for func in self.moments[sec]:
							func(fps, cursor)
						self.moments[sec] = 'done'
					else:
						raise ValueError(
f"'moments' kwarg at TimeLine constructor must be dict with integer keys and callable or list of callable values ( functions must takes 2 arguments: fps, cursor )"
							)

			if self.alive_time >= self.wait_time:
				results = []
				for obj in self.objects:
					is_dead = obj.update(self, fps, cursor)
					results.append(not is_dead)

				res = all(results)
				if res and not self.dead:
					self.dead = True
					if callable(self.on_death):
						self.on_death(self, fps)

				return res
			else:
				return False
		else:
			return False


class Cursor:
	def __init__(self, hp: int = 1, radius: int = 0, on_death = None,
		image: Union[Image, str] = None, transparent_color: str = None, resize: List[[int, int]] = None, alpha: float = 1.0):
		'''
		radius: integer number, the "click zone" of cursor expands by this number in all directions. For example 1 gets rectangle 3x3 around cursor, 2 gets 5x5
		image: string path to image or PIL.Image object, makes cursor with this image
		transparent_color: string color name, like "black". If you indicated kwarg image, you can remove some color from it. If transparent_color="black" will be removed black color from image
		resize: list with 2 integers. If you indicated kwarg image, you can resize cursor image
		alpha: float from 0 to 1, it is cursor window alpha, level of transparency
		'''
		if hp >= 0:
			self.hp = hp
		else:
			self.hp = 0

		self.on_death = on_death
		self.dead = False

		if isinstance(radius, int):
			if radius >= 0:
				self.radius = radius
			else:
				raise ValueError(f"'radius' must be integer >= 0, not {radius} {type(radius)}")
		else:
			raise ValueError(f"'radius' must be integer >= 0, not {radius} {type(radius)}")

		if isinstance(image, str):
			self.image = Image.open(image)
		elif isinstance(image, str):
			self.image = image
		else:
			self.image = None

		self.root = None
		self.transparent_color = transparent_color

		if isinstance(alpha, float) or isinstance(alpha, int):
			if 0 <= alpha <= 1:
				self.alpha = alpha
			else:
				raise ValueError(f"'alpha' must be float or integer from 0 to 1, not {alpha} {type(alpha)}")
		else:
			raise ValueError(f"'alpha' must be float or integer from 0 to 1, not {alpha} {type(alpha)}")

		if resize and isinstance(resize, list):
			if len(resize) == 2 and isinstance(resize[0], int) and isinstance(resize[1], int):
				if resize[0] > 0 and resize[1] > 0:
					self.image = self.image.resize(resize)
				else:
					raise ValueError(f"'resize' elements must be more than 0, not {resize}")
			else:
				raise ValueError(f"'resize' must be list with 2 integers, not {resize}")

		self.position = None
		self.pressed_button = None

		self.mouse_thread = mouse.Listener(on_move=self.on_mouse_move, on_click=self.on_mouse_click, daemon=True)
		self.mouse_thread.start()

	def set_hp(self, new_hp: Union[int, str]):
		if isinstance(new_hp, int):
			if new_hp < 0:
				self.hp = 0
				if callable(self.on_death) and not self.dead:
					self.on_death()
					self.dead = True
			else:			
				self.hp = new_hp

		elif isinstance(new_hp, str):
			if new_hp[0] in ['-', '+'] and new_hp[1:].isdigit():
				new = eval(f'self.hp{new_hp}')

				if new < 0:
					self.hp = 0
					if callable(self.on_death) and not self.dead:
						self.on_death()
						self.dead = True
				else:
					self.hp = new
			else:
				raise ValueError(f"new_hp must be integer number greater than 0 or relative string number like '+100' or '-30', not {new_hp}")
		else:
			raise ValueError(f"new_hp must be integer number greater than 0 or relative string number like '+100' or '-30', not {new_hp}")

	def intersect(self, mouse_position: list, box: list):
		if isinstance(mouse_position, list):
			if len(mouse_position) == 2 and all([ isinstance(i, int) for i in mouse_position ]):
				if isinstance(box, list):
					if len(box) == 2 and all([ len(i) == 2 and isinstance(i[0], int) and isinstance(i[1], int) and i[0] >= 0 and i[1] >= 0 for i in box ]):

						positions = [ box[0], box[1], (box[0][0], box[1][1]), (box[1][0], box[0][1]) ]
						x, y = mouse_position

						for pos in positions:
							if pos[0] in range(x - self.radius, x + self.radius) and pos[1] in range(y - self.radius, y + self.radius):
								return True

						return False

					else:
						raise ValueError(f"'box' must be list with 2 positions ( 2 lists with 2 integers >= 0 ), like [ (0, 0), (1, 1) ], not {box}, {type(box)}")
				else:
					raise ValueError(f"'box' must be list with 2 positions ( 2 lists with 2 integers >= 0 ), like [ (0, 0), (1, 1) ], not {box}, {type(box)}")
			else:
				raise ValueError(f"'mouse_position' must be list with 2 integers >= 0, like [0, 0], not {mouse_position} {type(mouse_position)}")
		else:
			raise ValueError(f"'mouse_position' must be list with 2 integers >= 0, like [0, 0], not {mouse_position} {type(mouse_position)}")

	def set_window(self, root: Union[Tk, Toplevel]):
		if self.image:
			self.root = root
			
			self.root.title("Cursor Window")

			if self.transparent_color:
				self.root.wm_attributes("-transparentcolor", self.transparent_color)

			self.root.config(cursor="none")
			self.root.attributes('-topmost', True)
			self.root.overrideredirect(True)
			self.root.attributes('-alpha', float(self.alpha))

			self.root.geometry(f"{self.image.size[0]}x{self.image.size[1]}")

			self.photo = ImageTk.PhotoImage(self.image)
			self.image_label = Label(root, image=self.photo)
			self.image_label.pack()

	def resize(self, size: List[[int, int]]):
		if size and isinstance(size, list):
			if len(size) == 2 and isinstance(size[0], int) and isinstance(size[1], int):
				if size[0] > 0 and size[1] > 0:
					self.image = self.image.resize(size)
					self.root.geometry(f"{self.image.size[0]}x{self.image.size[1]}+{self.position[0]}+{self.position[1]}")
				else:
					raise ValueError(f"'resize' elements must be more than 0, not {size}")
			else:
				raise ValueError(f"'resize' must be list with 2 integers, not {size}")

	def update(self):
		mouse_x, mouse_y = pag.position()

		if self.image:
			window_x = mouse_x - self.image.size[0] // 2
			window_y = mouse_y - self.image.size[1] // 2

			self.root.geometry(f"{self.image.size[0]}x{self.image.size[1]}+{window_x}+{window_y}")

	def on_mouse_move(self, x, y): # logs mouse position
		self.position = [x,y]

	def on_mouse_click(self, x, y, button, pressed): # logs mouse pressed button
		self.pressed_button = button if pressed else None


def is_float(string: str):
    try:
        float(string)
        return True
    except ValueError:
        return False