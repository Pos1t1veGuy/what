from typing import *

import pyaudio
import wave
import imageio
import itertools as it

from tkinter import Label
from PIL import Image, ImageTk
from math import floor, sqrt
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
		def __init__(self, video_path: str, size: Union[list, tuple] = [], angle: int = 0,
			duration: int = 1, cycle: bool = True, preload: bool = True,
			on_start: Callable = None, on_end: Callable = None):
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


def check_value(value, vtype, exc_msg: str = ''):
	if isinstance(vtype, list) or isinstance(vtype, tuple):
		return isinstance(value, tuple(vtype))
	elif isinstance(value, vtype):
		return True
	else:
		raise ValueError(exc_msg)


# line between 2 points, it works with geometry math
class Segment:
	def __init__(self, from_pos: List[[int, int]], to_pos: List[[int, int]]):
		check_value(from_pos, [tuple, list], exc_msg=f"'from_pos' constructor arg must be list or tuple of 2 integers, not {from_pos} {type(from_pos)}")
		if len(from_pos) == 2 and all(isinstance(pos, int) for pos in from_pos):
			self.from_pos = list(from_pos)
		else:
			raise ValueError(f"'from_pos' constructor arg must be list or tuple of 2 integers, not {from_pos} {type(from_pos)}")

		check_value(to_pos, [tuple, list], exc_msg=f"'to_pos' constructor arg must be list or tuple of 2 integers, not {to_pos} {type(to_pos)}")
		if len(to_pos) == 2 and all(isinstance(pos, int) for pos in to_pos):
			self.to_pos = list(to_pos)
		else:
			raise ValueError(f"'to_pos' constructor arg must be list or tuple of 2 integers, not {to_pos} {type(to_pos)}")

		self.k = Segment.get_k(from_pos, to_pos)
		self.b = Segment.get_b(from_pos, to_pos)
		self.length = sqrt( (from_pos[0] - to_pos[0])**2 + (from_pos[1] - to_pos[1])**2 )

		self.max_x, self.min_x = max(from_pos[0], to_pos[0]), min(from_pos[0], to_pos[0])
		self.max_y, self.min_y = max(from_pos[1], to_pos[1]), min(from_pos[1], to_pos[1])

	def intersects(self, object, return_count: bool = False) -> bool:
		if isinstance(object, list):
			res = self.intersects_point(object)
			return int(res) if return_count else res
		elif isinstance(object, Segment):
			res = self.intersects_segment(object)
			return int(res) if return_count else res
		elif isinstance(object, HitPolygon):
			return self.intersects_polygon(object, return_count=return_count)
		else:
			raise ValueError(f"Segment.intersects takes Segment/HitPolygon/HitBox object or list of 2 integers, not {object} {type(object)}")

	def intersects_point(self, point: List[[int, int]]) -> bool:
		if len(point) == 2 and ( all(isinstance(pos, float) for pos in point) or all(isinstance(pos, int) for pos in point) ):
			if self.k:
				return float(point[1]) == self.k * point[0] + self.b and self.min_y <= point[1] <= self.max_y and self.min_x <= point[0] <= self.max_x
			else:
				return self.min_y <= point[1] <= self.max_y and self.min_x <= point[0] <= self.max_x
		else:
			raise ValueError(f"Segment.intersects_point takes a list or tuple of 2 integers, not {point} {type(point)}")

	def intersects_segment(self, segment) -> bool:
		if self.k == segment.k:
			if self.direction == 'horizontal':
				return self.intersects_point([segment.max_x, self.max_y]) and segment.intersects_point([segment.max_x, self.max_y])
			elif self.direction == 'vertical':
				return self.intersects_point([self.max_x, segment.max_y]) and segment.intersects_point([self.max_x, segment.max_y])

		x = (segment.b - self.b) / (self.k - segment.k)
		y = self.k * x + self.b

		return self.intersects_point([x,y]) and segment.intersects_point([x,y])

		return False

	def intersects_polygon(self, polygon, return_count: bool = False) -> bool:
		count = 0
		for segment in polygon.segments:
			if self.intersects_segment(segment):
				count += 1

		return bool(count) if not return_count else count

	def at_pos(self, position: List[[int, int]]):
		check_value(position, [tuple, list], exc_msg=f"Segment.at_pos takes a list of 2 integers, not {position} {type(position)})")
		
		if len(position) == 2 and all(isinstance(pos, int) for pos in position):
			new_from = (self.from_pos[0] + position[0], self.from_pos[1] + position[1])
			new_to = (self.to_pos[0] + position[0], self.to_pos[1] + position[1])
			return Segment(new_from, new_to)
		else:
			raise ValueError(f"Segment.at_pos takes a list of 2 integers, not {position} {type(position)})")

	@staticmethod
	def get_k(pos1: List[[int, int]], pos2: List[[int, int]]) -> int:
		if pos1[0] == pos2[0]: # if it is vertical line
			return 0
		elif pos1[1] == pos2[1]: # if it is horizontal line
			return 0
		else:
			return ( pos1[1] - pos2[1] ) / ( pos1[0] - pos2[0] )

	@staticmethod
	def get_b(pos1: List[[int, int]], pos2: List[[int, int]]) -> int:
		if pos1[0] == pos2[0]: # if it is vertical line
			return pos1[0]
		elif pos1[1] == pos2[1]: # if it is horizontal line
			return pos2[1]
		else:
			k = ( pos1[1] - pos2[1] ) / ( pos1[0] - pos2[0] )
			return pos1[1] - k * pos1[0]

	@property
	def as_geometry(self) -> str:
		if self.direction == 'vertical':
			return f'x = {self.from_pos[0]}'
		elif self.direction == 'horizontal':
			return f'y = {self.from_pos[1]}'
		else:
			return f'y = { self.k if self.k != 1 else "" }x{ (f" + {self.b}" if self.b > 0 else f" - {-1*self.b}") if self.b else "" }'

	@property
	def direction(self) -> str:
		if self.from_pos[0] == self.to_pos[0]: # y = num
			return 'vertical'
		elif self.from_pos[1] == self.to_pos[1]: # x = num
			return 'horizontal'
		else: # y = kx + b
			return 'normal'

	def __str__(self):
		return f"Segment[{self.from_pos} -> {self.to_pos}]: ({self.as_geometry})"

	def __repr__(self):
		return f"Segment[{self.from_pos} -> {self.to_pos}]: ({self.as_geometry})"

	def __call__(self, x: int):
		return self.k * x + self.b

	def __len__(self):
		return self.length


