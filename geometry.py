from typing import *

from tkinter import Tk, Canvas
from math import sqrt, cos, sin, radians, pi

from .types import check_value

class Line:
	def __init__(self, from_pos: List[[int, int]], to_pos: List[[int, int]]):
		check_value(from_pos, [tuple, list], con=len(from_pos) == 2 and all(isinstance(pos, (int, float)) for pos in from_pos),
			exc_msg=f"'from_pos' constructor arg must be list or tuple of 2 integers or floats, not {from_pos} {type(from_pos)}")
		self.from_pos = list(from_pos)
		
		check_value(to_pos, [tuple, list], con=len(to_pos) == 2 and all(isinstance(pos, (int, float)) for pos in to_pos),
			exc_msg=f"'to_pos' constructor arg must be list or tuple of 2 integers or floats, not {to_pos} {type(to_pos)}")
		self.to_pos = list(to_pos)

		self.k = Line.get_k(from_pos, to_pos)
		self.b = Line.get_b(from_pos, to_pos)

	def intersects(self, object, return_positions: bool = False) -> bool:
		if isinstance(object, list):
			res = self.intersects_point(object)
			return object if return_positions else res
		elif isinstance(object, Line):
			return self.intersects_line(object, return_position=return_positions)
		elif isinstance(object, Ray):
			return self.intersects_ray(object, return_position=return_positions)
		elif isinstance(object, Segment):
			return self.intersects_segment(object, return_position=return_positions)
		elif isinstance(object, HitPolygon):
			return self.intersects_polygon(object, return_positions=return_positions)
		elif isinstance(object, HitCircle):
			return self.intersects_circle(object, return_positions=return_positions)
		else:
			raise ValueError(f"Line.intersects takes Line/Ray/Segment/HitPolygon/HitBox/HitCircle object or list of 2 integers, not {object} {type(object)}")

	def intersects_point(self, point: List[[int, int]]) -> bool:
		check_value(point, [list, tuple], con=len(point) == 2 and ( all(isinstance(pos, float) for pos in point) or all(isinstance(pos, int) for pos in point) ),
			exc_msg=f"Line.intersects_point takes a list or tuple of 2 integers, not {point} {type(point)}")

		if self.k:
			return float(point[1]) == self.k * point[0] + self.b
		else:
			if self.direction == 'horizontal':
				return point[1] == from_pos[1]
			elif self.direction == 'vertical':
				return point[0] == from_pos[0]

	def intersects_line(self, line, return_position: bool = False) -> bool:
		if self.k == line.k:
			if self.direction == 'horizontal':
				return self.intersects_point([line.max_x, self.max_y]) and line.intersects_point([line.max_x, self.max_y])
			elif self.direction == 'vertical':
				return self.intersects_point([self.max_x, line.max_y]) and line.intersects_point([self.max_x, line.max_y])

		x = (line.b - self.b) / (self.k - line.k)
		y = self.k * x + self.b

		if return_position:
			if self.intersects_point([x,y]) and line.intersects_point([x,y]):
				return [x,y]
			else:
				return []
		else:
			return self.intersects_point([x,y]) and line.intersects_point([x,y])

	def intersects_ray(self, ray, return_position: bool = False) -> bool:
		return self.intersects_line(ray, return_position=return_position)

	def intersects_segment(self, segment, return_position: bool = False) -> bool:
		return self.intersects_line(segment, return_position=return_position)

	def intersects_polygon(self, polygon, return_positions: bool = False) -> bool:
		positions = []
		for segment in polygon.segments:
			if self.intersects_segment(segment):
				if return_positions:
					positions.append(self.intersects_segment(segment, return_position=True))
				else:
					return True

		return positions

	def intersects_circle(self, circle, return_positions: bool = False) -> bool:
		# (1+k)x^2 + (2kb)x + (b^2 - r^2) = 0 with segment y=kx+b and circle (a+x)^2+(b+y)^2=r^2
		# ax^2 + bx + c = 0
		D = (2*circle.k*self.b)**2 - 4 * (1+self.k) * (self.b**2 - circle.radius**2)
		if return_positions:
			if D == 0:
				x = -(2*self.k*self.b) / 2 * (1+self.k)
				if self.intersects_point([x, self(x)]):
					return [x, self(x)]

			elif D > 0:
				x1 = ( -(2*self.k*self.b) + sqrt(D) ) / 2 * (1+self.k)
				x2 = ( -(2*self.k*self.b) - sqrt(D) ) / 2 * (1+self.k)
				if self.intersects_point([x1, self(x1)]) and self.intersects_point([x2, self(x2)]):
					return [x1, self(x1)], [x2, self(x2)]

			return []
		else:
			return D >= 0

	def at_pos(self, position: List[[int, int]]):
		check_value(position, [tuple, list], con=len(position) == 2 and all(isinstance(pos, int) for pos in position),
			exc_msg=f"Segment.at_pos takes a list of 2 integers, not {position} {type(position)})")
		
		new_from = (self.from_pos[0] + position[0], self.from_pos[1] + position[1])
		new_to = (self.to_pos[0] + position[0], self.to_pos[1] + position[1])
		return Line(new_from, new_to)

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
		elif self.direction == 'point':
			return f'x = {self.from_pos[0]}; y = {self.from_pos[1]}'
		else:
			return f'y = { self.k if self.k != 1 else "" }x{ (f" + {self.b}" if self.b > 0 else f" - {-1*self.b}") if self.b else "" }'

	@property
	def direction(self) -> str:
		if self.from_pos[0] == self.to_pos[0]: # y = num
			return 'vertical'
		elif self.from_pos[1] == self.to_pos[1]: # x = num
			return 'horizontal'
		elif self.from_pos == self.to_pos: # from [0, 0] to [0, 0]
			return 'point'
		else: # y = kx + b
			return 'normal'

	def __contains__(self, object):
		return self.intersects(i)

	def __str__(self):
		return f"Line[{self.as_geometry}]"

	def __repr__(self):
		return f"Line({self.from_pos}, {self.to_pos})"

	def __call__(self, x: int):
		return self.k * x + self.b

	def __len__(self):
		return int(self.length)

	def __int__(self):
		return int(self.length)

	def __float__(self):
		return float(self.length)

