from typing import *

import keyboard as kb
import pyautogui as pag

import time
import os

from PIL import Image, ImageTk
from pynput import mouse
from tkinter import Tk, Label, Toplevel, Canvas
from threading import Thread as th
from traceback import print_exc

from .types import Media, check_value, HitBox, HitPolygon, Segment


class Area: # main window
	def __init__(self, cursor = None, bg_always_on_top: bool = False, minimize_windows: bool = True, moments: dict = {},
		bg_func: Callable = None, on_death: Callable = None, on_start: Callable = None, cursor_circle_radius: int = 3, show_mouse: bool = False,
		on_tl_start: Callable = None, on_tl_death: Callable = None, on_click: Callable = None,
		alpha: int = None, media: Media = None):
		'''
		cursor: Cursor object or None
		bg_always_on_top: background is black window, you can set up it. This kwarg makes window always on top
		minimize_windows: if True it will minimize every opened window when it starts
		moments: dict with integer key second and callable value ( value must takes Area ). At a given second will do callable
		bg_func: callable that updated along with Area ( 1/fps times per second )
		cursor_circle_radius: integer radius of white circle under mouse, if 0 it will not shows circle
		alpha: background is black window, you can set up it. This kwarg makes level of window transparentcy
		media: Media object or None
		'''

		self.timelines = []
		self.keyboard_thread = th(target=self.check_keyboard, daemon=True)
		self.keyboard_thread.start()

		if minimize_windows:
			os.system("explorer shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}") # minimizes every window like WIN+D

		self.root = Tk()
		self.root.title("WHAT root")

		check_value(moments, dict, f"'moments' constructor kwarg must be dict with integer keys and callable values or list of callable values ( functions must takes Area argument )")
		self.moments = moments

		check_value(cursor_circle_radius, int, exc_msg=f"'cursor_circle_radius' constructor kwarg must be integer >= 0, not {cursor_circle_radius} {type(cursor_circle_radius)}")
		self.cursor_circle_radius = cursor_circle_radius

		if media:
			self.media_label = Label(self.root)
			self.media_label.pack(expand=True, anchor='center')
			self.media = media
			self.media.set_label(self.media_label)
		else:
			self.media = None
			self.media_label = None

		#self.message_label = Label(self.root, text="", font=("Arial", 34), bg="black", fg="white")
		#self.message_label.place(relx=0.5, y=0, anchor="center")

		if cursor:
			self.cursor = cursor
			self.cursor.set_window( Toplevel(self.root) )
			self.root.config(cursor="none")
		else:
			self.cursor = Cursor()

		check_value(show_mouse, [bool, int], f"'show_mouse' constructor kwarg must be bool, not {show_mouse} {type(show_mouse)}")
		if not show_mouse:
			self.root.config(cursor="none")

		self.screen_width = self.root.winfo_screenwidth()
		self.screen_height = self.root.winfo_screenheight()

		self.canvas = Canvas(self.root, width=self.screen_width, height=self.screen_height, bg="black", highlightthickness=0)
		self.canvas.pack()
		self.circle = self.canvas.create_oval(cursor_circle_radius, cursor_circle_radius, cursor_circle_radius, cursor_circle_radius, fill="white")

		self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

		self.root.overrideredirect(1)
		self.root.configure(bg="black")

		check_value(alpha, [int, float], exc_msg=f"'alpha' constructor kwarg must be integer of float from 0 to 1, not {alpha} {type(alpha)}")
		self.alpha = alpha
		self.alive_time = 0
		self.stopping = False
		check_value(bg_always_on_top, [int, bool], exc_msg=f"'bg_always_on_top' constructor kwarg must be bool, not {bg_always_on_top} {type(bg_always_on_top)}")
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
		self.results = {}

		if bg_always_on_top:
			self.root.wm_attributes("-topmost", 1)

	def set_timelines(self, timelines: list): # sets new timeline list
		check_value(timelines, [tuple, list], exc_msg=f"Area.set_timelines takes a list of TimeLine objects, not {timelines} {type(timelines)}")
		self.timelines = timelines

		for i, timeline in enumerate(self.timelines):
			timeline.name = i

	def add_timeline(self, timeline): # adds only one timeline to timeline list
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

		self.update()
		self.root.mainloop()

	def update(self): # updates every timeline, will be dead when every timeline is dead
		start_time = time.time()
		if self.bg_func:
			self.bg_func(self, self.fps)

		if self.moments:
			self.check_moments()
		if self.cursor.pressed_button and callable(self.on_click):
			self.on_click(self)
		if self.timeline_new_alpha != None and self.realpha_speed != '':
			self.realpha_step()
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

		if callable(self.on_tl_start):
			self.on_tl_start(self)

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
				raise ValueError(f"Area.set_alpha takes a float or an integer from 0 to 1, not {alpha} {type(alpha)}")

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
				raise ValueError(f"Area.set_alpha takes an integer, a float from 0 to 1 or a relative string numbers like '+100' or '-30', not {alpha} {type(alpha)}")

	def message(self, text: str, duration: int = 1): # shows message with 'text' at game
		...

	def realpha_step(self):
		if self.timeline_new_alpha < self.alpha and self.timeline_new_alpha < eval(f'self.alpha{self.realpha_speed}') and float(self.realpha_speed) < 0:
			self.set_alpha(self.realpha_speed)

		elif self.timeline_new_alpha > self.alpha and self.timeline_new_alpha > eval(f'self.alpha{self.realpha_speed}') and float(self.realpha_speed) > 0:
			self.set_alpha(self.realpha_speed)

		else:
			if self.timeline_new_alpha and ( isinstance(self.timeline_new_alpha, float) or isinstance(self.timeline_new_alpha, int) ) and 0 <= self.timeline_new_alpha <= 1:
				self.set_alpha(self.timeline_new_alpha)

			self.realpha_speed = ''
			self.timeline_new_alpha = None

	def check_moments(self):
		check_value(self.moments, dict, f"'moments' constructor kwarg must be dict with integer keys and callable values or list of callable values ( functions must takes Area argument )")
		for sec in self.moments.keys():
			if sec <= self.alive_time and self.moments[sec] != 'done':
				if callable(self.moments[sec]):
					self.moments[sec](self)
					self.moments[sec] = 'done'
				elif callable(self.moments[sec]) and all([ callable(i) for i in self.moments[sec] ]):
					for func in self.moments[sec]:
						func(self)
					self.moments[sec] = 'done'
				else:
					raise ValueError(
f"'moments' constructor kwarg must be dict with integer keys and callable values or list of callable values ( functions must takes Area argument )"
						)

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
		'''
		objects: list of Window objects
		wait_time: delay time before start in seconds
		bg_alpha: integer level of background area window transparency
		alive_time: integer limit, maximum of alive time
		moments: dict with integer key second and callable value ( value must takes TimeLine ). At a given second will do callable
		'''

		self.name = 'independent_timeline'
		check_value(objects, [tuple, list], exc_msg=f"'objects' constructor kwarg must be list of Window objects, not {objects} {type(objects)}")
		self.objects = objects
		check_value(bg_alpha, [int, float], exc_msg=f"'bg_alpha' constructor kwarg must be integer of float from 0 to 1, not {bg_alpha} {type(bg_alpha)}")
		self.bg_alpha = bg_alpha
		check_value(bg_realpha_speed, int, exc_msg=f"'bg_realpha_speed' constructor kwarg must be integer > 0, not {bg_realpha_speed} {type(bg_realpha_speed)}")
		self.bg_realpha_speed = bg_realpha_speed
		check_value(wait_time, int, exc_msg=f"'wait_time' constructor kwarg must be integer > 0, not {wait_time} {type(wait_time)}")
		self.wait_time = wait_time
		check_value(alive_time, int, exc_msg=f"'alive_time' constructor kwarg must be integer > 0 ( or -1 if it should be endless ), not {alive_time} {type(alive_time)}")
		self.max_alive_time = alive_time
		check_value(moments, dict, f"'moments' constructor kwarg must be dict with integer keys and callable values or list of callable values ( functions must takes TimeLine argument )")
		self.moments = moments

		self.on_start = on_start
		self.on_death = on_death

		self.initialized = False
		self.started = False
		self.dead = False
		self.alive_time = 0

	def update(self, fps: int, cursor): # returns true when every object is dead
		start_time = time.time()
		if self.initialized:
			if self.alive_time >= self.max_alive_time and self.max_alive_time != -1:
				return True

			if not self.started:
				if callable(self.on_start):
					self.on_start(self)
				self.started = True

			for sec in self.moments.keys():
				if sec <= self.alive_time and self.moments[sec] != 'done':
					if callable(self.moments[sec]):
						self.moments[sec](self)
						self.moments[sec] = 'done'
					elif callable(self.moments[sec]) and all([ callable(i) for i in self.moments[sec] ]):
						for func in self.moments[sec]:
							func(self)
						self.moments[sec] = 'done'
					else:
						raise ValueError(
f"'moments' constructor kwarg must be dict with integer keys and callable values or list of callable values ( functions must takes TimeLine argument )"
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
						self.on_death(self)

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
	def __init__(self, hp: int = 1, hitbox: Union[HitBox, HitPolygon] = None, hitbox_show_color = None, on_death = None, show_mouse: bool = False,
		image: Union[Image, str] = None, transparent_color: str = None, resize: List[[int, int]] = None, alpha: float = 1.0):
		'''
		radius: integer numbers, the "click zone" of cursor expands by this numbers in all directions. For example 1 gets rectangle 3x3 around cursor, 2 gets 5x5
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
		self.zero_hp = False

		check_value(show_mouse, [int, bool], exc_msg=f"'show_mouse' constructor kwarg must be bool, not {show_mouse} {type(show_mouse)}")
		self.show_mouse = show_mouse

		if hitbox:
			check_value(hitbox, [HitBox, HitPolygon], exc_msg=f"'hitbox' constructor kwarg must be HitBox or HitPolygon object, not {hitbox} {type(hitbox)}")
			self.default_hitbox = hitbox
		else:
			self.default_hitbox = None
		self.hitbox = None

		self.hitbox_show_color = hitbox_show_color

		length = 3_000
		self.default_ray = Segment([0,0], [0,length])

		if isinstance(image, str):
			self.image = Image.open(image)
		elif isinstance(image, str):
			self.image = image
		else:
			self.image = None

		self.root = None
		self.canvas = None
		self.polygon_id = None
		self.transparent_color = transparent_color

		self.alpha = 0
		self.set_alpha(alpha, init=True)

		if resize:
			check_value(resize, [list, tuple], f"'resize' constructor kwarg must be list of 2 integers > 0, not {resize} {type(resize)}")
			if len(resize) == 2:
				check_value(resize[0], int, f"'resize' constructor kwarg must be list of 2 integers > 0, not {resize} {type(resize)}")
				check_value(resize[1], int, f"'resize' constructor kwarg must be list of 2 integers > 0, not {resize} {type(resize)}")
				if resize[0] > 0 and resize[1] > 0:
					self.image = self.image.resize(resize)
				else:
					raise ValueError(f"'resize' constructor kwarg must be list of 2 integers > 0, not {resize} {type(resize)}")
			else:
				raise ValueError(f"'resize' constructor kwarg must be list of 2 integers > 0, not {resize} {type(resize)}")

		self.position = None
		self.pressed_button = None

		self.mouse_thread = mouse.Listener(on_move=self.on_mouse_move, on_click=self.on_mouse_click, daemon=True)
		self.mouse_thread.start()

	def set_hp(self, new_hp: Union[int, str]):
		if isinstance(new_hp, int):
			if new_hp <= 0:
				self.hp = 0
				if not self.zero_hp:
					if callable(self.on_death) and not self.dead:
						self.on_death(self)
					self.zero_hp = True
			else:			
				self.hp = new_hp

		elif isinstance(new_hp, str):
			if new_hp[0] in ['-', '+'] and new_hp[1:].isdigit():
				new = eval(f'self.hp{new_hp}')

				if new <= 0:
					self.hp = 0
					if not self.zero_hp:
						if callable(self.on_death) and not self.dead:
							self.on_death(self)
						self.zero_hp = True
				else:
					self.hp = new
			else:
				raise ValueError(f"Cursor.set_hp takes an integer > 0 or a relative string numbers like '+100' or '-30', not {new_hp} {type(new_hp)}")
		else:
			raise ValueError(f"Cursor.set_hp takes an integer > 0 or a relative string numbers like '+100' or '-30', not {new_hp} {type(new_hp)}")

	def set_alpha(self, alpha: Union[int, float], init: bool = False):
		if isinstance(alpha, float) or isinstance(alpha, int):
			if 0 <= alpha <= 1:
				self.alpha = alpha
				if not init:
					self.root.attributes('-alpha', alpha)
			else:
				raise ValueError(f"Cursor.set_alpha takes a float, an integer from 0 to 1 or a relative string numbers like '+100' or '-30', not {alpha} {type(alpha)}")

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
				raise ValueError(f"Cursor.set_alpha takes a float, an integer from 0 to 1 or a relative string numbers like '+100' or '-30', not {alpha} {type(alpha)}")

		else:
			raise ValueError(f"Cursor.set_alpha takes a float, an integer from 0 to 1 or a relative string numbers like '+100' or '-30', not {alpha} {type(alpha)}")

	def intersects(self, object: Union[HitBox, HitPolygon, Segment, list, tuple]):
		check_value(object, [HitBox, HitPolygon, Segment, list, tuple], exc_msg=f"Cursor.intersect takes Hitbox/HitPolygon/Segment object or list/tuple of 2 integers, not {object}, {type(object)}")

		if isinstance(object, (tuple, list)):
			if not all(isinstance(pos, int) for pos in object):
				raise ValueError(f"Cursor.intersect takes Hitbox/HitPolygon/Segment object or list/tuple of 2 integers, not {object}, {type(object)}")

		if isinstance(object, HitBox):
			if isinstance(self.hitbox, HitBox): # hitbox intersects cursor hitbox or polygon
				if self.hitbox in object:
					return True
			elif self.hitbox == None: # hitbox intersects cursor position
				if self.position in object:
					return True
		else:
			if self.hitbox: # polygon intersects cursor hitbox or polygon
				if object.intersects(self.hitbox):
					return True

		inter_cnt = object.intersects(self.ray, return_count=True)
		if inter_cnt % 2 and inter_cnt != 0:
			return True

		return False

	def set_window(self, root: Union[Tk, Toplevel]):
		if self.image:
			self.root = root
			
			self.root.title("Cursor Window")

			if self.transparent_color:
				self.root.wm_attributes("-transparentcolor", self.transparent_color)

			self.root.attributes('-topmost', True)
			self.root.overrideredirect(True)
			self.root.attributes('-alpha', float(self.alpha))

			if self.hitbox_show_color:
				self.canvas = Canvas(root, width=self.image.size[0], height=self.image.size[1], highlightthickness=0)
				self.canvas.pack()
				self.polygon_id = self.canvas.create_polygon(self.default_hitbox.as_tk_polygon, fill=self.hitbox_show_color)

			self.root.geometry(f"{self.image.size[0]}x{self.image.size[1]}")

			self.photo = ImageTk.PhotoImage(self.image)
			self.image_label = Label(root, image=self.photo)
			self.image_label.pack()

		if not self.show_mouse:
			self.root.config(cursor="none")

	def resize(self, size: List[[int, int]]):
		if size:
			check_value(size, [list, tuple], exc_msg=f"Cursor.resize takes a list with 2 integers, not {size} {type(size)}")
			if len(size) == 2:
				check_value(size[0], int, f"'size' constructor kwarg must be list of 2 integers > 0, not {size} {type(size)}")
				check_value(size[1], int, f"'size' constructor kwarg must be list of 2 integers > 0, not {size} {type(size)}")
				if size[0] > 0 and size[1] > 0:
					self.image = self.image.resize(size)
					self.root.geometry(f"{self.image.size[0]}x{self.image.size[1]}+{self.position[0]}+{self.position[1]}")
				else:
					raise ValueError(f"Cursor.resize takes an integer values must be > 0, not {size} {type(size)}")
			else:
				raise ValueError(f"Cursor.resize takes a list with 2 integers, not {size} {type(size)}")

	def update(self):
		mouse_x, mouse_y = pag.position()
		self.update_hitbox()

		if self.hp <= 0 and callable(self.on_death) and not self.dead:
			self.on_death(self)

		if self.image:
			window_x = mouse_x - self.image.size[0] // 2
			window_y = mouse_y - self.image.size[1] // 2

			self.root.geometry(f"{self.image.size[0]}x{self.image.size[1]}+{window_x}+{window_y}")

	def update_hitbox(self):
		if self.position:
			self.ray = self.default_ray.at_pos(self.position)

			if self.polygon_id != None:
				self.canvas.itemconfig(self.polygon_id, fill=self.hitbox_show_color)

			if self.default_hitbox:
				new_pos = [ self.position[0] - self.default_hitbox.edge_length//2, self.position[1] - self.default_hitbox.edge_length//2 ]
				self.hitbox = self.default_hitbox.at_pos(new_pos)
			else:
				self.hitbox = None
		else:
			self.ray = None
			self.hitbox = None

	def on_mouse_move(self, x, y): # logs mouse position
		self.position = [x,y]

	def on_mouse_click(self, x, y, button, pressed): # logs mouse pressed button
		self.pressed_button = button if pressed else None

	def kill(self):
		self.dead = True
		if self.root:
			self.root.destroy()

	def __str__(self):
		return f"Cursor([{ len(self) } vertices], position={self.position}, area={self.area})"
	
	def __contains__(self, i: Union[list, tuple, Segment, HitPolygon, HitBox]):
		return self.intersects(i)

	def __repr__(self):
		return f"HitPolygon(hp={self.hp}, hitbox={self.hitbox}, hitbox_show_color={self.hitbox_color_show}, show_mouse={self.show_mouse}, image={self.image}, transparent_color={self.transparent_color}, resize={self.resize}, alpha={self.alpha})"


def is_float(string: str):
	try:
		float(string)
		return True
	except ValueError:
		return False