# like hitbox, but may be arbitrary figure with different vertices and different angles
class HitPolygon:
	def __init__(self, vertices: List[[ [int, int], [int, int], [int, int], [int, int] ]]):
		check_value(vertices, [tuple, list], exc_msg=f"'vertices' constructor arg must be list or tuple of lists or tuples of 2 integers, not {vertices} {type(vertices)}")
		if all([ isinstance(vertice, (list, tuple)) and len(vertice) == 2 for vertice in vertices ]):
			if all([ all([ isinstance(pos, int) for pos in vertice ]) for vertice in vertices ]):
				self.vertices = list(vertices)
			else:
				raise ValueError(f"'vertices' constructor arg must be (list or tuple) of (lists or tuples) of 2 integers, not {vertices} {type(vertices)}")
		else:
			raise ValueError(f"'vertices' constructor arg must be (list or tuple) of (lists or tuples) of 2 integers, not {vertices} {type(vertices)}")
		
		self.segments = []
		self.position = [0, 0]
		self.segment(vertices)

	def segment(self, positions: list):
		self.segments = []
		res = []

		for i in range(len( self.vertices )):
		    res.append( Segment(self.vertices[i-1], self.vertices[i]) )

		self.segments = res

	def at_pos(self, position: List[[int, int]]):
		self.position = position
		new_vertices = []
		for segment in self.segments:
			new_vertices.append( segment.at_pos(position).from_pos )

		return HitPolygon(new_vertices)

	def intersects(self, object, return_count: bool = False) -> bool:
		count = 0
		if isinstance(object, list):
			for segment in self.segments:
				if segment.intersects_point(object):
					count += 1

		elif isinstance(object, Segment):
			for segment in self.segments:
				if segment.intersects_segment(object):
					count += 1

		elif isinstance(object, HitPolygon):
			for first_segment in self.segments:
				for second_segment in object.segments:
					if first_segment.intersects_segment(second_segment):
						count += 1

		else:
			raise ValueError(f"Segment.intersects takes Segment object, list of 2 integers or HitPolygon object, not {object} {type(object)}")

		return bool(count) if not return_count else count

	def segments_by_point(self, position: List[[int, int]]):
		segments = []
		for segment in self.segments:
			if segment.intersects_point(position):
				segments.append(segment)

		return segments

	def segments_by_fromto_point(self, position: List[[int, int]]):
		segments = []
		for segment in self.segments:
			if position in [segment.from_pos, segment.to_pos]:
				segments.append(segment)

		return segments

	def segment_by_from_point(self, position: List[[int, int]]):
		for segment in self.segments:
			if list(position) == segment.from_pos:
				return segment

	def segment_by_to_point(self, position: List[[int, int]]):
		for segment in self.segments:
			if position == segment.to_pos:
				return segment

	@property
	def area(self) -> int:
		res = 0
		for segment in self.segments:
			res += segment.from_pos[0] * segment.to_pos[1] - segment.from_pos[1] * segment.to_pos[0]

		return abs(res) / 2

	@property
	def as_tk_polygon(self):
		res = []
		for pos in self.vertices:
			for xy in pos:
				res.append(xy)
		return res

	def __str__(self):
		return f"HitPolygon([{ len(self) } vertices], position={self.position}, area={self.area})"
	
	def __contains__(self, i: Union[list, tuple, Segment]):
		if isinstance(i, (list, tuple, HitBox, HitPolygon, Segment)):
			return self.intersects(i)
		else:
			if hasattr(i, 'hitbox'):
				if i.intersects(self):
					return True
			if hasattr(i, 'ray'):
				if i.intersects(self):
					return True
			return False

	def __iter__(self):
		return self.vertices

	def __list__(self):
		return self.vertices

	def __getitem__(self, i):
		return self.vertices[i]

	def __repr__(self):
		return f"HitPolygon({self.vertices})"

	def __len__(self):
		return len(self.vertices)

 
