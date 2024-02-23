from math import *
from .types import check_value

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
        check_value(positions, [list, tuple],
exc_msg=f"'positions' constructor kwarg must be list or tuple of integer positions, like [ (0, 0), (0, 0) ] or one position, like [0, 0], not {positions} {type(positions)}"
            )
        if len(positions) == 2:
            if isinstance(positions[0], int) and isinstance(positions[1], int):
                self.positions = [positions]
            else:
                self.positions = positions
        else:
            self.positions = positions


    def then(self, positions: list):
        i = -1
        while isinstance(self.positions[i][0], str): # to find last position instead of string command
            i -= 1
        last_x, last_y = self.positions[i]

        if positions:
            if isinstance(positions, list):
                if len(positions[0]) > 0:
                    if isinstance(positions[0], str):
                        self.positions.append( positions )
                        return self

                    elif isinstance(positions[0], list):
                        if len(positions[0]) == 2:
                            if isinstance(positions[0][0], int) and isinstance(positions[0][1], int):
                                self.positions.append( positions )
                                return self

                        if isinstance(positions[0], str):
                            self.positions.append( positions )
                            return self

                    for pos in positions:
                        if isinstance(pos[0], str):
                            self.positions.append( pos )
                        else:
                            self.positions.append( (last_x + pos[0], last_y + pos[1]) )
            else:
                raise ValueError(
f"'positions' constructor kwarg must be list or tuple of integer positions, like [ (0, 0), (0, 0) ] or one position, like [0, 0], not {positions} {type(positions)}"
                    )

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