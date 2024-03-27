from typing import *

import time

from tkinter import Tk, Toplevel
from tkinter import Label, Canvas

from .types import check_value, Media
from .geometry import HitBox, HitPolygon, HitCircle


class Window: # it is child window
	def __init__(self, movements: Union[ List[Tuple[int, int]], list ], size: List[int], cycle: bool = False, repeat: int = -1,
		always_on_top: bool = True, show_frame: bool = False, alpha: float = 1.0, transparent_color: str = None, bg_color: str = "black",
		spawn_time: int = 0, alive_time: int = None, rhythm: Union[int, float] = None, is_rhythm_enabled: bool = True, on_rhythm: list = [], moments: dict = {},
		media: Media = None, media_label_args: list = [], media_label_kwargs: dict = {'relx': 0.5, 'rely': 0.5, 'anchor': 'center'},
		hitbox: Union[HitBox, HitPolygon, HitCircle] = None, click_button: str = 'left', hitbox_show_color = None,
		on_mouse_in_hitbox: list = [], on_mouse_hitbox_click: list = [], on_mouse_not_in_hitbox: list = [], on_mouse_not_in_hitbox_click: list = [],
		on_click: list = [], bg_func: Callable = None):
		'''
		movements: list of the positions or Command object, it change position after every screen update
		cycle: it may move endlessly
		transparent_color: everywhere in window this color will be transparent
		spawn_time: time in seconds when window should spawn after connected timeline initialize
		alive_time: time in seconds how long it will be alive after spawn
		rhythm: time in seconds how many seconds it will execute on_rhythm commands
		on_rhythm: list of Command objects
		hitbox: HitBox or HitPolygon object, it will execute Command at kwarg on_mouse_in_hitbox if you indicate this kwarg
		click_button: string pyautogui button id, after click it will do Command in on_click, if you indicate kwarg hitbox it will works with on_mouse_hitbox_click too
		hitbox_show_color: color of hitbox, if it is not None hitbox will be filled
		moments: dict with integer key second and callable value ( value must takes Window ). At a given second will do callable
		'''

		self.name = 'independent_child_window'
		self.parent_tl_name = None
		self.root = None # Window.root will be loaded after use Window.set_window(tkinter.TopLevel)
		self.media = media

		check_value(movements, [list, tuple], exc_msg=f"'movements' constructor kwarg must be list, not {movements} {type(movements)}")
		self.movements = movements

		check_value(cycle, [bool, int], exc_msg=f"'cycle' constructor kwarg must be bool, not {cycle} {type(cycle)}")
		self.cycle = bool(cycle)

		check_value(repeat, int, exc_msg=f"'repeat' constructor kwarg must be integer > 0, not {repeat} {type(repeat)}")
		if repeat == -1:
			self.repeat = repeat
		else:
			self.repeat = repeat-1

		check_value(moments, dict, exc_msg=f"'moments' constructor kwarg must be dict with integer keys and callable values or list of callable values ( functions must takes TimeLine argument )")
		self.moments = moments

		check_value(size, [list, tuple], con=len(size) == 2,
			exc_msg=f"'size' constructor kwarg must be list or tuple of 2 integers > 0, not {size} {type(size)}")
		if isinstance(size[0], int) and isinstance(size[1], int) and size[0] > 0 and size[1] > 0:
			self.size = size
		else:
			raise ValueError(f"'size' constructor kwarg must be list of 2 integers > 0, not {size} {type(size)}")

		check_value(spawn_time, [int, float], con=spawn_time >= 0,
			exc_msg=f"'spawn_time' constructor kwarg must be integer or float > 0, not {spawn_time} {type(spawn_time)}")
		self.spawn_time = spawn_time

		if alive_time != None:
			check_value(alive_time, [int, float], con=alive_time > 0,
				exc_msg=f"Window 'alive_time' kwarg of constructor must be integer or float > 0, not {alive_time} {type(alive_time)}")
			self.max_alive_time = alive_time
		else:
			self.max_alive_time = None

		if rhythm:
			check_value(rhythm, [int, float], con=rhythm > 0, exc_msg=f"'rhythm' constructor kwarg must be integer or float > 0, not {rhythm} {type(rhythm)}")
			self.rhythm = rhythm
		else:
			self.rhythm = None

		check_value(is_rhythm_enabled, [int, bool], exc_msg=f"'is_rhythm_enabled' constructor kwarg must be bool, not {is_rhythm_enabled} {type(is_rhythm_enabled)}")
		self.is_rhythm_enabled = bool(is_rhythm_enabled)

		self.alive_time = 0
		self.position = [0,0]
		self.media_label_kwargs = media_label_kwargs
		self.media_label_args = media_label_args

		if hitbox:
			check_value(hitbox, [HitBox, HitPolygon], exc_msg=f"'hitbox' constructor kwarg must be HitBox or HitPolygon object, not {hitbox} {type(hitbox)}")
			self.hitbox = hitbox
			self.default_hitbox = hitbox
		else:
			self.hitbox = None
			self.default_hitbox = None

		self.hitbox_show_color = hitbox_show_color

		self.on_hitbox = on_mouse_in_hitbox
		self.on_mouse_not_hitbox = on_mouse_not_in_hitbox
		self.on_hitbox_click = on_mouse_hitbox_click
		self.on_not_hitbox_click = on_mouse_not_in_hitbox_click
		self.on_click = on_click
		self.bg_func = bg_func

		self.screen_width = None
		self.screen_height = None
		self.canvas = None

		check_value(always_on_top, [bool, int], exc_msg=f"'always_on_top' constructor kwarg must be bool, not {always_on_top} {type(always_on_top)}")
		self.always_on_top = always_on_top
		check_value(show_frame, [bool, int], exc_msg=f"'show_frame' constructor kwarg must be bool, not {show_frame} {type(show_frame)}")
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
		self.polygon_id = None

		self.default_alpha = float(alpha)
		self.default_size = size
		self.default_media = media

		self.rhythm_animation_warning = False

	def update(self, parent_timeline, fps: int, cursor):
