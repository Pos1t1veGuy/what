from what import *

from PIL import Image


def mainloop(area, fps):
	global cursor
	print(cursor.hp)


cursor = Cursor(hp=10, radius=15, image='assets/cursor.png', on_death=lambda: print('cursor in dead'), transparent_color="white")

m1 = Movement(quadratic_y(600, a=1500, step=5)[:int((600-200)/5)]).then(
	linear_x(300, step=5)).then(
	linear_x(600, step=5, k=-1)).mirror_center()
m2 = Movement(quadratic_y(600, a=1500, step=5)[:int((600-200)/5)]).then(
	linear_x(300, step=5) ).then(
	linear_x(600, step=5, k=-1) )

tl = TimeLine([
	Window(m1, [50, 50], bg_color="white", cycle=True, hitbox=[(0,0), (50,50)], on_mouse_in_hitbox=lambda win: cursor.set_hp("-1")),
	Window(m2, [50, 50], bg_color="green", repeat=2),
	][::-1], bg_alpha=0.4, moments={5: lambda fps, cursor: cursor.set_hp("-5"), 10: lambda fps, cursor: cursor.set_hp("+15")}, on_start=lambda fps, cursor: print('started'))

area = Area([tl], cursor=cursor, minimize_windows=False, bg_func=mainloop)
area.run()