# line between 2 points, it works with geometry math
class Segment(Line):
	def __init__(self, from_pos: List[[int, int]], to_pos: List[[int, int]]):
		super().__init__(from_pos, to_pos)
		
		self.length = sqrt( (from_pos[0] - to_pos[0])**2 + (from_pos[1] - to_pos[1])**2 )

		self.max_x, self.min_x = max(from_pos[0], to_pos[0]), min(from_pos[0], to_pos[0])
		self.max_y, self.min_y = max(from_pos[1], to_pos[1]), min(from_pos[1], to_pos[1])

	def intersects_point(self, point: List[[int, int]]) -> bool:
		check_value(point, [list, tuple], con=len(point) == 2 and ( all(isinstance(pos, float) for pos in point) or all(isinstance(pos, int) for pos in point) ),
			exc_msg=f"Segment.intersects_point takes a list or tuple of 2 integers, not {point} {type(point)}")
		if self.k:
			return float(point[1]) == self.k * point[0] + self.b and self.min_y <= point[1] <= self.max_y and self.min_x <= point[0] <= self.max_x
		else:
			return self.min_y <= point[1] <= self.max_y and self.min_x <= point[0] <= self.max_x

	def at_pos(self, position: List[[int, int]]):
		check_value(position, [tuple, list], con=len(position) == 2 and all(isinstance(pos, int) for pos in position),
			exc_msg=f"Segment.at_pos takes a list of 2 integers, not {position} {type(position)})")
		
		new_from = (self.from_pos[0] + position[0], self.from_pos[1] + position[1])
		new_to = (self.to_pos[0] + position[0], self.to_pos[1] + position[1])
		return Segment(new_from, new_to)

	def intersects(self, object, return_positions: bool = False) -> bool:
		check_value(object, [list, tuple, Line, Ray, Segment, HitPolygon, HitCircle],
			exc_msg=f"Segment.intersects takes Line/Ray/Segment/HitPolygon/HitBox/HitCircle object or list of 2 integers, not {object} {type(object)}")
		return super().intersects(object)

	def __str__(self):
		return f"Segment[{self.from_pos} -> {self.to_pos}]: ({self.as_geometry})"

	def __repr__(self):
		return f"Segment({self.from_pos}, {self.to_pos})"

