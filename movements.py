from math import *

def linear_x(distance: int, k: int = 1, b: int = 0, step: int = 1, start_at: list = [0, 0]) -> list: # y = kx + b
    return [ (start_at[0] + x, start_at[1] + int(k*x + b)) for x in range(0, distance, step) ]

def linear_y(distance: int, k: int = 1, b: int = 0, step: int = 1, start_at: list = [0, 0]) -> list: # y = kx + b
    return [ (start_at[0] + int(k*x + b), start_at[1] + x) for x in range(0, distance, step) ]

def quadratic_x(distance: int, a: int = 1, b: int = 0, c: int = 1, step: int = 1, start_at: list = [0, 0]) -> list:
    a = a / distance**2
    return [ (start_at[0] + x, start_at[1] + int(a * (x - distance/2)**2 + c)) for x in range(0, distance, step) ]

def quadratic_y(distance: int, a: int = 1, b: int = 0, c: int = 1, step: int = 1, start_at: list = [0, 0]) -> list:
    a = a / distance**2
    return [ (start_at[0] + int(a * (x - distance/2)**2 + c), start_at[1] + x) for x in range(0, distance, step) ]


class Movement:
    def __init__(self, positions: list = []):
        self.positions = positions

    def then(self, positions: list):
        i = -1
        while isinstance(self.positions[i][0], str): # to find last position instead of string command
            i -= 1
        last_x, last_y = self.positions[i]
        new_positions = [ (last_x + x, last_y + y) for x, y in positions ]
        self.positions = [ *self.positions, *new_positions ]
        return self

    def do_then(self, command: str):
        self.positions.append(command)
        return self

    def mirror_x(self, width: int):
        self.positions = [ (width - x, y) for x, y in self.positions ]
        return self

    def mirror_y(self, height: int):
        self.positions = [ (x, height - y) for x, y in self.positions ]
        return self

    def mirror_xy(self, width: int, height: int):
        self.positions = [ (width - x, height - y) for x, y in self.positions ]
        return self

    def mirror_center(self):
        self.positions = [ (y, x) for x, y in self.positions ]
        return self

    def __list__(self):
        return self.positions
    def __getitem__(self, i):
        return self.positions[i]
    def __len__(self):
        return len(self.positions)
    def __str__(self):
        return str(self.positions)
    def __repr__(self):
        if len(self.positions) > 4:
            return f'Movement path [{self.positions[0]}, {self.positions[1]}, ... {self.positions[-1]}]'
        else:
            return f'Movement path {self.positions}'