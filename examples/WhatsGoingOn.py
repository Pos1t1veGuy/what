from what import *

from PIL import Image


def mainloop(area):
	global cursor
	print(cursor.position)

def resize_to_default(win):
	if win.media.size[0] < 70 and win.media.size[1] < 70:
		win.media.resize('+10', '+10')

cursor = Cursor(hp=10, hitbox=HitBox([0,0], [25,25]), image='assets/cursor.png', on_death=lambda cur: print('cursor in dead'), transparent_color="white", alpha=0.7)
media2 = Media.Image('assets/cat.jpg', size=[1800,900])
area = Area(cursor=cursor, minimize_windows=False, alpha=0.0, cursor_circle_radius=0, media=media2)

m1 = Movement(quadratic_y(600, a=1500, step=5)[:int((600-200)/5)]).then(
	linear_x(300, step=5)).then(
	linear_x(600, step=5, k=-1)).mirror_center()
m2 = Movement(quadratic_y(600, a=1500, step=5)[:int((600-200)/5)]).then(
	linear_x(300, step=5) ).then(
	linear_x(600, step=5, k=-1) )
m3 = Movement([150,150]).then(
	linear_x(100, step=2) ).then(
	linear_x(600, step=2) ).then(
	linear_y(10, step=2) )
m4 = Movement([500,0]).then(
	linear_x(100, step=5) ).then(
	linear_y(300, step=10, k=-1) ).then(
	linear_y(300, step=5) ).then(
	linear_y(300, step=5, k=5) )

media1 = Media.Image('assets/cat.jpg', size=[70,70], resize_max=[200,200], resize_min=[20,20])
media3 = Media.Video('assets/bruh.mp4', size=[100,100], duration=2)
media5 = Media.Image('assets/cool_bro.png', size=[200,200])
media41 = Media.Image('assets/cool_bro.png', size=[100,100])
media42 = Media.Image('assets/cat.jpg', size=[100,100])

area.add_timeline(TimeLine([
		Window(m1, [70, 70], bg_color="black", transparent_color='black', media=media1, cycle=True, hitbox=HitBox([0,0], [70,70]), on_mouse_in_hitbox=Command.media.resize("-10", "-10"), on_mouse_not_in_hitbox=resize_to_default),
		Window(m2, [200, 200], bg_color='black', transparent_color='black', media=media5, cycle=True, hitbox=HitBox([0,0], [200,200]), on_mouse_in_hitbox=Command.media.rotate(10), on_mouse_not_in_hitbox_click=lambda win: print('loss! =)')),
		Window(m4, [100,100], bg_color="blue", media=media41, cycle=True, hitbox=HitBox([0,0], [100,100]), on_mouse_in_hitbox=Command.media.set(media3), on_mouse_not_in_hitbox=Command.media.set(media41)),
		Window(m3, [150,150], bg_color="black", transparent_color='black', cycle=True, media=media42, hitbox=HitBox([0,0], [150,150]), on_mouse_in_hitbox=Command.media.set(media41), on_mouse_not_in_hitbox=Command.media.set(media42)),
	][::-1], bg_alpha=0.8, bg_realpha_speed=2,
	moments={2: lambda timeline: cursor.set_hp("-5"), 4: lambda timeline: cursor.set_hp("+15")}, on_death=lambda timeline: print('dead'))
)

area.moments = {2: lambda area: print('moment')}
area.on_tl_start = lambda area: print('started')
area.run(fps=60)

'''
Нужно создать функционал создания звуков по ивентам и фоновой музыки
Сделать анимацию получения урона
Ограничитель для мыши, поле где двигаться можно и нельзя
Чувство ритма на заднем фоне
Исправить баг с поздним запуском потока считывания клавиатуры
Сделать всплывающую надпись
Поворот хитбокса
Результаты
Включение и отключение ритма в окнеы

Реализовать обекты:
луч
сфера
синий луч
желтый луч
кнопка
текст

Реализовать геометрицеские функции:
прямая по углу
парабола по углу
гипербола
гипербола по углу
синусоуда
синусоида по углу
Также жобавить функциям динамическую скорость


'''