class HitBox(HitPolygon):
	def __init__(self, pos1: List[[int, int]], pos2: List[[int, int]]):
		super().__init__([ pos1, [pos1[0], pos2[1]], pos2, [pos2[0], pos1[1]] ])

	def at_pos(self, position: List[[int, int]]):
		new_vertices = [ segment.at_pos(position).from_pos for segment in self.segments ]
		return HitBox(new_vertices[:2][0], new_vertices[2:4][0])

	def intersects_hitbox(self, hitbox) -> bool:
		if isinstance(hitbox, HitBox):
			if hitbox.left_up[0] <= self.left_up[0] <= hitbox.right_up[0] or hitbox.left_up[0] <= self.right_up[0] <= hitbox.right_up[0]:
				if hitbox.left_up[1] <= self.left_up[1] <= hitbox.left_down[1] or hitbox.left_up[1] <= self.left_down[1] <= hitbox.left_down[1]:
					return True

			return False
		else:
			raise ValueError(f"HitBox.intersects_hitbox takes HitBox object, not {hitbox} {type(hitbox)}")

	def intersects_point(self, point: List[[int, int]]) -> bool:
		if isinstance(hitbox, HitBox):
			return self.left_up[0] <= point[0] <= self.right_up[0] and self.left_up[1] <= point[1] <= self.left_down[1]
		else:
			raise ValueError(f"HitBox.intersects_point takes a list of 2 integers, not {point} {type(point)}")

	@property
	def edge_length(self):
		return abs(self.left_up[0] - self.right_up[0])

	@property
	def upper_segment(self):
		return self.segment_by_from_point(self.left_up)
	@property
	def lower_segment(self):
		return self.segment_by_from_point(self.right_down)
	@property
	def right_segment(self):
		return self.segment_by_from_point(self.right_up)
	@property
	def left_segment(self):
		return self.segment_by_from_point(self.left_down)

	@property
	def left_up(self):
		return [min(x for (x,y) in self.vertices), min(y for (x,y) in self.vertices)]
	@property
	def up_left(self):
		return [min(x for (x,y) in self.vertices), min(y for (x,y) in self.vertices)]

	@property
	def left_down(self):
		return [min(x for (x,y) in self.vertices), max(y for (x,y) in self.vertices)]
	@property
	def down_left(self):
		return [min(x for (x,y) in self.vertices), max(y for (x,y) in self.vertices)]

	@property
	def right_up(self):
		return [max(x for (x,y) in self.vertices), min(y for (x,y) in self.vertices)]
	@property
	def up_right(self):
		return [max(x for (x,y) in self.vertices), min(y for (x,y) in self.vertices)]

	@property
	def right_down(self):
		return [max(x for (x,y) in self.vertices), max(y for (x,y) in self.vertices)]
	@property
	def down_right(self):
		return [max(x for (x,y) in self.vertices), max(y for (x,y) in self.vertices)]

	def __str__(self):
		return f"HitBox([{self.edge_length}x{self.edge_length}], position={self.position} area={self.area})"

	def __repr__(self):
		return f"HitBox({self.left_up}, {self.right_down})"


class Sound:
# you can use music and sounds: create object and play() or stop() it ( you can use it in another thread, make play(threading=True) )
	def __init__(self, filepath: str):
		self.filepath = filepath
		self.wfile = wave.open(filepath, 'rb')
		self.audio = pyaudio.PyAudio()

		self.playing = False

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