class Ray(Line):
	def __init__(self, from_pos: List[[int, int]], to_pos: List[[int, int]]):
		super().__init__(from_pos, to_pos)

		self.max_x, self.min_x = max(from_pos[0], to_pos[0]), min(from_pos[0], to_pos[0])
		self.max_y, self.min_y = max(from_pos[1], to_pos[1]), min(from_pos[1], to_pos[1])

	def intersects_point(self, point: List[[int, int]]) -> bool:
		check_value(point, [list, tuple], con=len(point) == 2 and ( all(isinstance(pos, float) for pos in point) or all(isinstance(pos, int) for pos in point) ),
			exc_msg=f"Ray.intersects_point takes a list or tuple of 2 integers, not {point} {type(point)}")

		if self.k:
			at_line = float(point[1]) == self.k * point[0] + self.b
			if self.direction == 'right-down':
				return at_line and point[1] >= self.from_pos[1] and point[0] >= self.from_pos[0]
			elif self.direction == 'right-up':
				return at_line and point[1] <= self.from_pos[1] and point[0] >= self.from_pos[0]
			elif self.direction == 'left-down':
				return at_line and point[1] >= self.from_pos[1] and point[0] <= self.from_pos[0]
			elif self.direction == 'left-up':
				return at_line and point[1] <= self.from_pos[1] and point[0] <= self.from_pos[0]
		else:
			if self.direction == 'up':
				return point[1] <= self.from_pos[1] and point[0] == self.from_pos[0]
			elif self.direction == 'down':
				return point[1] >= self.from_pos[1] and point[0] == self.from_pos[0]
			elif self.direction == 'left':
				return point[1] <= self.from_pos[1] and point[0] == self.from_pos[0]
			elif self.direction == 'right':
				return point[1] >= self.from_pos[1] and point[0] == self.from_pos[0]

		if self.direction == 'point':
			return self.from_pos == point

		return False

	def at_pos(self, position: List[[int, int]]):
		check_value(position, [tuple, list], con=len(position) == 2 and all(isinstance(pos, int) for pos in position),
			exc_msg=f"Ray.at_pos takes a list of 2 integers, not {position} {type(position)})")
		
		new_from = (self.from_pos[0] + position[0], self.from_pos[1] + position[1])
		new_to = (self.to_pos[0] + position[0], self.to_pos[1] + position[1])
		return Ray(new_from, new_to)

	def intersects(self, object, return_positions: bool = False) -> bool:
		check_value(object, [list, tuple, Line, Ray, Segment, HitPolygon, HitCircle],
			exc_msg=f"Ray.intersects takes Line/Ray/Segment/HitPolygon/HitBox/HitCircle object or list of 2 integers, not {object} {type(object)}")
		return super().intersects(object)

	@property
	def direction(self) -> str:
		if self.from_pos == self.to_pos: # from [0, 0] to [0, 0]
			return 'point'

		if self.from_pos[0] == self.to_pos[0]: # y = num
			if self.to_pos[1] > self.from_pos[1]:
				return 'down'
			elif self.to_pos[1] < self.from_pos[1]:
				return 'up'
		elif self.from_pos[1] == self.to_pos[1]: # x = num
			if self.to_pos[0] > self.from_pos[0]:
				return 'right'
			elif self.to_pos[0] < self.from_pos[0]:
				return 'left'
		else: # y = kx + b
			if to_pos[0] > from_pos[0] and to_pos[1] > from_pos[1]:
				return 'right-down'
			elif to_pos[0] > from_pos[0] and to_pos[1] < from_pos[1]:
				return 'right-up'
			elif to_pos[0] < from_pos[0] and to_pos[1] > from_pos[1]:
				return 'left-down'
			elif to_pos[0] < from_pos[0] and to_pos[1] < from_pos[1]:
				return 'left-up'

	@property
	def as_geometry(self) -> str:
		if self.direction in ['up', 'down']:
			return f'x = {self.from_pos[0]}'
		elif self.direction in ['left', 'right']:
			return f'y = {self.from_pos[1]}'
		elif self.direction == 'point':
			return f'x = {self.from_pos[0]}; y = {self.from_pos[1]}'
		else:
			return f'y = { self.k if self.k != 1 else "" }x{ (f" + {self.b}" if self.b > 0 else f" - {-1*self.b}") if self.b else "" }'

	def __str__(self):
		return f"Ray[{self.from_pos} -> {self.to_pos}, direction={self.direction}]: ({self.as_geometry})"

	def __repr__(self):
		return f"Ray({self.from_pos}, {self.to_pos})"

