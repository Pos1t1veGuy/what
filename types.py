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
					raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not {num}")
			elif isinstance(num, int):
				if num < 0:
					raise ValueError(f"{['x','y'][i]} must be greater than 0, not {num}")
				else:
					res.append(num)
			else:
				raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not {num}")

		return res

	def wait(time: int) -> list:
		if isinstance(time, int) or isinstance(time, float):
			if time > 0:
				return ["wait", time]
			else:
				raise ValueError(f"'time' must be integer number more than 0")
		else:
			raise ValueError(f"'time' must be integer number more than 0")

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
						raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not '{num}' {type(num)}")
				elif isinstance(num, int):
					if num < 0:
						raise ValueError(f"{['x','y'][i]} must be greater than 0, not {num}")
					else:
						res.append(num)
				else:
					raise ValueError(f"{['x','y'][i]} must be integer number greater than 0 or relative string number like '+100' or '-30', not '{num}' {type(num)}")

			return res

		def resize_impulse(delta: int, speed: int = 1) -> list:
			res = [Command.media.resize( f'+{speed}', f'+{speed}' if speed >= 0 else f'{speed}' )] * floor(delta/2)
			res += [Command.media.resize('+0', '+0')] if delta % 2 != 0 else []
			res += [Command.media.resize( f'-{speed}', f'-{speed}' if speed >= 0 else f'+{speed*-1}' )] * floor(delta/2)
			return res

		def set(media: str) -> list: # better use preloaded and resized PIL.Image instead of string image path
			if isinstance(media, str) or isinstance(media, Image.Image):
				return ["set_media", media]
			else:
				raise ValueError(f"media must be string path to media file or PIL.Image object, not '{media}', {type(media)}")

		def rotate(angle: int) -> list:
			if isinstance(angle, int):
				return ["rotate_media", angle]
			elif isinstance(angle, str):
				if angle[0] in ['-', '+'] and angle[1:].isdigit():
					return ["rotate_media", angle]
				else:
					raise ValueError(f"angle must be integer number greater than 0 or relative string number like '+100' or '-30', not '{angle}' {type(angle)}")
			else:
				raise ValueError(f"angle must be integer number greater than 0 or relative string number like '+100' or '-30', not '{angle}' {type(angle)}")

		def rotate_impulse(angle: int, speed: int = 1) -> list:
			res = [Command.media.rotate(f'+{speed}' if speed >= 0 else f'{speed}')] * floor(angle/2)
			res += [Command.media.rotate('+0')] if angle % 2 != 0 else []
			res += [Command.media.rotate(f'-{speed}' if speed >= 0 else f'+{speed*-1}')] * floor(angle/2)
			return res


class Media:
	class Image:
		def __init__(self, image: Union[str, Image], size: Union[list, tuple] = [], angle: int = 0):
			
			if isinstance(image, str):
				self.image = Image.open(image)
			elif isinstance(image, Image.Image):
				self.image = image
			else:
				raise ValueError(f"'image' arg must be string path to image or PIL.Image object, not {image} {type(image)})")
			self.default_image = self.image

			if size:
				if isinstance(size, list) or isinstance(size, tuple):
					if len(size) == 2 and isinstance(size[0], int) and isinstance(size[0], int) and size[0] > 0 and size[1] > 0:
						self.size = size
						self.image = self.image.resize(size)
					else:
						raise ValueError(f"'size' kwarg must be list or tuple of 2 integers more than 0, not {size} {type(size)})")
				else:
					raise ValueError(f"'size' kwarg must be list or tuple of 2 integers more than 0, not {size} {type(size)})")
			else:
				self.size = None
			self.default_resized_image = self.image

			if isinstance(angle, int):
				self.angle = angle
				self.image = self.image.rotate(angle)
			else:
				raise ValueError(f"'angle' kwarg must be integer, not {angle} {type(angle)})")
			self.default_rotated_image = self.image

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
						res.append(num)
					else:
						raise ValueError(f"'{['x', 'y'][i]}' must be integer more than 0 or relative string number like '+100' or '-30', not {num} {type(num)}")

				elif isinstance(num, str):
					if num[0] in ['+', '-'] and num[1:].isdigit():
						new = eval(f"self.size[i]{num}")

						if new > 0:
							res.append(new)
						else:
							raise ValueError(f"'{['x', 'y'][i]}' relative string number must returns integer more than 0, not {new} {type(new)}")
					else:
						raise ValueError(f"'{['x', 'y'][i]}' must be integer more than 0 or relative string number like '+100' or '-30', not {num} {type(num)}")
				
				else:
					raise ValueError(f"'{['x', 'y'][i]}' must be integer more than 0 or relative string number like '+100' or '-30', not {num} {type(num)}")
			
			self.size = res
			self.image = self.default_rotated_image.resize(self.size)
			self.default_rotated_image = self.image
			if self.photo and self.label:
				self.photo = ImageTk.PhotoImage(self.image)
				self.label.config(image=self.photo)

		def rotate(self, angle: int):
			if isinstance(angle, int):
				self.angle = self.angle + angle

				if self.angle >= 360:
					self.angle -= 360
				if self.angle <= -360:
					self.angle += 360

				self.image = self.default_resized_image.rotate(self.angle)
				if self.photo and self.label:
					self.photo = ImageTk.PhotoImage(self.image)
					self.label.config(image=self.photo)
			else:
				raise ValueError(f"'angle' kwarg must be integer, not {angle} {type(angle)})")

	class Video:
		def __init__(self, video_path: str, size: Union[list, tuple] = [], angle: int = 0, duration: int = 1, cycle: bool = True, preload: bool = True):
			check_value(cycle, [bool, int], f"'cycle' kwarg must be bool, not {cycle} {type(cycle)})")
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
						raise ValueError(f"'size' kwarg must be list or tuple of 2 integers more than 0, not {size} {type(size)})")
				else:
					raise ValueError(f"'size' kwarg must be list or tuple of 2 integers more than 0, not {size} {type(size)})")
			else:
				self.size = None

			if isinstance(angle, int):
				self.angle = angle
			else:
				raise ValueError(f"'angle' kwarg must be integer, not {angle} {type(angle)})")

			self.photoes = None
			self.label = None
			self.update_count = 0

			check_value(duration, int, f"'duration' kwarg must be integer more than 0, not {duration} {type(duration)})")
			if duration > 0:
				self.duration = duration
			else:
				raise ValueError(f"'duration' kwarg must be integer more than 0, not {duration} {type(duration)})")

			check_value(preload, [bool, int], f"'preload' kwarg must be bool, not {preload} {type(preload)})")
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