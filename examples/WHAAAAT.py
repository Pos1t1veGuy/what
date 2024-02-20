from what import *

m1 = Movement(quadratic_y(600, a=1500, step=5)[:int((600-200)/5)]).then(
	linear_x(300, step=5)).then(
	linear_x(600, step=5, k=-1)).mirror_center()
m2 = Movement(quadratic_y(600, a=1500, step=5)[:int((600-200)/5)]).then(
	linear_x(300, step=5) ).then(
	linear_x(600, step=5, k=-1) )

tl = TimeLine([
	Window(m1, [50, 50], bg_color="white", spawn_time=2, cycle=True),
	Window(m2, [50, 50], bg_color="green", cycle=True, rhythm=0.3, on_rhythm=Command.window.impulse(10, speed=10)),
	], bg_alpha=0.4)

area = Area([tl], cursor_circle_radius=10)
area.run()