class AngleLine(Line):
	def __init__(self, angle: int):
		return super().__init__([0, 0], [
			int(cos( radians(angle) )),
			int(sin( radians(angle) ))
		])

class AngleRay(Line):
	def __init__(self, from_pos: List[[int, int]], angle: int):
		return super().__init__([0, 0], [
			int(cos( from_pos[0] + radians(angle) )),
			int(sin( from_pos[1] + radians(angle) ))
		])

class AngleSegment(Segment):
	def __init__(self, from_pos: List[[int, int]], angle: int, distance: int):
		return super().__init__(from_pos, [
			int(from_pos[0] + distance * cos( radians(angle) )),
			int(from_pos[1] + distance * sin( radians(angle) ))
		])


# like hitbox, but may be arbitrary figure with different vertices and different angles
class HitPolygon:
	def __init__(self, vertices: List[[ [int, int], [int, int], [int, int], [int, int] ]]):
		check_value(vertices, [tuple, list],
			con=all([ isinstance(vertice, (list, tuple)) and len(vertice) == 2 for vertice in vertices ]) and all([ all([ isinstance(pos, int) for pos in vertice ]) for vertice in vertices ]),
			exc_msg=f"'vertices' constructor arg must be list or tuple of lists or tuples of 2 integers, not {vertices} {type(vertices)}")
		self.vertices = list(vertices)

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

	def intersects(self, object, return_positions: bool = False) -> bool:
		positions = []

		if isinstance(object, (list, tuple)):
			for segment in self.segments:
				if segment.intersects_point(object):
					return object if return_positions else True

			help_ray = Ray(object, [object[0], object[1] - 1]) # ray ^

			c = 0
			for segment in self.segments:
				if segment.intersects_ray(help_ray):
					c += 1

			if return_positions:
				return object if c % 2 != 0 and c != 0 else Npne
			else:
				return c % 2 != 0 and c != 0


		elif isinstance(object, Segment):
			for segment in self.segments:
				if segment.intersects_segment(object):
					if return_positions:
						positions.append(segment.intersects_segment(object, return_position=True))
					else:
						return True

		elif isinstance(object, HitPolygon):
			for first_segment in self.segments:
				for second_segment in object.segments:
					if first_segment.intersects_segment(second_segment):
						if return_positions:
							positions.append(first_segment.intersects_segment(second_segment, return_position=True))
						else:
							return True

		elif isinstance(object, HitCircle):
			if self.intersects(object.center):
				return True

			for segment in self.segments:
				if segment.intersects_circle(object):
					if return_positions:
						positions.append(segment.intersects_circle(object, return_positions=True))
					else:
						return True

		else:
			raise ValueError(f"Segment.intersects takes Segment object, list of 2 integers or HitPolygon object, not {object} {type(object)}")

		return positions if return_positions else False

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

	@property
	def min_x(self):
		return min( x for x, y in self.vertices )
	@property
	def min_y(self):
		return min( y for x, y in self.vertices )
	@property
	def max_x(self):
		return max( x for x, y in self.vertices )
	@property
	def max_y(self):
		return max( y for x, y in self.vertices )

	@property
	def min_pos(self):
		return [self.min_y, self.min_x]
	@property
	def max_pos(self):
		return [self.max_y, self.max_x]

	@property
	def width(self):
		return abs(self.max_x - self.min_x)
	@property
	def height(self):
		return abs(self.max_y - self.min_y)

	def view(self):
		root = Tk()
		root.title("Polygon view")
		root.geometry(f"{self.width}x{self.height}")

		canvas = Canvas(root, width=self.width, height=self.height, bg='gray')
		canvas.pack()

		canvas.create_polygon(self.at_pos([0 - self.min_x, 0 - self.min_y]).as_tk_polygon, outline='', fill='red')

		root.mainloop()

	def __str__(self):
		return f"HitPolygon([{ len(self) } vertices], position={self.position}, area={self.area})"
	
	def __contains__(self, object):
		return self.intersects(object)

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

