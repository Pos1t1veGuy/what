from typing import *

import os, time
import pyautogui as pag

from tkinter import Tk, Toplevel
from PIL import Image, ImageTk
from tkinter import Label

from .types import check_value, Media
from .movements import Movement


class Window: # it is child window
	def __init__(self, movements: Union[ List[Tuple[int, int]], list ], size: List[int], cycle: bool = False, repeat: int = -1,
		always_on_top: bool = True, show_frame: bool = False, alpha: float = 1.0, transparent_color: str = None, bg_color: str = "black",
		spawn_time: int = 0, alive_time: int = None, rhythm: int = None, on_rhythm: list = [], media: Media = None,
		hitbox: list = [], click_button: str = 'left', on_mouse_in_hitbox: list = [], on_click: list = [], on_mouse_hitbox_click: list = []):
		'''
		movements: list of the positions or Command object, it change position after every screen update
		cycle: it may move endlessly
		transparent_color: everywhere in window this color will be transparent
		spawn_time: time in seconds when window should spawn after connected timeline initialize
		alive_time: time in seconds how long it will be alive after spawn
		rhythm: time in seconds how many seconds it will execute on_rhythm commands
		on_rhythm: list of Command objects
		hitbox: list of 2 positions, it will execute Command at kwarg on_mouse_in_hitbox if you indicate this kwarg
		click_button: string pyautogui button id, after click it will do Command in on_click, if you indicate kwarg hitbox it will works with on_mouse_hitbox_click too
		'''

		self.name = 'independent_child_window'
		self.parent_tl_name = None
		self.root = None # Window.root will be loaded after use Window.set_window(tkinter.TopLevel)
		self.media = media

		check_value(movements, [list, Movement], exc_msg=f"Window.movements kwarg must be list, not {movements} {type(movements)}")
		self.movements = movements

		check_value(cycle, [bool, int], exc_msg=f"Window.cycle kwarg must be bool, not {cycle} {type(cycle)}")
		self.cycle = bool(cycle)

		check_value(repeat, int, exc_msg=f"Window.repeat kwarg must be integer more than 0, not {repeat} {type(repeat)}")
		if repeat == -1:
			self.repeat = repeat
		else:
			self.repeat = repeat-1

		check_value(size, list, exc_msg=f"Window.size kwarg must be list of 2 integers more than 0, not {size} {type(size)}")
		if len(size) == 2:
			if isinstance(size[0], int) and isinstance(size[1], int) and size[0] > 0 and size[1] > 0:
				self.size = size
			else:
				raise ValueError(f"Window.size kwarg must be list of 2 integers more than 0, not {size} {type(size)}")
		else:
			raise ValueError(f"Window.size kwarg must be list of 2 integers more than 0, not {size} {type(size)}")

		check_value(spawn_time, int, exc_msg=f"Window.spawn_time kwarg must be integer more than 0, not {spawn_time} {type(spawn_time)}")
		if spawn_time >= 0:
			self.spawn_time = spawn_time
		else:
			raise ValueError(f"Window.spawn_time kwarg must be integer more than 0, not {spawn_time} {type(spawn_time)}")

		check_value(alive_time, [int, type(None)], exc_msg=f"Window.alive_time kwarg must be integer more than 0, not {alive_time} {type(alive_time)}")
		if alive_time != None:
			if alive_time > 0:
				self.max_alive_time = alive_time
			else:
				raise ValueError(f"Window.alive_time kwarg must be integer more than 0, not {alive_time} {type(alive_time)}")
		else:
			self.max_alive_time = None

		check_value(rhythm, [int, type(None)], exc_msg=f"Window.rhythm kwarg must be integer more than 0, not {rhythm} {type(rhythm)}")
		if rhythm:
			if rhythm > 0:
				self.rhythm = rhythm
			else:
				raise ValueError(f"Window.rhythm kwarg must be integer more than 0, not {rhythm} {type(rhythm)}")
		else:
			self.rhythm = None

		self.alive_time = 0
		self.position = [0,0]

		check_value(hitbox, [list, tuple], exc_msg=f"Window.hitbox kwarg must be list or tuple of 2 positions, like [ (0, 0), (1, 1) ], not {hitbox} {type(hitbox)}")
		if len(hitbox) == 2:
			check_value(hitbox[0], [list, tuple], exc_msg=f"Window.hitbox kwarg must be list or tuple of 2 positions ( with only integers ), like [ (0, 0), (1, 1) ], not {hitbox} {type(hitbox)}")
			check_value(hitbox[1], [list, tuple], exc_msg=f"Window.hitbox kwarg must be list or tuple of 2 positions ( with only integers ), like [ (0, 0), (1, 1) ], not {hitbox} {type(hitbox)}")
			if len(hitbox[0]) == 2 and len(hitbox[1]) == 2:
				if isinstance(hitbox[0][0], int) and isinstance(hitbox[0][1], int) and isinstance(hitbox[1][0], int) and isinstance(hitbox[0][1], int):
					self.hitbox = hitbox
				else:
					raise ValueError(f"Window.hitbox kwarg must be list or tuple of 2 positions ( with only integers ), like [ (0, 0), (1, 1) ], not {hitbox} {type(hitbox)}")
			else:
				raise ValueError(f"Window.hitbox kwarg must be list or tuple of 2 positions ( with only integers ), like [ (0, 0), (1, 1) ], not {hitbox} {type(hitbox)}")
		else:
			self.hitbox = []

		self.on_hitbox = on_mouse_in_hitbox
		self.on_mouse_hitbox = on_mouse_hitbox_click
		self.on_click = on_click

		self.screen_width = None
		self.screen_height = None

		check_value(always_on_top, [bool, int], exc_msg=f"Window.always_on_top kwarg must be bool, not {always_on_top} {type(always_on_top)}")
		self.always_on_top = always_on_top
		check_value(show_frame, [bool, int], exc_msg=f"Window.show_frame kwarg must be bool, not {show_frame} {type(show_frame)}")
		self.show_frame = show_frame
		self.transparent_color = transparent_color
		self.bg_color = bg_color
		self.click_button = click_button

		self.dead = False
		self.movement_index = 0
		self.repeat_count = 0
		self.rhythm_index = 0
		self.on_rhythm_index = -1
		self.alpha = .0
		self.on_rhythm = on_rhythm
		self.pause = 0

		self.default_alpha = float(alpha)
		self.default_size = size
		self.default_media = media

		self.rhythm_animation_warning = False

	def update(self, parent_timeline, fps: int, cursor):