# returns true if this window is dead, do not use Window.update before Window.root loads ( to load Window.root use Window.set_window(tkinter.TopLevel) )
		start_time = time.time()

		if callable(self.bg_func):
			self.bg_func(self)

		if self.pause > 0:
			self.pause -= 1/fps
			self.alive_time += (time.time() - start_time) + 1/fps
			return True
		elif self.pause == -1:
			self.alive_time += (time.time() - start_time) + 1/fps
			return True
		else:
			self.pause = 0

		if self.parent_tl_name != parent_timeline.name:
			self.parent_tl_name = parent_timeline.name

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


		if parent_timeline.alive_time >= self.spawn_time:
			if self.root:
				if not self.dead:
					if self.max_alive_time != None and self.max_alive_time <= parent_timeline.alive_time:
						if self.root:
							self.root.destroy()

						self.dead = True
						self.alive_time += (time.time() - start_time) + 1/fps
						return False

					self.mouse_listener(cursor)

					if self.alpha == .0:
						self.root.attributes('-alpha', self.default_alpha)
						self.alpha = self.default_alpha
						del self.default_alpha

					self.rhythm_step()

					if hasattr(self.media, 'update'):
						self.media.update(self, parent_timeline, fps, cursor)

					self.step()
					self.alive_time += (time.time() - start_time) + 1/fps
					return True
				else:
					return False
			else:
				raise AttributeError(f'{self.adress}Child tkinter window "Window.root" did not configured')
		
		self.alive_time += (time.time() - start_time) + 1/fps
		return True

	def set_window(self, root: Union[Tk, Toplevel]):
		self.root = root
		self.root.geometry(f"{self.default_size[0]}x{self.default_size[1]}")

		if self.media:
			self.media_label = Label(self.root, borderwidth=0, background="black", highlightthickness=0)
			self.media_label.place(*self.media_label_args, **self.media_label_kwargs)
			
			self.media.set_label(self.media_label)

		self.root.wm_attributes("-topmost", self.always_on_top)
		self.root.overrideredirect(not self.show_frame)
		self.root.attributes('-alpha', float(self.alpha))
		self.root.configure(bg=self.bg_color)
		self.root.config(cursor="none")

		self.screen_width = self.root.winfo_screenwidth()
		self.screen_height = self.root.winfo_screenheight()

		if self.hitbox_show_color:
			self.canvas = Canvas(root, width=self.default_size[0], height=self.default_size[1], highlightthickness=0)
			self.canvas.pack()
			self.polygon_id = self.canvas.create_polygon(self.hitbox.as_tk_polygon, fill=self.hitbox_show_color)
			
		if self.transparent_color:
			self.root.wm_attributes("-transparentcolor", self.transparent_color)

		self.root.title("Child Window")
		self.root.attributes('-alpha', .0)

	def resize(self, x: int, y: int):
		self.resize_window(x, y)
		self.media.resize(x, y)

	def resize_window(self, x: int, y: int):
		args = [x,y]
		res = []
		for i, num in enumerate(args):
			if isinstance(num, str):
				new = eval(f'self.size[{i}]{num}')
				if new < 0 and isinstance(new, int):
					raise ValueError(
f"{self.adress}Window.resize_window takes 2 arguments: integers > 0 or relaitive string numbers like '+100' or '-30'. Used relative and gets negative from current window size {self.size}"
						)
				else:
					res.append(new)
			else:
				res.append(num)

		self.root.geometry(f"{res[0]}x{res[1]}")
		self.size = res

	def mouse_listener(self, cursor):
		if cursor.position:
			absolute_x, absolute_y = cursor.position
			x = absolute_x - self.position[0]
			y = absolute_y - self.position[1]

			if callable(self.on_click):
				self.command(self.on_click)

			if self.hitbox and ( cursor.hitbox or cursor.position ):
				if cursor.hitbox in self.hitbox or cursor.position in self.hitbox:
					if self.polygon_id != None:
						self.canvas.itemconfig(self.polygon_id, fill=self.hitbox_show_color)

					if isinstance(self.on_hitbox, list) and len(self.on_hitbox):
						if isinstance(self.on_hitbox[0], str):
							self.command(self.on_hitbox)
					elif callable(self.on_hitbox):
						self.on_hitbox(self)

					if cursor.pressed_button and callable(self.on_hitbox_click):
						self.on_hitbox_click(self)
				else:
					if self.polygon_id != None:
						self.canvas.itemconfig(self.polygon_id, fill="blue" if self.hitbox_show_color != 'blue' else 'red')

					if isinstance(self.on_mouse_not_hitbox, list) and len(self.on_mouse_not_hitbox):
						if isinstance(self.on_mouse_not_hitbox[0], str):
							self.command(self.on_mouse_not_hitbox)
					elif callable(self.on_mouse_not_hitbox):
						self.on_mouse_not_hitbox(self)

					if cursor.pressed_button and callable(self.on_not_hitbox_click):
						self.on_not_hitbox_click(self)

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
				self.resize(args[0], args[1])
			else:
				raise ValueError(f"{self.adress}Command.window.resize takes 2 integers > 0, not {args} {type(args)}")

		elif cmd == 'resize_window':
			if len(args) >= 2:
				self.resize_window(args[0], args[1])
			else:
				raise ValueError(f"{self.adress}Command.window.resize takes 2 integers > 0, not {args} {type(args)}")

		elif cmd == 'resize_media':
			if not self.media:
				return ValueError(f"{self.adress}Window has not an media")

			if len(args) >= 2:
				self.media.resize(*args)
			else:
				raise ValueError(f"{self.adress}Command.media.resize takes 2 integers > 0, not {args} {type(args)}")

		elif cmd == 'rotate_media':
			if not self.media:
				return ValueError(f"{self.adress}Window has not an media")

			if len(args) >= 1:
				self.media.rotate(args[0])
			else:
				raise ValueError(f"{self.adress}Command.media.rotate takes an integer > 0, not {args} {type(args)}")

		elif cmd == 'set_media':
			if len(args) >= 1:
				if self.media != args[0]:
					self.media = args[0]
					self.media.set_label(self.media_label)
			else:
				raise ValueError(f"{self.adress}Command.media.set takes a Media, not {args} {type(args)}")

		elif cmd == 'wait':
			if len(args) > 0:
				check_value(args[0], [int, float], con=args[0] > 0 or args[0] == -1,
exc_msg=f"{self.adress}Invalid string command at Window.movements[{self.movement_index}]: {self.movements[self.movement_index]}. Command.wait takes an integer or float > 0 ( or -1 if it should be endless )"
					)
				self.pause = args[0]
			else:
				raise ValueError(
					f"{self.adress}Invalid string command at Window.movements[{self.movement_index}]: {self.movements[self.movement_index]}. Command.wait takes an integer or float > 0 ( or -1 if it should be endless )"
					)

	def step(self):
		if self.movements:
			if len(self.movements) > self.movement_index:
				is_list = ( isinstance(self.movements[self.movement_index], list) or isinstance(self.movements[self.movement_index], tuple) )

				if is_list and len(self.movements[self.movement_index]) == 2 and not isinstance(self.movements[self.movement_index][0], str):
					pos = self.movements[self.movement_index]
					self.root.geometry(f"+{pos[0]}+{pos[1]}")
					self.position = pos
					if self.default_hitbox:
						self.hitbox = self.default_hitbox.at_pos(pos)

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

	def rhythm_step(self):
		if self.rhythm != None and self.on_rhythm != None:
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

			if self.on_rhythm_index > -1 and self.on_rhythm and self.is_rhythm_enabled:
				self.command(self.on_rhythm[self.on_rhythm_index], rhythm=True)
				self.on_rhythm_index += 1
				if self.on_rhythm_index > len(self.on_rhythm)-1:
					self.on_rhythm_index = -1

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