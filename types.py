from typing import *
import imageio
import itertools as it

from tkinter import Label
from PIL import Image, ImageTk
from math import floor, ceil


class Command:
# you can use Command object instead of movement position in Window constructor, it allows you to perform animation ( resize, rotate_image and etc. ) in parallel with the movements
	def resize(x: int, y: int) -> list:
		res = ["resize"]
		for i, num in enumerate([x, y]):
			if isinstance(num, str):
				if num[0] in ['-', '+'] and num[1:].isdigit():
					res.append(num)
				else:
					raise ValueError(f"Command.resize takes 2 arguments: integers > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")
			elif isinstance(num, int):
				if num < 0:
					raise ValueError(f"Command.resize takes 2 arguments: integers > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")
				else:
					res.append(num)
			else:
				raise ValueError(f"Command.resize takes 2 arguments: integers > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")

		return res

	def wait(time: int) -> list:
		if isinstance(time, int) or isinstance(time, float):
			if time > 0:
				return ["wait", time]
			else:
				raise ValueError(f"Command.wait takes an integer > 0")
		else:
			raise ValueError(f"Command.wait takes an integer > 0")

	class window:
		def resize(x: int, y: int) -> list:
			res = ["resize_window"]
			for i, num in enumerate([x, y]):
				if isinstance(num, str):
					if num[0] in ['-', '+'] and num[1:].isdigit():
						res.append(num)
					else:
						raise ValueError(f"Command.window.resize takes 2 arguments: integer > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")
				elif isinstance(num, int):
					if num < 0:
						raise ValueError(f"Command.window.resize takes 2 arguments: integer > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")
					else:
						res.append(num)
				else:
					raise ValueError(f"Command.window.resize takes 2 arguments: integer > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")

			return res

		def resize_impulse(delta: int, speed: int = 1) -> list:
			res = [Command.window.resize( f'+{speed}', f'+{speed}' if speed >= 0 else f'{speed}' )] * floor(delta/2)
			res += [Command.window.resize('+0', '+0')] if delta % 2 != 0 else []
			res += [Command.window.resize( f'-{speed}', f'-{speed}' if speed >= 0 else f'+{speed*-1}' )] * floor(delta/2)
			return res

	class media:
		def resize(x: int, y: int) -> list:
			res = ["resize_media"]
			for i, num in enumerate([x, y]):
				if isinstance(num, str):
					if num[0] in ['-', '+'] and num[1:].isdigit():
						res.append(num)
					else:
						raise ValueError(f"Command.media.resize takes 2 arguments: integer > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")
				elif isinstance(num, int):
					if num < 0:
						raise ValueError(f"Command.media.resize takes 2 arguments: integer > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")
					else:
						res.append(num)
				else:
					raise ValueError(f"Command.media.resize takes 2 arguments: integer > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")

			return res

		def resize_impulse(delta: int, speed: int = 1) -> list:
			check_value(delta, int, f"Command.media.resize_impulse takes an integer > 0 or a relative string numbers like '+100' or '-30', not {delta} {type(delta)}")
			res = [Command.media.resize( f'+{speed}', f'+{speed}' if speed >= 0 else f'{speed}' )] * floor(delta/2)
			res += [Command.media.resize('+0', '+0')] if delta % 2 != 0 else []
			res += [Command.media.resize( f'-{speed}', f'-{speed}' if speed >= 0 else f'+{speed*-1}' )] * floor(delta/2)
			return res

		def set(media) -> list: # better use preloaded and resized PIL.Image instead of string image path
			return ["set_media", media]

		def rotate(angle: int) -> list:
			if isinstance(angle, int):
				return ["rotate_media", angle]
			elif isinstance(angle, str):
				if angle[0] in ['-', '+'] and angle[1:].isdigit():
					return ["rotate_media", angle]
				else:
					raise ValueError(f"Command.media.rotate takes 2 arguments: integer > 0 or relative string numbers like '+100' or '-30', not '{angle}' {type(angle)}")
			else:
				raise ValueError(f"Command.media.rotate takes 2 arguments: integer > 0 or relative string numbers like '+100' or '-30', not '{angle}' {type(angle)}")

		def rotate_impulse(angle: int, speed: int = 1) -> list:
			check_value(angle, int, f"Command.media.resize_impulse takes an integer > 0 or a relative string numbers like '+100' or '-30', not {angle} {type(angle)}")
			res = [Command.media.rotate(f'+{speed}' if speed >= 0 else f'{speed}')] * floor(angle/2)
			res += [Command.media.rotate('+0')] if angle % 2 != 0 else []
			res += [Command.media.rotate(f'-{speed}' if speed >= 0 else f'+{speed*-1}')] * floor(angle/2)
			return res


