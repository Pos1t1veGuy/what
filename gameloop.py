import keyboard as kb

from tkinter import Tk, Label, Toplevel
from threading import Thread as th
from traceback import print_exc


class Area: # main window
	def __init__(self, timelines: list, bg_always_on_top: bool = False, minimize_windows: bool = True):
		self.timelines = timelines

		if minimize_windows:
			os.system("explorer shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}") # minimizes every window like WIN+D

		self.root = Tk()
		self.root.title("WHAT root")

		self.screen_width = self.root.winfo_screenwidth()
		self.screen_height = self.root.winfo_screenheight()

		self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

		self.root.overrideredirect(1)
		self.root.configure(bg="black")

		self.alpha = 0
		self.alive_time = 0
		self.dead = False
		self.bg_always_on_top = bg_always_on_top

		if bg_always_on_top:
			self.root.wm_attributes("-topmost", 1)

		for timeline in self.timelines:
			for obj in timeline.objects:
				obj.set_window( Toplevel(self.root) ) # creates child window for every Window object

		keyboard_thread = th(target=self.check_keyboard, daemon=True)
		keyboard_thread.start()

	def run(self, fps: int = 90): # starts main loop
		self.update(fps)
		self.root.mainloop()

	def update(self, fps: int): # will be dead when every timeline is dead
		for timeline in self.timelines:
			try:
				is_dead = timeline.update(fps)
				if not is_dead:
					if self.alpha != timeline.bg_alpha:
						self.root.attributes('-alpha', float(timeline.bg_alpha))
						self.alpha = timeline.bg_alpha
					break
			except Exception as e:
				self.dead = True
				self.root.attributes('-alpha', 0.0)
				print_exc()
				return
		else:
			self.root.destroy()
			print("WHAT? END?")
		
		if not self.dead:
			self.alive_time += 1/fps
			self.root.after(int(1/fps*1000), self.update, fps)
		else:
			self.root.destroy()

	def check_keyboard(self): # logs keystrokes
	    while 1:
	        key = kb.read_event()
	        if key.event_type == kb.KEY_DOWN:
	            if key.name == 'esc':
	            	self.dead = True
	            	return

class TimeLine: # it is a scene where contain child windows, you may use several scenes in one Area in sequience, one after another
	def __init__(self, objects: list, bg_alpha: float = 1, wait_time: int = 0, alive_time: int = -1):
		# objects: list of Window objects
		# wait_time: delay time before start in seconds
		self.objects = objects
		self.bg_alpha = bg_alpha
		self.alive_time = 0
		self.wait_time = wait_time
		self.max_alive_time = alive_time

	def update(self, fps: int): # returns true when every object is dead
		self.alive_time += 1/fps
		if self.alive_time >= self.max_alive_time and self.max_alive_time != -1:
			return True

		if self.alive_time >= self.wait_time:
			results = []
			for obj in self.objects:
				is_dead = obj.update( int(self.alive_time), fps )
				results.append(not is_dead)

			return all(results)
		else:
			return False