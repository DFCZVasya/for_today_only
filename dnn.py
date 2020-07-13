import jetson.inference
import jetson.utils
import comp
import time
from threading import Thread

net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
camera = jetson.utils.gstCamera(640, 480, "/dev/video1")
display = jetson.utils.glDisplay()
com = comp.Com(STMPath = "/dev/ttyUSB0", portSpeed = 115200)

REDGE = 1664
LEDGE = 0
UEDGE = 400
DEDGE = 120

commands = {
	'left': 101,
	'stopX': 119,
	'right': 113,
	'up': 117,
	'stopY': 106,
	'down': 110,
}
speed = [50, 51, 52, 53, 54, 55, 56, 57]
delay = [0.015, 0.011, 0.008, 0.006, 0.005, 0.004, 0.003, 0.002]
com.writeCmd(speed[7])

def go(flags, direction):
	if not flags[direction]:
		com.writeCmd(commands[direction])
		for i in flags:
			flags[i] = False		
		flags[direction] = True

class Aiming(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.objects = []
		self.flagsX = {
			'left': False,
			'stopX': True,
			'right': False,
		}
		self.flagsY = {
			'up': False,
			'stopY': True,
			'down': False,
		}
		self.ticksX = 832
		self.tickX = 0
		self.ticksY = 170
		self.tickY = 0
		self.s = 7
		ticker = Thread(target = self.tick, daemon = True)
		ticker.start()
		self.searches = 0
		self.steps = [True, False, False, False]
		time.sleep(3)
	def run(self):
		t = time.time()
		while True:
			x, y = self.get_XY(self.objects)
			if (x != 0 or y != 0) and self.ticksX < 1700 and self.ticksX > 0 and self.ticksY < 750 and self.ticksY > 0:
				t = time.time()
				new_s = int(((240 - x)**2 + (320 - y)**2)**(0.5)//57)
				if self.s != new_s:
					self.s = new_s			
					com.writeCmd(speed[self.s])
				if x > 0 and x < 280:
					go(self.flagsX,'left')
					self.tickX = -1
				elif x > 360:
					go(self.flagsX,'right')
					self.tickX = 1
				else:
					go(self.flagsX,'stopX')
					self.tickX = 0
				if y > 0 and y < 190:
					go(self.flagsY,'up')
					self.tickY = 1
				elif y > 290:
					go(self.flagsY,'down')
					self.tickY = -1
				else:
					go(self.flagsY,'stopY')
					self.tickY = 0
				print(self.ticksX, self.ticksY, self.tickX, self.tickY, self.s)
			else:
				go(self.flagsY,'stopY')
				self.tickY = 0
				go(self.flagsX,'stopX')
				self.tickX = 0
				if time.time()-t > 1.5:
					self.find()
	def tick(self):
		tme = 0
		while True:
			t = time.time()
			while tme < 0.01:
				tme = time.time() - t	
			tme /= delay[self.s]
			self.ticksX += self.tickX * tme
			self.ticksY += self.tickY * tme
			tme = 0	

	def correctY(self):
		com.writeCmd(speed[7])
		go(self.flagsY,'stopY')
		go(self.flagsY,'down')
		time.sleep(2)
		go(self.flagsY,'stopY')
		self.ticksY = 0

	def find(self):
		go(self.flagsY,'stopY')
		go(self.flagsX,'stopX')
		x, y = self.get_XY(self.objects)
		
		self.s = 6
		com.writeCmd(speed[self.s])
		go_down = False
		down_checked = False
		go_up = False
		up_checked = False
		found = False
		#self.searches = 0
		t = time.time()
		while not found:
			if self.steps[0]:
				go(self.flagsX, 'right')
				self.tickX = 1
				if self.ticksX >= REDGE:
					go(self.flagsX,'stopX')
					self.tickX = 0
					self.steps[0] = False
					self.steps[1] = True					
			if self.steps[1]:
				if self.searches >= 10:
					self.correctY()
					self.searches = 0
				if not down_checked and self.ticksY > DEDGE:
					go(self.flagsY, 'down')
					self.tickY = -1
					go_down = True
					down_checked = True
				elif not down_checked and self.ticksY <= DEDGE:
					go(self.flagsY, 'up')
					self.tickY = 1
					go_down = False
					down_checked = True
				if go_down and self.ticksY < DEDGE:
					go(self.flagsY,'stopY')
					self.tickY = 0
					self.steps[1] = False
					self.steps[2] = True
					down_checked = False
				elif not go_down and self.ticksY > DEDGE:
					go(self.flagsY,'stopY')
					self.tickY = 0
					self.steps[1] = False
					self.steps[2] = True
					down_checked = False
			if self.steps[2]:
				go(self.flagsX, 'left')
				self.tickX = -1
				if self.ticksX <= LEDGE:
					go(self.flagsX,'stopX')
					self.tickX = 0
					self.steps[2] = False
					self.steps[3] = True	
			if self.steps[3]:
				go(self.flagsY, 'up')
				self.tickY = 1
				if not up_checked and self.ticksY > UEDGE:
					go(self.flagsY, 'down')
					self.tickY = -1
					go_down = True
					up_checked = True
				elif not up_checked and self.ticksY <= UEDGE:
					go(self.flagsY, 'up')
					self.tickY = 1
					go_down = False
					up_checked = True
				if go_down and self.ticksY < UEDGE:
					go(self.flagsY,'stopY')
					self.tickY = 0
					up_checked = False
					self.steps[3] = False
					self.steps[0] = True
					self.searches += 1
				elif not go_down and self.ticksY > UEDGE:
					go(self.flagsY,'stopY')
					self.tickY = 0
					up_checked = False
					self.steps[3] = False
					self.steps[0] = True
					self.searches += 1

			x, y = self.get_XY(self.objects)
			if x == 0 and y == 0:
				t = time.time()
			if time.time() - t > 0.17:
				found = True
			print(self.steps, self.ticksX, self.ticksY)
			
	def get_XY(self, objects):
		areas = []
		x, y = 0, 0
		for i in objects:
			if i.ClassID == 1:
				areas.append(i.Area)
		if len(areas)>0:
			person = objects[areas.index(max(areas))]
			x = person.Center[0]
			y = person.Top + person.Width/4
		return (x, y)

aim = Aiming()
aim.start()
while display.IsOpen():
	img, width, height = camera.CaptureRGBA()
	detections = net.Detect(img, width, height) #detections - list of objects
	"""
	for object in detection list
	object.ClassID - class id (0 - face)
 	object.Center - tupple(x,y) max x - 640, max y - 480 // 220-260, 300-340
	object.Area - square of box
	"""
	aim.objects = detections
	display.RenderOnce(img, width, height)
	display.SetTitle("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
