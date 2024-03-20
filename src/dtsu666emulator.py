#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
import datetime
import logging

from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.constants import Endian

from pymodbus.server import StartTcpServer, StartUdpServer

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from threading import Thread

from pymodbus import pymodbus_apply_logging_config

wordorder = Endian.BIG
byteorder = Endian.BIG

header = [207, 701, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 1, 10, 0, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 0, 0, 11, 3, 4]

#Not all mappings are known, only the relevant ones have their correct address
#All other ones after 0x1000 added to not disturb
Registermapping = {
	"Volts_AB":	{"addr":0x1836, 'scale': .1},
	"Volts_BC":	{"addr":0x1838, 'scale': .1},
	"Volts_CA":	{"addr":0x183A, 'scale': .1},
	"Volts_L1":	{"addr":0x83E, 'scale': .1},
	"Volts_L2":	{"addr":0x840, 'scale': .1},
	"Volts_L3":	{"addr":0x842, 'scale': .1},
	"Current_L1":	{"addr":0x836, 'scale': .001},
	"Current_L2":	{"addr":0x838, 'scale': .001},
	"Current_L3":	{"addr":0x83A, 'scale': .001},
	"Active_Power_L1":	{"addr":0x850, 'scale': .1},
	"Active_Power_L2":	{"addr":0x852, 'scale': .1},
	"Active_Power_L3":	{"addr":0x854, 'scale': .1},
	"Reactive_Power_L1":	{"addr":0x184E, 'scale': .1},
	"Reactive_Power_L2":	{"addr":0x1850, 'scale': .1},
	"Reactive_Power_L3":	{"addr":0x1852, 'scale': .1},
	"Power_Factor_L1":	{"addr":0x1854, 'scale': .001},
	"Power_Factor_L2":	{"addr":0x1856, 'scale': .001},
	"Power_Factor_L3":	{"addr":0x1858, 'scale': .001},
	"Total_System_Active_Power":	{"addr":0x84E, 'scale': .1},
	"Total_System_Reactive_Power":	{"addr":0x856, 'scale': .1},
	"Total_System_Power_Factor":	{"addr":0x866, 'scale': .001},
	"Frequency":					{"addr":0x84C, 'scale': .01},
	"DmPt":							{"addr":0x1862, 'scale': .1},
	"Total_import_kwh":	{"addr":0x876, 'scale': 1},
	"Total_export_kwh":	{"addr":0x87E, 'scale': 1},
	"Total_Q1_kvarh":	{"addr":0x1868, 'scale': 1000},
	"Total_Q2_kvarh":	{"addr":0x186A, 'scale': 1000},
	"Total_Q3_kvarh":	{"addr":0x186C, 'scale': 1000},
	"Total_Q4_kvarh":	{"addr":0x186E, 'scale': 1000},
}

class dtsu666Emulator:
	def __init__(self, SlaveID=11):
		
		self.threads = {}

		# ----------------------------------------------------------------------- #
		# initialize the server information
		i1 = ModbusDeviceIdentification()
		i1.VendorName = 'Pymodbus'
		i1.ProductCode = 'PM'
		i1.VendorUrl = 'http://github.com/riptideio/pymodbus/'
		i1.ProductName = 'Pymodbus Server'
		i1.ModelName = 'Pymodbus Server'

		self.block = ModbusSequentialDataBlock(0, [0]*0x4052)
		# Add header:
		self._setval(0, header)
		self._setval(0x7d1, [3]) #When detecting the meter a "3" is expected here

		self.store   = ModbusSlaveContext(hr=self.block)
		self.context = ModbusServerContext(slaves={SlaveID: self.store}, single=False)
		#pymodbus_apply_logging_config("DEBUG")

	#------------------------------------------------
	def _setval(self, addr, data):
		self.block.setValues((addr+1), data)	# why +1 ?! ..ugly

	#------------------------------------------------
	def _startserver(self):
		srv = StartUdpServer(context=self.context, address=('0.0.0.0', 5020))

		logging.info('Modbus server started')

	#------------------------------------------------
	def _datejob(self):
		while True:
			self.set_date()
			time.sleep(1)

	#------------------------------------------------
	def startserver(self):
		self.threads['srv'] = Thread(target=self._startserver)
		self.threads['srv'].start()

		self.threads['date'] = Thread(target=self._datejob)
		self.threads['date'].start()

	#------------------------------------------------
	def set_date(self):
		now = datetime.datetime.now()
		builder = BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)
		builder.add_16bit_int(now.second)
		builder.add_16bit_int(now.minute)
		builder.add_16bit_int(now.hour)
		builder.add_16bit_int(now.day)
		builder.add_16bit_int(now.month)
		builder.add_16bit_int(now.year)

		self._setval(0x002f, builder.to_registers())

	#------------------------------------------------
	def update(self, data):
		for k,v in data.items():
			reg = Registermapping[k]["addr"]

			#d = v / Registermapping[k]["scale"]
			#Scaling not needed
			d = v
			builder = BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)
			builder.add_32bit_float(d)

			self._setval(reg, builder.to_registers())

# ==========================================================================================
# ==========================================================================================
if __name__ == "__main__":
	em1 = dtsu666Emulator()

	em1.startserver()
	builder = BinaryPayloadBuilder(byteorder=byteorder, wordorder=wordorder)

	Testdata = {'Volts_AB': 403.6, 'Volts_BC': 408.0, 'Volts_CA': 404.5, 'Volts_L1': 231.0, 'Volts_L2': 235.1, 'Volts_L3': 236.1, 'Current_L1': 0.339, 'Current_L2': 0.36, 'Current_L3': 0.352, 'Active_Power_L1': 2.8, 'Active_Power_L2': 11.8, 'Active_Power_L3': 8.5, 'Reactive_Power_L1': -76.7, 'Reactive_Power_L2': -80.0, 'Reactive_Power_L3': -79.7, 'Power_Factor_L1': 0.036, 'Power_Factor_L2': 0.14, 'Power_Factor_L3': 0.102, 'Total_System_Active_Power': 23.2, 'Total_System_Reactive_Power': -236.5, 'Total_System_Power_Factor': 0.094,}
	reg = 2102
	num = 1

	while True:
		logging.info("updating the context")
		builder.add_32bit_float(num)
		print("Setting %x to %d" % (reg, num))
		em1._setval(reg, builder.to_registers())
		builder.reset()
		#em1.update(Testdata)
		input("Press the Enter key to continue: ")
		reg = reg + 2
		num = num + 1

	print("bla")


