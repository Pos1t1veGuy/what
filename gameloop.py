from typing import *

import keyboard as kb
import pyautogui as pag

import time
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

from .types import Media, check_value


class Area: # main window
	def __init__(self, cursor = None, bg_always_on_top: bool = False, minimize_windows: bool = True,
		bg_func: Callable = None, on_death: Callable = None, on_start: Callable = None, cursor_circle_radius: int = 3,
		on_tl_start: Callable = None, on_tl_death: Callable = None, on_click: Callable = None,
		alpha: int = None, media: Media = None):

		self.timelines = []
		self.kb_thread_started = False
		self.keyboard_thread = th(target=self.check_keyboard, daemon=True)
		self.keyboard_thread.start()

		if minimize_windows:
			os.system("explorer shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}") # minimizes every window like WIN+D

		self.root = Tk()
		self.root.title("WHAT root")

		self.pause_label = Label(self.root, text="PAUSED", font=("Arial", 34), bg="black", fg="white")
		self.pause_label.place(relx=0.5, rely=0.5, anchor="center")
		self.pause_label.place_forget()
		check_value(cursor_circle_radius, int, exc_msg=f"'cursor_circle_radius' kwarg must be integer >= 0, not {cursor_circle_radius} {type(cursor_circle_radius)}")
		self.cursor_circle_radius = cursor_circle_radius

		if media:
			self.media_label = Label(self.root)
			self.media_label.pack(expand=True, anchor='center')
			self.media = media
			self.media.set_label(self.media_label)
		else:
			self.media = None
			self.media_label = None

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

		check_value(alpha, [int, float], exc_msg=f"'alpha' kwarg must be integer of float from 0 to 1, not {alpha} {type(alpha)}")
		self.alpha = alpha
		self.alive_time = 0
		self.stopping = False
		check_value(bg_always_on_top, [int, bool], exc_msg=f"'bg_always_on_top' kwarg must be bool, not {bg_always_on_top} {type(bg_always_on_top)}")
		self.bg_always_on_top = bg_always_on_top

		self.bg_func = bg_func
		self.on_death = on_death
		self.on_start = on_start
		self.on_tl_start = on_tl_start
		self.on_tl_death = on_tl_death
		self.on_click = on_click

		self.timeline_index = 0
		self.paused = True
		self.pause_count = 0
		self.bg_animation_count = 0
		self.on_set_alpha_tl = 0
		self.timeline_new_alpha = None
		self.realpha_speed = ''
		self.dead = False
		self.fps = 0
		self.key = None

		if bg_always_on_top:
			self.root.wm_attributes("-topmost", 1)

	def set_timelines(self, timelines: list):
		check_value(timelines, [tuple, list], exc_msg=f"'timelines' arg must be list of TimeLine objects, not {timelines} {type(timelines)}")
		self.timelines = timelines

		for i, timeline in enumerate(self.timelines):
			timeline.name = i

	def add_timeline(self, timeline):
		self.timelines.append(timeline)
		self.timelines[-1].name = self.timelines.index(self.timelines[-1])

	def run(self, fps: int = 90): # starts main loop
		if callable(self.on_start):
			self.on_start(self)
		self.paused = False

		self.fps = fps
		if self.alpha == None:
			self.alpha = self.timelines[0].bg_alpha
			self.root.attributes('-alpha', float(self.timelines[0].bg_alpha))

		#while not self.kb_thread_started:
			#time.sleep(0.3)

		self.update()
		self.root.mainloop()

	def update(self): # updates every timeline, will be dead when every timeline is dead
		start_time = time.time()
		if self.bg_func:
			self.bg_func(self, self.fps)

		if self.cursor.pressed_button and callable(self.on_click):
			self.on_click(self)

		if self.timeline_new_alpha != None and self.realpha_speed != '':
			if self.timeline_new_alpha < self.alpha and self.timeline_new_alpha < eval(f'self.alpha{self.realpha_speed}') and float(self.realpha_speed) < 0:
				self.set_alpha(self.realpha_speed)

			elif self.timeline_new_alpha > self.alpha and self.timeline_new_alpha > eval(f'self.alpha{self.realpha_speed}') and float(self.realpha_speed) > 0:
				self.set_alpha(self.realpha_speed)

			else:
				if self.timeline_new_alpha and ( isinstance(self.timeline_new_alpha, float) or isinstance(self.timeline_new_alpha, int) ) and 0 <= self.timeline_new_alpha <= 1:
					self.set_alpha(self.timeline_new_alpha)

				self.realpha_speed = ''
				self.timeline_new_alpha = None

		if self.dead and self.realpha_speed == '' and self.timeline_new_alpha == None:
			self.set_alpha(0)


		if not self.paused and not self.dead:

			if hasattr(self.media, 'update'):
				self.media.update(self, None, self.fps, self.cursor)

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

					is_dead = timeline.update(self.fps, self.cursor)

					if not timeline.initialized:
						self.init_timeline(timeline)
						if callable(self.on_tl_start):
							self.on_tl_start(self)

					if not is_dead:
						if self.alpha != timeline.bg_alpha:
							if self.on_set_alpha_tl != self.timeline_index:
								self.root.attributes('-alpha', float(timeline.bg_alpha))
								self.alpha = timeline.bg_alpha
						break
					else:
						self.timeline_index += 1
						if callable(self.on_tl_death):
							self.on_tl_death(self)

				except Exception as e:
					self.kill()
					print_exc()
					return
			else:
				self.kill()

		if self.alpha == 0 and self.dead:
			print("WHAT? END?")
			if callable(self.on_death):
				self.on_death(self)
			for timeline in self.timelines:
				timeline.kill()
			self.root.destroy()

		timedelta = (time.time() - start_time)
		self.alive_time += timedelta + 1/self.fps
		self.root.after(int( (1/self.fps - timedelta*0.5) * 1000 ), self.update)

	def init_timeline(self, timeline):
		for i, obj in enumerate(timeline.objects):
			obj.set_window( Toplevel(self.root) ) # creates child window for every Window object
			obj.name = i
		timeline.initialized = True
		self.animate_alpha(timeline.bg_alpha, timeline.bg_realpha_speed)

	def animate_alpha(self, new_alpha: Union[float, int], speed: int):
		if new_alpha != self.alpha:
			new = round(abs( self.alpha - new_alpha ) / self.fps * speed, 3)
			self.realpha_speed = f"+{new}" if new_alpha > self.alpha else f"-{new}"
			self.timeline_new_alpha = new_alpha

	def set_alpha(self, alpha: Union[int, float, str]):
		if isinstance(alpha, int) or isinstance(alpha, float):
			if 0 <= alpha <= 1:
				self.alpha = round(alpha, 3)
				self.root.attributes('-alpha', alpha)
				self.on_set_alpha_tl = self.timeline_index
			else:
				raise ValueError(f"'alpha' must be float or integer from 0 to 1, not {alpha} {type(alpha)}")

		elif isinstance(alpha, str):
			if alpha[0] in ['-', '+'] and ( alpha[1:].isdigit() or is_float(alpha[1:]) ):
				new = round(eval(f'self.alpha{alpha}'), 3)

				if new <= 0:
					self.alpha = 0
				elif new >= 1:
					self.alpha = 1
				else:
					self.alpha = new

				self.root.attributes('-alpha', self.alpha)
			else:
				raise ValueError(f"'alpha' must be integer number more than 0 or relative string number like '+100' or '-30', not {alpha} {type(alpha)}")

	def check_keyboard(self): # logs keystrokes
		while 1:
			key = kb.read_event()

			if key.event_type == kb.KEY_DOWN:
				self.key = key
				if key.name == 'esc':
					self.kill()
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

	def kill(self, realpha_speed: int = 2):
		self.root.wm_attributes("-topmost", 1)
		if self.timeline_new_alpha and self.realpha_speed and not self.dead:
			self.realpha_speed = ''
			self.timeline_new_alpha = None
		
		if not self.timeline_new_alpha and not self.realpha_speed:
			self.animate_alpha(0, realpha_speed)

		self.dead = True


