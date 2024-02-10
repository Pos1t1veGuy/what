import os, time
import pyautogui as pag

from PIL import Image, ImageTk
from math import floor
from tkinter import Label


class Window: # it is child window
	def __init__(self, movements: list, size: list, cycle: bool = False,
		always_on_top: bool = True, show_frame: bool = False, alpha: float = 1.0, transparent_color = None, bg_color = "black",
		image_path: str = '', image_size: list = [], spawn_time: int = 0, alive_time: int = None, rhythm: int = -1, on_rhythm: list = []):
		'''
		movements: list of the positions, it change position after every screen update
		cycle: it may move endlessly
		transparent_color: everywhere in window this color will be transparent
		spawn_time: time in seconds when window should spawn after connected timeline initialize
		alive_time: time in seconds how long it will be alive after spawn
		rhythm: time in seconds how many seconds it will execute on_rhythm commands
		on_rhythm: list of Command objects
		'''

		self.root = None # Window.root will be loaded after use Window.set_window(tkinter.TopLevel)
		self.movements = movements
		self.cycle = cycle
		self.default_size = size
		self.size = size
		self.image = None
		self.image_path = image_path
		self.spawn_time = spawn_time
		self.max_alive_time = alive_time
		self.alive_time = 0
		self.position = [0,0]
		self.rhythm = rhythm
		self.image_size = [0,0]
		self.fixed_image_size = image_size

		self.screen_width = None
		self.screen_height = None

		self.always_on_top = always_on_top
		self.show_frame = show_frame
		self.transparent_color = transparent_color
		self.bg_color = bg_color

		self.dead = False
		self.movement_index = 0
		self.rhythm_index = 0
		self.on_rhythm_index = -1
		self.alpha = .0
		self.on_rhythm = on_rhythm

		self.default_alpha = float(alpha)
		self.default_image = None

	def update(self, tl_alive_time: int, fps: int):
# returns true if this window is dead, do not use Window.update before Window.root loads ( to load Window.root use Window.set_window(tkinter.TopLevel) )
		self.alive_time += 1/fps

		if tl_alive_time >= self.spawn_time:
			if self.root:
				if not self.dead:
					if self.max_alive_time != None and self.max_alive_time <= tl_alive_time:
						if self.root:
							self.root.destroy()

						self.dead = True
						return False

					if self.alpha == .0:
						self.root.attributes('-alpha', self.default_alpha)
						self.alpha = self.default_alpha
						del self.default_alpha

					if self.rhythm != -1:
						if self.alive_time >= self.rhythm_index * self.rhythm:
							self.rhythm_index += 1
							self.on_rhythm_index = 0

						if self.on_rhythm_index > -1:
							self.command(self.on_rhythm[self.on_rhythm_index])
							self.on_rhythm_index += 1
							if self.on_rhythm_index > len(self.on_rhythm)-1:
								self.on_rhythm_index = -1

					self.step()

				return True
			else:
				raise AttributeError('Child window "Window.root" did not configured')
		return True

	def set_window(self, root):
		self.root = root
		self.root.geometry(f"{self.default_size[0]}x{self.default_size[1]}")

		if self.image_path:
			self.image_label = Label(self.root)
			self.image_label.pack()
			self.set_image(self.image_path)
			self.default_image = self.image
			self.image_size = self.image.size

		self.root.wm_attributes("-topmost", self.always_on_top)
		self.root.overrideredirect(not self.show_frame)
		self.root.attributes('-alpha', float(self.alpha))
		self.root.configure(bg=self.bg_color)

		self.screen_width = self.root.winfo_screenwidth()
		self.screen_height = self.root.winfo_screenheight()

		if self.transparent_color:
			self.root.wm_attributes("-transparentcolor", transparent_color)

		self.root.title("Child Window")

		self.root.attributes('-alpha', .0)

	def resize(self, x: int, y: int, default: bool = False):
		self.root.geometry(f"{x}x{y}")
		self.size = [x,y]

		if self.image:
			if not default:
				self.photo = ImageTk.PhotoImage(self.image.resize([x,y]))
				self.image_size = [x,y]
			else:
				self.photo = ImageTk.PhotoImage(self.default_image)
				self.image_size = self.default_image.size

			self.image_label.configure(image=self.photo, anchor="center")
		else:
			return ValueError("Window has not an image")

	def resize_window(self, x: int, y: int, default: bool = False):
		if default:
			self.root.geometry(f"{self.default_size[0]}x{self.default_size[1]}")
			self.size = self.default_size
		else:
			self.root.geometry(f"{x}x{y}")
			self.size = [x,y]

	def resize_image(self, x: int, y: int, default: bool = False):
		if self.image:
			if not default:
				self.photo = ImageTk.PhotoImage(self.image.resize([x,y]))
				self.image_size = [x,y]
			else:
				self.photo = ImageTk.PhotoImage(self.default_image)
				self.image_size = self.default_image.size

			self.image_label.configure(image=self.photo, anchor="center")
		else:
			return ValueError("Window has not an image")

	def set_image(self, image: str):
		if image:
			if isinstance(image, str):
				if os.path.isfile(image):
					try:
						Image.open(image).verify()
					except (IOError, SyntaxError):
						raise InvalidImageError(image)
					self.image = Image.open(image)
				else:
					raise FileNotFoundError(image)

			elif isinstance(image, Image.Image):
				self.image = image

			else:
				raise ValueError(f"image must be string path to image file or PIL.Image object, not '{image}', {type(image)}")

			if self.size:
				if self.fixed_image_size:
					self.image = self.image.resize(self.fixed_image_size)
				else:
					self.image = self.image.resize(self.size)

			self.image_size = self.image.size
			self.photo = ImageTk.PhotoImage(self.image)
			self.image_label.configure(image=self.photo)
		else:
			raise ValueError(f"image must be string path to image file or PIL.Image object, not '{image}', {type(image)}")

	def command(self, command: list):
		cmd, args = command[0], command[1:]

		if cmd == 'resize':
			if not self.image:
				return ValueError("Window has not an image")

			res = []
			for i, num in enumerate(args):
				if isinstance(num, str):
					new = eval(f'self.size[{i}]{num}')
					if new < 0:
						raise ValueError(
f"{['x','y'][i]} must be integer number greater than 0 or relaitive string number like '+100' or '-30'. Used relative and gets negative from current window size {self.size}"
							)
					else:
						res.append(new)
				else:
					res.append(num)

			self.resize( int(res[0]), int(res[1]) )
		elif cmd == 'resize_window':
			res = []
			for i, num in enumerate(args):
				if isinstance(num, str):
					if '-' in num:
						new = self.size[i] - int(num[1:])
					elif '+' in num:
						new = self.size[i] + int(num[1:])
					if 30 in self.size:
						exit()
					if new < 0:
						raise ValueError(
f"{['x','y'][i]} must be integer number greater than 0 or relaitive string number like '+100' or '-30'. Used relative and gets negative from current window size {self.size}"
							)
					else:
						res.append(new)
				else:
					res.append(num)

			self.resize_window( int(res[0]), int(res[1]) )
		elif cmd == 'resize_image':
			if not self.image:
				return ValueError("Window has not an image")

			res = []
			for i, num in enumerate(args):
				if isinstance(num, str):
					new = eval(f'self.image_size[{i}]{num}')
					if new < 0:
						raise ValueError(
f"{['x','y'][i]} must be integer number greater than 0 or relaitive string number like '+100' or '-30'. Used relative and gets negative from current window size {self.size}"
							)
					else:
						res.append(new)
				else:
					res.append(num)

			self.resize_image( int(res[0]), int(res[1]) )
		elif cmd == 'set_image':
			self.set_image(args[0])
		else:
			raise ValueError(f"Unknow string command at Window.movements[{self.movement_index}]: {self.movements[self.movement_index]}")

	def step(self):
		if self.movements:
			if len(self.movements)-1 > self.movement_index:
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
				if self.cycle:
					self.movement_index = 0
					if self.size != self.default_size or self.image != self.default_image:
						if self.default_image:
							self.resize(*self.default_size, default=True)
						else:
							self.resize_window(*self.default_size, default=True)
						self.on_rhythm_index = -1
						self.on_rhythm_index = -1
				else:
					self.root.destroy()
					self.dead = False
					return False
		else:
			if self.alpha != .0:
				self.root.attributes('-alpha', .0)
				self.alpha = .0