class Media:
	class Image:
		def __init__(self, image: Union[str, Image], angle: int = 0,
			size: Union[list, tuple] = [], resize_max: Union[list, tuple] = [], resize_min: Union[list, tuple] = []
			):
			
			if isinstance(image, str):
				self.image = Image.open(image)
			elif isinstance(image, Image.Image):
				self.image = image
			else:
				raise ValueError(f"'image' constructor arg must be string path to image or PIL.Image object, not {image} {type(image)})")
			self.default_image = self.image

			if size:
				check_value(size, [list, tuple], exc_msg=f"'size' kwarg must be list or tuple of 2 integers > 0, not {size} {type(size)})")
				if len(size) == 2:
					if isinstance(size[0], int) and isinstance(size[1], int) and size[0] > 0 and size[1] > 0:
						self.size = size
						self.image = self.image.resize(size)
					else:
						raise ValueError(f"'size' constructor kwarg must be list or tuple of 2 integers > 0, not {size} {type(size)})")
				else:
					raise ValueError(f"'size' constructor kwarg must be list or tuple of 2 integers > 0, not {size} {type(size)})")
			else:
				self.size = None
			self.default_resized_image = self.image

			check_value(angle, int, exc_msg=f"'angle' constructor kwarg must be integer, not {angle} {type(angle)})")
			self.angle = angle
			self.image = self.image.rotate(angle)
			self.default_rotated_image = self.image

			if resize_max:
				check_value(resize_max, [list, tuple], exc_msg=f"'resize_max' kwarg must be list or tuple of 2 integers > 0, not {resize_max} {type(resize_max)})")
				if len(resize_max) == 2:
					if isinstance(resize_max[0], int) and isinstance(resize_max[1], int) and resize_max[0] > 0 and resize_max[1] > 0:
						self.resize_max = resize_max
					else:
						raise ValueError(f"'resize_max' constructor kwarg must be list or tuple of 2 integers > 0, not {resize_max} {type(resize_max)})")
				else:
					raise ValueError(f"'resize_max' constructor kwarg must be list or tuple of 2 integers > 0, not {resize_max} {type(resize_max)})")
			else:
				self.resize_max = None

			if resize_min:
				check_value(resize_min, [list, tuple], exc_msg=f"'resize_min' kwarg must be list or tuple of 2 integers > 0, not {resize_min} {type(resize_min)})")
				if len(resize_min) == 2:
					if isinstance(resize_min[0], int) and isinstance(resize_min[1], int) and resize_min[0] > 0 and resize_min[1] > 0:
						self.resize_min = resize_min
					else:
						raise ValueError(f"'resize_min' constructor kwarg must be list or tuple of 2 integers > 0, not {resize_min} {type(resize_min)})")
				else:
					raise ValueError(f"'resize_min' constructor kwarg must be list or tuple of 2 integers > 0, not {resize_min} {type(resize_min)})")
			else:
				self.resize_min = None

			self.photo = None
			self.label = None

		def set_label(self, label: Label):
			self.label = label
			self.photo = ImageTk.PhotoImage(self.image)
			self.label.config(image=self.photo)

		def resize(self, x: Union[int, str], y: Union[int, str]):
			res = []
			for i, num in enumerate([x,y]):
				if isinstance(num, int):
					if num > 0:
						if num > self.resize_max[i]:
							res.append(self.resize_max[i])
						elif num < self.resize_min[i]:
							res.append(self.resize_min[i])
						else:
							res.append(num)
					else:
						raise ValueError(f"Media.Image.resize takes 2 arguments: integers > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")

				elif isinstance(num, str):
					if num[0] in ['+', '-'] and num[1:].isdigit():
						new = eval(f"self.size[i]{num}")

						if new > 0:
							if new > self.resize_max[i]:
								res.append(self.resize_max[i])
							elif new < self.resize_min[i]:
								res.append(self.resize_min[i])
							else:
								res.append(new)
						else:
							raise ValueError(f"Media.Image.resize takes 2 arguments: integers > 0, not {new} {type(new)}")
					else:
						raise ValueError(f"Media.Image.resize takes 2 arguments: integers > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")
				
				else:
					raise ValueError(f"Media.Image.resize takes 2 arguments: integers > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")

			self.size = res
			self.image = self.default_rotated_image.resize(self.size)
			self.default_rotated_image = self.image
			if self.photo and self.label:
				self.photo = ImageTk.PhotoImage(self.image)
				self.label.config(image=self.photo)

		def rotate(self, angle: int):
			check_value(angle, int, exc_msg=f"Media.Image.rotate takes an integer > 0, not {angle} {type(angle)})")
			self.angle = self.angle + angle

			if self.angle >= 360:
				self.angle -= 360
			if self.angle <= -360:
				self.angle += 360

			self.image = self.default_resized_image.rotate(self.angle)
			if self.photo and self.label:
				self.photo = ImageTk.PhotoImage(self.image)
				self.label.config(image=self.photo)

	class Video:
		def __init__(self, video_path: str, size: Union[list, tuple] = [], angle: int = 0, duration: int = 1, cycle: bool = True, preload: bool = True):
			check_value(cycle, [bool, int], f"'cycle' constructor kwarg must be bool, not {cycle} {type(cycle)})")
			self.cycle = cycle

			self.video = imageio.get_reader(video_path)
			data = self.video.iter_data()
			self.data = it.cycle(data) if cycle else data
			self.frames = []

			if size:
				if isinstance(size, list) or isinstance(size, tuple):
					if len(size) == 2 and isinstance(size[0], int) and isinstance(size[0], int) and size[0] > 0 and size[1] > 0:
						self.size = size
					else:
						raise ValueError(f"'size' constructor kwarg must be list or tuple of 2 integers > 0, not {size} {type(size)})")
				else:
					raise ValueError(f"'size' constructor kwarg must be list or tuple of 2 integers > 0, not {size} {type(size)})")
			else:
				self.size = None

			if isinstance(angle, int):
				self.angle = angle
			else:
				raise ValueError(f"'angle' constructor kwarg must be integer, not {angle} {type(angle)})")

			self.photoes = None
			self.label = None
			self.update_count = 0

			check_value(duration, int, f"'duration' constructor kwarg must be integer > 0, not {duration} {type(duration)})")
			if duration > 0:
				self.duration = duration
			else:
				raise ValueError(f"'duration' constructor kwarg must be integer > 0, not {duration} {type(duration)})")

			check_value(preload, [bool, int], f"'preload' constructor kwarg must be bool, not {preload} {type(preload)})")
			self.preload = preload
			if preload:
				for frame in self.video.iter_data():
					if self.size:
						frame = Image.fromarray(frame).resize(self.size)
					if self.angle:
						frame = frame.rotate(self.angle)
					self.frames.append(frame)

		def step(self):
			try:
				frame = next(self.data)
				if self.size:
					frame = Image.fromarray(frame).resize(self.size)
				if self.angle:
					frame = frame.rotate(self.angle)
				return frame
			except StopIteration:
				return None

		def set_label(self, label: Label):
			self.label = label
			self.photo = ImageTk.PhotoImage(self.step())
			self.label.config(image=self.photo)

		def update(self, window, timeline, fps, cursor):
			if self.duration > 1:
				if self.update_count <= self.duration:
					self.update_count += 1
				else:
					self.update_count = 0
					self.photo = ImageTk.PhotoImage(self.step())
					self.label.config(image=self.photo)
			else:
				self.photo = ImageTk.PhotoImage(self.step())
				self.label.config(image=self.photo)


def check_value(value, vtype, exc_msg: str = ''):
	if isinstance(vtype, list) or isinstance(vtype, tuple):
		return isinstance(value, tuple(vtype))
	elif isinstance(value, vtype):
		return True
	else:
		raise ValueError(exc_msg)