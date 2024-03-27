from typing import *

import pyaudio
import wave
import imageio
import itertools as it

from tkinter import Label, Tk
from PIL import Image, ImageTk
from math import floor
from threading import Thread as th


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
		check_value(time, [int, float], con=time > 0, exc_msg=f"Command.wait takes an integer > 0")
		return ["wait", time]

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
			check_value(delta, int, exc_msg=f"Command.media.resize_impulse takes an integer > 0 or a relative string numbers like '+100' or '-30', not {delta} {type(delta)}")
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
			check_value(angle, int, exc_msg=f"Command.media.resize_impulse takes an integer > 0 or a relative string numbers like '+100' or '-30', not {angle} {type(angle)}")
			res = [Command.media.rotate(f'+{speed}' if speed >= 0 else f'{speed}')] * floor(angle/2)
			res += [Command.media.rotate('+0')] if angle % 2 != 0 else []
			res += [Command.media.rotate(f'-{speed}' if speed >= 0 else f'+{speed*-1}')] * floor(angle/2)
			return res


class Media:
# you can use it in Window media constructor kwarg to insect image or video into window
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
				check_value(size, [list, tuple], con=len(size) == 2 and isinstance(size[0], int) and isinstance(size[1], int) and size[0] > 0 and size[1] > 0,
					exc_msg=f"'size' kwarg must be list or tuple of 2 integers > 0, not {size} {type(size)})")
				self.size = size
				self.image = self.image.resize(size)
			else:
				self.size = None
			self.default_resized_image = self.image

			check_value(angle, int, exc_msg=f"'angle' constructor kwarg must be integer, not {angle} {type(angle)})")
			self.angle = angle
			self.image = self.image.rotate(angle)
			self.default_rotated_image = self.image

			if resize_max:
				check_value(resize_max, [list, tuple],
					con=len(resize_max) == 2 and isinstance(resize_max[0], int) and isinstance(resize_max[1], int) and resize_max[0] > 0 and resize_max[1] > 0,
					exc_msg=f"'resize_max' kwarg must be list or tuple of 2 integers > 0, not {resize_max} {type(resize_max)})")
				self.resize_max = resize_max
			else:
				self.resize_max = None

			if resize_min:
				check_value(resize_min, [list, tuple],
					con=len(resize_min) == 2 and isinstance(resize_min[0], int) and isinstance(resize_min[1], int) and resize_min[0] > 0 and resize_min[1] > 0,
					exc_msg=f"'resize_min' kwarg must be list or tuple of 2 integers > 0, not {resize_min} {type(resize_min)})")
				self.resize_min = resize_min
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
					check_value(num, int, con=num > 0,
						exc_msg=f"Media.Image.resize takes 2 arguments: integers > 0 or relative string numbers like '+100' or '-30', not {num} {type(num)}")
					if num > self.resize_max[i]:
						res.append(self.resize_max[i])
					elif num < self.resize_min[i]:
						res.append(self.resize_min[i])
					else:
						res.append(num)

				elif isinstance(num, str):
					if num[0] in ['+', '-'] and num[1:].isdigit():
						new = eval(f"self.size[i]{num}")

						check_value(new, [float, int], con=new > 0,
							exc_msg=f"Media.Image.resize takes 2 arguments: integers > 0, not {new} {type(new)}")
						if new > self.resize_max[i]:
							res.append(self.resize_max[i])
						elif new < self.resize_min[i]:
							res.append(self.resize_min[i])
						else:
							res.append(new)
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
		def __init__(self, video_path: str, size: Union[list, tuple] = [], angle: int = 0,
			duration: int = 1, cycle: bool = True, preload: bool = True,
			on_start: Callable = None, on_end: Callable = None):
			check_value(cycle, [bool, int], exc_msg=f"'cycle' constructor kwarg must be bool, not {cycle} {type(cycle)})")
			self.cycle = bool(cycle)

			self.video = imageio.get_reader(video_path)
			data = self.video.iter_data()
			self.data = it.cycle(data) if cycle else data
			self.frames = []

			if size:
				check_value(size, [list, tuple], con=len(size) == 2 and isinstance(size[0], int) and isinstance(size[0], int) and size[0] > 0 and size[1] > 0,
					exc_msg=f"'size' constructor kwarg must be list or tuple of 2 integers > 0, not {size} {type(size)})")
				self.size = size
			else:
				self.size = None

			check_value(angle, int, exc_msg=f"'angle' constructor kwarg must be integer, not {angle} {type(angle)})")
			self.angle = angle

			if callable(on_start):
				self.on_start = on_start
			else:
				self.on_start = None
			if callable(on_end):
				self.on_start = on_start
			else:
				self.on_start = None

			self.photoes = None
			self.label = None
			self.update_count = 0
			self.started = False
			self.dead = False

			check_value(duration, int, con=duration > 0, exc_msg=f"'duration' constructor kwarg must be integer > 0, not {duration} {type(duration)})")
			self.duration = duration

			check_value(preload, [bool, int], exc_msg=f"'preload' constructor kwarg must be bool, not {preload} {type(preload)})")
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
				if callable(self.on_end) and self.dead:
					self.on_end(self)
					self.dead = True

				return None

		def set_label(self, label: Label):
			self.label = label
			self.photo = ImageTk.PhotoImage(self.step())
			self.label.config(image=self.photo)

		def update(self, window, timeline, fps, cursor):
			if callable(self.on_start) and not self.started:
				self.on_start(self)
				self.started = True

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


def check_value(value, vtype, con: Union[bool, List[bool]] = True, exc_msg: str = ''):
	if isinstance(con, bool) or isinstance(con, int):
		condition = bool(con)
	elif isinstance(con, list) or isinstance(con, tuple):
		condition = all(con)
	else:
		raise ValueError(f"'con' function kwarg must be bool or list of bools, not {con} {type(con)}")

	if isinstance(vtype, list) or isinstance(vtype, tuple):
		return isinstance(value, tuple(vtype)) and condition
	elif isinstance(value, vtype):
		return condition
	elif vtype == None:
		return isinstance(value, type(None)) and condition
	else:
		raise ValueError(exc_msg)


class Sound:
# you can use music and sounds: create object and play() or stop() it ( you can use it in another thread, make play(threading=True) )
	def __init__(self, filepath: str):
		self.filepath = filepath
		self.wfile = wave.open(filepath, 'rb')
		self.audio = pyaudio.PyAudio()

		self.playing = False
		self.stream = None

		self.audio_thread = th(target=self.audio_player, args=(1024,))

	def play(self, chunk: int = 1024, threading=False):
		if not threading:
			self.audio_player(chunk)
		else:
			self.audio_thread = th(target=self.audio_player, args=(chunk,))
			self.audio_thread.start()

	def stop(self):
		self.playing = False

	def audio_player(self, chunk: int):
		self.playing = True
		self.stream = self.audio.open(
			format=self.audio.get_format_from_width(self.wfile.getsampwidth()),
			channels=self.wfile.getnchannels(),
			rate=self.wfile.getframerate(),
			output=True
			)

		self.data = True
		while self.data and self.stream and self.playing:
			self.step(chunk)

		self.playing = False
		self.stream.close()

	def step(self, chunk: int):
		self.data = self.wfile.readframes(chunk)
		self.stream.write(self.data)

	def close(self):
		if self.stream:
			self.stream.close()

		self.wfile.close()
		self.audio.terminate()

	def __del__(self):
		self.close()

	def __str__(self):
		return f'Sound(filepath="{self.filepath}", playing={self.playing})'

	def __repr__(self):
		return f'Sound(filepath="{self.filepath}")'