class Command:
# you can use Command object instead of movement position in Window constructor, it allows you to perform animation ( resize, rotate_image and etc. ) in parallel with the movements
	def resize(x: int, y: int) -> list:
		res = ["resize"]
		for i, num in enumerate([x, y]):
			if isinstance(num, str):
				if num[0] in ['-', '+'] and num[1:].isdigit():
					res.append(num)
				else:
					raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not {num}")
			elif isinstance(num, int):
				if num < 0:
					raise ValueError(f"{['x','y'][i]} must be greater than 0, not {num}")
				else:
					res.append(num)
			else:
				raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not {num}")

		return res

	class window:
		def resize(x: int, y: int) -> list:
			res = ["resize_window"]
			for i, num in enumerate([x, y]):
				if isinstance(num, str):
					if num[0] in ['-', '+'] and num[1:].isdigit():
						res.append(num)
					else:
						raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not {num}")
				elif isinstance(num, int):
					if num < 0:
						raise ValueError(f"{['x','y'][i]} must be greater than 0, not {num}")
					else:
						res.append(num)
				else:
					raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not {num}")

			return res

		def impulse(delta: int, power: int = 1) -> list:
			res = [Command.window.resize( f'+{power}', f'+{power}' )] * floor(delta/2)
			res += [Command.window.resize('+0', '+0')] if delta % 2 != 0 else []
			res += [Command.window.resize( f'-{power}', f'-{power}' )] * floor(delta/2)
			return res

	class image:
		def resize(x: int, y: int) -> list:
			res = ["resize_image"]
			for i, num in enumerate([x, y]):
				if isinstance(num, str):
					if num[0] in ['-', '+'] and num[1:].isdigit():
						res.append(num)
					else:
						raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not {num}")
				elif isinstance(num, int):
					if num < 0:
						raise ValueError(f"{['x','y'][i]} must be greater than 0, not {num}")
					else:
						res.append(num)
				else:
					raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not {num}")

			return res

		def impulse(delta: int, power: int = 1) -> list:
			res = [Command.image.resize( f'+{power}', f'+{power}' )] * floor(delta/2)
			res += [Command.image.resize('+0', '+0')] if delta % 2 != 0 else []
			res += [Command.image.resize( f'-{power}', f'-{power}' )] * floor(delta/2)
			return res

		def set(image: str) -> list: # better use preloaded and resized PIL.Image instead of string image path
			if isinstance(image, str) or isinstance(image, Image.Image):
				return ["set_image", image]
			else:
				raise ValueError(f"image must be string path to image file or PIL.Image object, not '{image}', {type(image)}")

		def rotate(degree: int) -> list:
			return []