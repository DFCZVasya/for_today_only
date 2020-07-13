import serial
import time
from threading import Thread
import struct

class Com:
	portSpeed = 0
	STMCom = 0
	STMPath = 0
	thread = 0
	packByte = struct.Struct('>B').pack
	def __init__(self, STMPath, portSpeed):
		self.portSpeed = portSpeed
		self.STMPath = STMPath
		self.STMCom = serial.Serial(self.STMPath, self.portSpeed, timeout = 1)
		if self.STMCom.is_open:
			print("Serial port is opened on {0} with {1} baud".format(self.STMPath, self.portSpeed))
	def writeCmd(self, cmd):
		self.STMCom.write(self.packByte(cmd))
		#print(cmd)
