# dtsu666-Emulator

This is a python library to emulate a CHINT DTSU666 smartmeter. The project has been modified from its original state in order to

 - Use ModbusUDP instead of ModbusRTU
 - Support the latest (as of 2024) pymodbus 3.0.0 on the BeagleBone Debian distribution
 - Provide the registers as expected by the Huawei Sun2000 inverter
 - Use SMA-EM via MQTT as backend

## Content:
`dtsu666emulator.py` the emulator.  
It's a modbus server, the client ( the Hyundai inverter) can pull the data as needed.

`mqtt2smemulator.py` subscribes the available MQTT topics and converts the data for the dtsu666 emulator.  

## Background:
I have a Hyuandai Sun2000 photovoltaik inverter, which expects an DTSU666 smartmeter to be installed in the main fuse box.
For the inverter this is necessay, to know when to charge the battery, show correct energy flow status, and so on...

However, I already have this information available from an SMA energy meter (see project: [SMA-EM](https://github.com/datenschuft/SMA-EM)).
So for me it would be redundant to have two smartmeters installed. Additionally I wanted to avoid the RS485 cabeling between smart meter and inverter.
To also avoid RS485 cable between inverter and BeagleBone I used a Serial-to-Ethernet modbus converter that uses the already existing Ethernet connection

This project takes the provided info from MQTT, modifies it as needed and emulates the dtsu666 smartmeter to be used by the growatt inverter.


## Current status:
It's working.  
I use this code on a BeagleBone Green with debian 12

Now I see on the display of the inverter arrow symbols between the grid and the inverter,
Error 401 ( no smartmeter conected ) disapered and the inverter is now correctly calculating if the power goes to the grid or to the local load.


## Dependency:
 - pymodbus 3.0.0