# returns true if this window is dead, do not use Window.update before Window.root loads ( to load Window.root use Window.set_window(tkinter.TopLevel) )
		start_time = time.time()

		if self.pause > 0:
			self.pause -= 1/fps
			return True
		else:
			self.pause = 0

		if self.parent_tl_name != parent_timeline.name:
			self.parent_tl_name = parent_timeline.name

		if parent_timeline.alive_time >= self.spawn_time:
			if self.root:
				if not self.dead:
					if self.max_alive_time != None and self.max_alive_time <= parent_timeline.alive_time:
						if self.root:
							self.root.destroy()

						self.dead = True
						return False

					self.mouse_listener(cursor)

					if self.alpha == .0:
						self.root.attributes('-alpha', self.default_alpha)
						self.alpha = self.default_alpha
						del self.default_alpha

					if self.rhythm != None:
						if len(self.on_rhythm) / fps >= self.rhythm and not self.rhythm_animation_warning:
							print(
f'''WARNING: {self.adress}Your window has rhythm animation that lasts longer than its assigned execution time in Window constructor at kwarg 'rhythm'
Window.rhythm = {self.rhythm}, but needs more than {round(len(self.on_rhythm) / fps, 2)}
You must:
1. Change rhythm kwarg in constructor or
2. Use fewer commands in command list self.on_rhythm ( 'on_rhythm' at Window constructor ) or
3. Increase fps at Area.run() kwarg 'fps' '''
								)
							self.rhythm_animation_warning = True

						if self.alive_time >= self.rhythm_index * self.rhythm:
							self.rhythm_index += 1
							self.on_rhythm_index = 0

						if self.on_rhythm_index > -1 and self.on_rhythm:
							self.command(self.on_rhythm[self.on_rhythm_index], rhythm=True)
							self.on_rhythm_index += 1
							if self.on_rhythm_index > len(self.on_rhythm)-1:
								self.on_rhythm_index = -1

					if hasattr(self.media, 'update'):
						self.media.update(self, parent_timeline, fps, cursor)

					self.step()
					self.alive_time += (time.time() - start_time) + 1/fps
					return True
				else:
					return False
			else:
				raise AttributeError(f'{self.adress}Child window "Window.root" did not configured')
		return True

	def set_window(self, root: Union[Tk, Toplevel]):

		self.root = root
		self.root.geometry(f"{self.default_size[0]}x{self.default_size[1]}")

		if self.media:
			self.image_label = Label(self.root)
			self.image_label.place(relx=0.5, rely=0.5, anchor="center")
			
			self.media.set_label(self.image_label)

		self.root.wm_attributes("-topmost", self.always_on_top)
		self.root.overrideredirect(not self.show_frame)
		self.root.attributes('-alpha', float(self.alpha))
		self.root.configure(bg=self.bg_color)
		self.root.config(cursor="none")

		self.screen_width = self.root.winfo_screenwidth()
		self.screen_height = self.root.winfo_screenheight()

		if self.transparent_color:
			self.root.wm_attributes("-transparentcolor", transparent_color)

		self.root.title("Child Window")
		self.root.attributes('-alpha', .0)

	def resize(self, x: int, y: int):
		self.resize_window(x, y)
		self.media.resize(x, y)

	def resize_window(self, x: int, y: int):
		self.root.geometry(f"{x}x{y}")
		self.size = [x,y]

	def mouse_listener(self, cursor):
		if cursor.position:
			absolute_x, absolute_y = cursor.position
			x = absolute_x - self.position[0]
			y = absolute_y - self.position[1]

			is_in_window = cursor.intersect([absolute_x, absolute_y], [ self.position, (self.position[0] + self.size[0], self.position[1] + self.size[1]) ])

			if is_in_window:
				if callable(self.on_click):
					self.command(self.on_click)

				if self.hitbox:
					is_in_hitbox = cursor.intersect([absolute_x, absolute_y], [
						(self.position[0] + self.hitbox[0][0], self.position[1] + self.hitbox[0][1]),
						(self.position[0] + self.hitbox[1][0], self.position[1] + self.hitbox[1][1])
						])

					if is_in_hitbox:
						if isinstance(self.on_hitbox, list) and isinstance(self.on_hitbox[0], str):
							self.command(self.on_hitbox)
						elif callable(self.on_hitbox):
							self.command(self.on_hitbox(self))

						if cursor.pressed_button and callable(self.on_mouse_hitbox):
							self.command(self.on_mouse_hitbox)

	def command(self, command: Union[List[list], Callable], rhythm: bool = False):
		if command:
			if isinstance(command, list):
				if isinstance(command[0], str):
					self.string_command(command)
				else:
					if isinstance(command, list):
						if isinstance(command[0], str):
							self.string_command(command)
						else:
							if not rhythm:
								raise ValueError(
f"{self.adress}Invalid command at Window.movements[{self.movement_index}]: {self.movements[self.movement_index]}. Command must be Command object, callable or list of callable ( functions must take Window argument )"
									)
							else:
								raise ValueError(
f"{self.adress}Invalid command at Window.on_rhythm[{self.on_rhythm_index}]: {self.on_rhythm[self.on_rhythm_index]}. Command must be Command object, callable or list of callable ( functions must take Window argument )"
									)

					elif callable(command):
						command(self)

					else:
						if not rhythm:
							raise ValueError(
f"{self.adress}Invalid command at Window.movements[{self.movement_index}]: {self.movements[self.movement_index]}. Command must be Command object, callable or list of callable ( functions must take Window argument )"
								)
						else:
							raise ValueError(
f"{self.adress}Invalid command at Window.on_rhythm[{self.on_rhythm_index}]: {self.on_rhythm[self.on_rhythm_index]}. Command must be Command object, callable or list of callable ( functions must take Window argument )"
								)
		
			elif callable(command):
				command(self)
			
			else:
				if not rhythm:
					raise ValueError(
f"{self.adress}Invalid command at Window.movements[{self.movement_index}]: {self.movements[self.movement_index]}. Command must be Command object, callable or list of callable ( functions must take Window argument )"
						)
				else:
					raise ValueError(
f"{self.adress}Invalid command at Window.on_rhythm[{self.on_rhythm_index}]: {self.on_rhythm[self.on_rhythm_index]}. Command must be Command object, callable or list of callable ( functions must take Window argument )"
						)

	def string_command(self, command: str):
		cmd, args = command[0], command[1:]

		if cmd == 'resize':
			if len(args) >= 2:

				res = []
				for i, num in enumerate(args):
					if isinstance(num, str):
						new = eval(f'self.size[{i}]{num}')
						if new < 0:
							raise ValueError(
f"{self.adress}{['x','y'][i]} argument must be integer number greater than 0 or relaitive string number like '+100' or '-30'. Used relative and gets negative from current window size {self.size}"
								)
						else:
							res.append(new)
					else:
						res.append(num)

				self.resize( int(res[0]), int(res[1]) )

			else:
				raise ValueError(f"{self.adress}Command.window.resize must contains 2 integer arguments more than 0, not {args}")

		elif cmd == 'resize_window':
			if len(args) >= 2:

				res = []
				for i, num in enumerate(args):
					if isinstance(num, str):
						new = eval(f'self.size[{i}]{num}')
						if new < 0:
							raise ValueError(
f"{self.adress}{['x','y'][i]} argument must be integer number greater than 0 or relaitive string number like '+100' or '-30'. Used relative and gets negative from current window size {self.size}"
								)
						else:
							res.append(new)
					else:
						res.append(num)

				self.resize_window( int(res[0]), int(res[1]) )

			else:
				raise ValueError(f"{self.adress}Command.window.resize must contains 2 integer arguments more than 0, not {args}")

		elif cmd == 'resize_media':
			if not self.media:
				return ValueError(f"{self.adress}Window has not an media")

			if len(args) >= 2:
				self.media.resize(*args)
			else:
				raise ValueError(f"{self.adress}Command.media.resize must contains 2 integer arguments more than 0, not {args}")

		elif cmd == 'rotate_media':
			if not self.media:
				return ValueError(f"{self.adress}Window has not an media")

			if len(args) >= 1:
				self.media.rotate(args[0])
			else:
				raise ValueError(f"{self.adress}Command.media.rotate must contains 1 integer arguments more than 0, not {args}")

		elif cmd == 'set_media':
			if len(args) >= 1:
				self.media = args[0]
			else:
				raise ValueError(f"{self.adress}Command.media.set must contains 1 Media argument, not {args}")

		elif cmd == 'wait':
			check_value(args[0], [int, float],
exc_msg=f"{self.adress}Invalid string command at Window.movements[{self.movement_index}]: {self.movements[self.movement_index]}. 'time' argument must be integer or float > 0 or -1 ( endless )"
				)
			if args[0] > 0 or args[0] == -1:
				self.pause = args[0]
			else:
				raise ValueError(
f"{self.adress}Invalid string command at Window.movements[{self.movement_index}]: {self.movements[self.movement_index]}. 'time' argument must be integer or float > 0 or -1 ( endless )"
					)

	def step(self):
		if self.movements:
			if len(self.movements) > self.movement_index:
				is_list = ( isinstance(self.movements[self.movement_index], list) or isinstance(self.movements[self.movement_index], tuple) )

				if is_list and len(self.movements[self.movement_index]) == 2 and not isinstance(self.movements[self.movement_index][0], str):
					pos = self.movements[self.movement_index]
					self.root.geometry(f"+{pos[0]}+{pos[1]}")
					self.position = pos

					self.movement_index += 1
				elif isinstance(self.movements[self.movement_index][0], str):
					self.command(self.movements[self.movement_index])
					self.movement_index += 1
			else:
				if self.pause:
					pass

				elif self.cycle:
					self.undo()
					self.repeat_count += 1
				elif self.repeat > self.repeat_count:
					self.undo()
					self.repeat_count += 1
				else:
					self.kill()
					return True
		else:
			if self.alpha != .0:
				self.root.attributes('-alpha', .0)
				self.alpha = .0

	def undo(self):
		self.movement_index = 0
		self.on_rhythm_index = -1

		if self.size != self.default_size:
			self.resize_window(*self.default_size)

		if self.media != self.default_media:
			self.media = self.default_media

	def kill(self):
		self.dead = True
		if self.root:
			self.root.destroy()

	@property
	def adress(self):
		return f'Timeline {self.parent_tl_name}, Window {self.name}: '