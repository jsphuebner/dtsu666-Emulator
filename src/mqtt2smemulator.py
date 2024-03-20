#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pprint import PrettyPrinter

pp = PrettyPrinter(indent=4)

import logging
import logging.handlers as Handlers

#log = logging.getLogger("pymodbus.server")
#log.setLevel(logging.DEBUG)

log = logging.getLogger()
log.setLevel(logging.INFO)

from dtsu666emulator import dtsu666Emulator
import paho.mqtt.client as mqtt
import json
import math

MQTT_Settings = {
	"Server":	"localhost",
	"Port":     	1883,
	"AMS_Topic": "SMA-EM/status/3007888642"
	}
	
	
	
#--------------------------------------------------
em1 = dtsu666Emulator()

em1.startserver()
logging.info('smartmeter started...')
data = { "U1": 230, "U2": 230, "U3": 230, "PF": 1, "frequency": 50, "pconsume": 0, "tPI": 0, "tPO": 0 }


#============================================================================

# The callback for when the client receives a CONNACK response from the server.
def mqtt_on_connect(client, userdata, flags, rc):
	logging.info(f"MQTT connected with result code {rc}")

	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	client.subscribe(MQTT_Settings['AMS_Topic']+"/#")
	#em1.update({"SWVer": 100, "UCode": 1, "Phases": 1, "Comm": 3, "Addr": 4, "Parity": 5})


# The callback for when a PUBLISH message is received from the server.
def mqtt_on_message(client, userdata, msg):
#	print(msg.topic)
	global data

	if msg.topic == MQTT_Settings['AMS_Topic']+"/u1":
		data['U1'] = float(msg.payload)
	elif msg.topic == MQTT_Settings['AMS_Topic']+"/u2":
		data['U2'] = float(msg.payload)
	elif msg.topic == MQTT_Settings['AMS_Topic']+"/u3":
		data['U3'] = float(msg.payload)
	elif msg.topic == MQTT_Settings['AMS_Topic']+"/cosphi":
		data['PF'] = float(msg.payload)
	elif msg.topic == MQTT_Settings['AMS_Topic']+"/frequency":
		data['frequency'] = float(msg.payload)
	elif msg.topic == MQTT_Settings['AMS_Topic']+"/pconsume":
		data['pconsume'] = float(msg.payload)
	elif msg.topic == MQTT_Settings['AMS_Topic']+"/psupply":
		d = data
		d['P'] = data['pconsume'] - float(msg.payload)
		d['PO'] = 0

		P = d['P'] - d['PO']
		S = P / d["PF"]
		Q = math.sqrt(S**2 - P**2)

		U1 = (d['U1'] + d['U2'] + d['U3'])/3

		w3 = 1.732050808 # sqrt(3)
		Vab = U1*w3
		
		I = P / (U1 * d["PF"] * 3)

		Inverterdata = {
			# Cosinussatz: sqrt(a² + b² -2*a*b*cos(120°) )
			# -2*cos(120°) = 1

#			'Volts_AB':		math.sqrt( U1**2 + U2**2 + U1*U2),

			'Volts_AB':		Vab,
			'Volts_BC':		Vab,
			'Volts_CA':		Vab,

			'Volts_L1':		d['U1'],
			'Volts_L2':		d['U2'],
			'Volts_L3':		d['U3'],
#			'Current_L1':		d['I1'],
#			'Current_L2':		d['I2'],
#			'Current_L3':		d['I3'],

			'Current_L1':		I,
			'Current_L2':		I,
			'Current_L3':		I,
			
			'Active_Power_L1':	P/3,
			'Active_Power_L2':	P/3,
			'Active_Power_L3':	P/3,

			'Total_System_Power_Factor':	d['PF'],
			'Power_Factor_L1':	d['PF'],	 # don't have the data aund don't care
			'Power_Factor_L2':	d['PF'],
			'Power_Factor_L3':	d['PF'],

			'Reactive_Power_L1':	Q/3,
			'Reactive_Power_L2':	Q/3,
			'Reactive_Power_L3':	Q/3,

			'Total_System_Active_Power':	P,
	#		'Total_System_Apparent_Power':	Pn,
			'Total_System_Reactive_Power':	Q,
			'DmPt': P,

			"Frequency":	data['frequency'],
			}


		logging.info("..update power..")
		#logging.info(pp.pformat(Inverterdata))
		em1.update(Inverterdata)


	elif msg.topic == MQTT_Settings['AMS_Topic']+"/psupplycounter":
		data['tPO'] = float(msg.payload)
	elif msg.topic == MQTT_Settings['AMS_Topic']+"/pconsumecounter":
		data['tPI'] = float(msg.payload)

		Inverterdata = {
			'Total_import_kwh':	data['tPI'],
			'Total_export_kwh':	data['tPO'],
			}

		logging.info("..update energy..")
		em1.update(Inverterdata)


# ========================================================================================================================
mqttclient=mqtt.Client()
mqttclient.on_connect = mqtt_on_connect
mqttclient.on_message = mqtt_on_message
mqttclient.connect(MQTT_Settings['Server'], MQTT_Settings['Port'], 60)

# Blocking call that processes network traffic, dispatches callbacks and handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a manual interface.
mqttclient.loop_forever()