class TimeLine: # it is a scene where contain child windows, you may use several scenes in one Area in sequience, one after another
	def __init__(self, objects: list, bg_alpha: Union[int, float] = 1, bg_realpha_speed: int = 1,
		wait_time: int = 0, alive_time: int = -1, moments: dict = {},
		on_start: Callable = None, on_death: Callable = None):
		# objects: list of Window objects
		# wait_time: delay time before start in seconds
		self.name = 'independent_timeline'
		self.objects = objects
		self.bg_alpha = bg_alpha
		self.bg_realpha_speed = bg_realpha_speed
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
		start_time = time.time()
		if self.initialized:
			if self.alive_time >= self.max_alive_time and self.max_alive_time != -1:
				return True

			if not self.started:
				if callable(self.on_start):
					self.on_start(cursor)
				self.started = True

			for sec in self.moments.keys():
				if sec <= self.alive_time and self.moments[sec] != 'done':
					if callable(self.moments[sec]):
						self.moments[sec](cursor)
						self.moments[sec] = 'done'
					elif callable(self.moments[sec]) and all([ callable(i) for i in self.moments[sec] ]):
						for func in self.moments[sec]:
							func(cursor)
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
						self.on_death(cursor)

				self.alive_time += (time.time() - start_time) + 1/fps
				return res
			else:
				return False
		else:
			return False

	def kill(self):
		for obj in self.objects:
			obj.kill()


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

		self.alpha = 0
		self.set_alpha(alpha, init=True)

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
					self.on_death(self)
					self.kill()
			else:			
				self.hp = new_hp

		elif isinstance(new_hp, str):
			if new_hp[0] in ['-', '+'] and new_hp[1:].isdigit():
				new = eval(f'self.hp{new_hp}')

				if new < 0:
					self.hp = 0
					if callable(self.on_death) and not self.dead:
						self.on_death()
						self.kill()
				else:
					self.hp = new
			else:
				raise ValueError(f"'new_hp' must be integer number greater than 0 or relative string number like '+100' or '-30', not {new_hp} {type(new_hp)}")
		else:
			raise ValueError(f"'new_hp' must be integer number greater than 0 or relative string number like '+100' or '-30', not {new_hp} {type(new_hp)}")

	def set_alpha(self, alpha: Union[int, float], init: bool = False):
		if isinstance(alpha, float) or isinstance(alpha, int):
			if 0 <= alpha <= 1:
				self.alpha = alpha
				if not init:
					self.root.attributes('-alpha', alpha)
			else:
				raise ValueError(f"'alpha' must be float or integer from 0 to 1 or relative string number like '+100' or '-30', not {alpha} {type(alpha)}")

		elif isinstance(alpha, str):
			if alpha[0] in ['-', '+'] and ( alpha[1:].isdigit() or is_float(alpha[1:]) ):
				new = eval(f'self.alpha{alpha}')

				if new < 0:
					self.alpha = 0
				elif new > 1:
					self.alpha = 1
				else:
					self.alpha = new

				if not init:
					self.root.attributes('-alpha', self.alpha)
			else:
				raise ValueError(f"'alpha' must be float or integer from 0 to 1 or relative string number like '+100' or '-30', not {alpha} {type(alpha)}")

		else:
			raise ValueError(f"'alpha' must be float or integer from 0 to 1 or relative string number like '+100' or '-30', not {alpha} {type(alpha)}")

	def intersect(self, box: list):
		if isinstance(box, list):
			if len(box) == 2 and all([ len(i) == 2 and isinstance(i[0], int) and isinstance(i[1], int) for i in box ]):

				mx, my = self.position
				mx_left, my_up, mx_right, my_down = mx-self.radius, my-self.radius, mx+self.radius, my+self.radius
				(bx_left, by_up), (bx_right, by_down) = box

				# box more than cursor
				if bx_left < mx_left <  bx_right or bx_left < mx_right <  bx_right: # if cursor x+radius or cursor x-radius is from box x[0] to box x[1]
					if by_up < my_up <  by_down or by_up < my_down <  by_down: # if cursor y+radius or cursor y-radius is from boy y[0] to boy y[1]
						return True

				# cursor more than box
				if mx_left < bx_left <  mx_right or mx_left < bx_right <  mx_right: # if box x[0] or box x[1] is from cursor x+radius or cursor x-radius
					if my_up < by_up <  my_down or my_up < by_down <  my_down: # if boy y[0] or boy y[1] is from cursor y+radius or cursor y-radius
						return True

				return False

			else:
				raise ValueError(f"'box' must be list with 2 positions ( 2 lists with 2 integers >= 0 ), like [ (0, 0), (1, 1) ], not {box}, {type(box)}")
		else:
			raise ValueError(f"'box' must be list with 2 positions ( 2 lists with 2 integers >= 0 ), like [ (0, 0), (1, 1) ], not {box}, {type(box)}")

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

	def kill(self):
		self.dead = True
		if self.root:
			self.root.destroy()


def is_float(string: str):
	try:
		float(string)
		return True
	except ValueError:
		return False