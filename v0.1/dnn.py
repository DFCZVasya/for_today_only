import jetson.inference
import jetson.utils
import comp
import time
from threading import Thread

net = jetson.inference.detectNet("facenet-120", threshold=0.5)
camera = jetson.utils.gstCamera(640, 480, "/dev/video1")
display = jetson.utils.glDisplay()
com = comp.Com(STMPath = "/dev/ttyUSB1", portSpeed = 115200)

commands = {
	'left': 113,
	'stopX': 119,
	'right': 101,
	'up': 117,
	'stopY': 106,
	'down': 110,
}
speed = [50, 51, 52, 53, 54, 55, 56, 57]
delay = [0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01]
com.writeCmd(speed[7])

def go(flags, direction):
	if not flags[direction]:
		com.writeCmd(commands[direction])
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
			'stopX': False,
			'right': False,
		}
		self.flagsY = {
			'up': False,
			'stopY': False,
			'down': False,
		}
	def run(self):
		s = 7
		while True:
			x, y = self.get_XY(self.objects)
			new_s = int(((240 - x)**2 + (320 - y)**2)**(0.5)//57)
			if s != new_s:
				s = new_s			
				com.writeCmd(speed[s])
			time.sleep(delay[s])
			if x > 0 and x < 280:
				go(self.flagsX,'right')
			elif x > 360:
				go(self.flagsX,'left')
			else:
				go(self.flagsX,'stopX')
			if y > 0 and y < 190:
				go(self.flagsY,'up')
			elif y > 290:
				go(self.flagsY,'down')
			else:
				go(self.flagsY,'stopY')

	def get_XY(self, objects):
		areas = []
		x, y = 0, 0
		for i in objects:
			areas.append(i.Area)
		if len(areas)>0:
			x, y = objects[areas.index(max(areas))].Center
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