class HitCircle:
	def __init__(self, center: Union[list, tuple], radius: int):

		check_value(center, list, con=all(isinstance(xy, (int, float)) for xy in center) and len(center) == 2,
			exc_msg=f"'center' constructor arg must be list with 2 integers or floats, not {center} {type(center)}")
		self.center = center
		self.x, self.y = center

		check_value(radius, int, con=radius > 0, exc_msg=f"'radius' constructor arg must be integer >0, not {radius} {type(radius)}")
		self.radius = radius

	def intersects_point(self, point) -> bool:
		check_value(point, [tuple, list], con=len(point) == 2 and all(isinstance(xy, (int, float)) for xy in point),
			exc_msg=f"HitCircle.intersects_point takes a list of 2 integers or floats, not {point} {type(point)}")
		return len(Segment(self.center, point)) <= self.radius

	def intersects_segment(self, segment, return_positions: bool = False) -> bool:
		# (1+k)x^2 + (2kb)x + (b^2 - r^2) = 0 with segment y=kx+b and circle (a+x)^2+(b+y)^2=r^2
		# ax^2 + bx + c = 0
		D = (2*segment.k*segment.b)**2 - 4 * (1+segment.k) * (segment.b**2 - self.radius**2)
		if return_positions:
			if D == 0:
				x = -(2*segment.k*segment.b) / 2 * (1+segment.k)
				return [x, segment(x)]
			elif D > 0:
				x1 = ( -(2*segment.k*segment.b) + sqrt(D) ) / 2 * (1+segment.k)
				x2 = ( -(2*segment.k*segment.b) - sqrt(D) ) / 2 * (1+segment.k)
				return [x1, segment(x1)], [x2, segment(x2)]
			return []
		else:
			return D >= 0

	def intersects_polygon(self, polygon, return_positions: bool = False) -> bool:
		positions = []
		for segment in polygon.segments:
			if self.intersects_segment(segment):
				if return_positions:
					for pos in self.intersects_segment(segment, return_positions=True):
						positions.append(pos)
				else:
					return True

		if return_positions:
			return positions
		else:
			return False

	def intersects_circle(self, circle) -> bool:
		return len(Segment(self.center, circle.center)) <= self.radius + circle.radius

	def intersects(self, object, return_count: bool = False) -> bool:
		count = 0
		if isinstance(object, (list, tuple)):
			count = self.intersects_point(object)

		elif isinstance(object, Segment):
			count = len(self.intersects_segment(object, True))

		elif isinstance(object, HitPolygon):
			for segment in object.segments:
				count += len(self.intersects_segment(segment, True))

		else:
			raise ValueError(f"HitCircle.intersects takes Segment object, list of 2 integers or HitPolygon object, not {object} {type(object)}")

		return bool(count) if not return_count else count

	@property
	def area(self):
		return pi * self.radius**2
	@property
	def length(self):
		return pi * self.radius * 2

	def __str__(self):
		return f"HitCircle[{self.center}, radius={self.radius} area={self.area} length={self.length}] ((x + {self.x})**2 + (y + {self.y})**2 = {self.radius}**2)"

	def __repr__(self):
		return f"HitCircle({self.center}, {self.radius})"