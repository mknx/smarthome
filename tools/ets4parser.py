#!/usr&bin/env python
#
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.   http://smarthome.sourceforge.net/
#
#  SmartHome.py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHome.py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
##########################################################################

import os
import sys
import xml.etree.ElementTree as ET

# Ausgabedatei
OUTFILE = '/usr/local/smarthome/etc/smarthome.conf'

# erster Knoten ist meist das Projekt, damit das nicht mit abgebildet wird
# folgende Option auf 1 setzen
IGNORE_TOP_LEVEL = 1

NS_URL = '{http://knx.org/xml/project/10}'
FIND_BUILDINGS = NS_URL + 'Buildings'
FIND_BUILDINGPART = NS_URL + 'BuildingPart'
FIND_DEVICEREF = NS_URL + 'DeviceInstanceRef'
FIND_DEVICE = NS_URL + 'DeviceInstance'
FIND_COMREF = NS_URL + 'ComObjectInstanceRef'
FIND_CONNECTOR = NS_URL + 'Connectors'
FIND_SEND = NS_URL + 'Send'
FIND_RECEIVE = NS_URL + 'Receive'
FIND_GA = NS_URL + 'GroupAddress'

def processBuildingPart(root, part, depth, f):
	print "processing " + part.tag + " " + part.attrib['Name'] + " (" + part.attrib['Type'] + ")"

	if part.attrib['Type'] != "DistributionBoard":
		write_node(part.attrib['Name'], depth, f)
		
		for devref in part.findall(FIND_DEVICEREF):
			processDevice(root, devref.attrib['RefId'], depth + 1, f)

	for subpart in part.findall(FIND_BUILDINGPART):
		processBuildingPart(root, subpart, depth + 1, f)
		
	f.write('\n')

def processDevice(root, ref, depth, f):
	print "process device " + ref
	device = root.findall('.//' + FIND_DEVICE + "[@Id='" + ref + "']")[0]
	if 'Description' in device.attrib.keys():
		print device.attrib['Description']

	for comobj in device.findall('.//' + FIND_COMREF):
		# TODO: read DPT
		for connector in comobj.findall('.//' + FIND_CONNECTOR):

			for send in connector.findall('.//' + FIND_SEND):
				if 'GroupAddressRefId' in send.keys():
					ga_ref = send.attrib['GroupAddressRefId']
					print "process ga " + ga_ref
					ga = root.findall('.//' + FIND_GA + "[@Id='" + ga_ref + "']")[0]
					ga_str = ga2str(int(ga.attrib['Address']))
					print "Send GA: " + ga_str + " (" + ga.attrib['Name'] + ")"

					if len(ga_str) > 0:
						write_node(ga.attrib['Name'], depth, f)
						write_param("knx_send=" + ga_str, depth + 1, f)

			for receive in connector.findall('.//' + FIND_RECEIVE):
				if 'GroupAddressRefId' in receive.keys():
					ga_ref = receive.attrib['GroupAddressRefId']
					print "process ga " + ga_ref
					ga = root.findall('.//' + FIND_GA + "[@Id='" + ga_ref + "']")[0]
					ga_str = ga2str(int(ga.attrib['Address']))
					print "Receive GA: " + ga_str + " (" + ga.attrib['Name'] + ")"

					if len(ga_str) > 0:
						write_node(ga.attrib['Name'], depth, f)
						write_param("knx_read=" + ga_str, depth + 1, f)

def write_param(string, depth, f):
	for i in range(depth):
		f.write('\t')

	f.write(string + '\n')

def write_node(string, depth, f):
	for i in range(depth):
		f.write('\t')

	for i in range(depth + 1):
		f.write('[')

	f.write("'" + string.encode('UTF-8') + "'")

	for i in range(depth + 1):
		f.write(']')

	f.write('\n')

def ga2str(ga):
	return "%d/%d/%d" % ((ga >> 11) & 0xf, (ga >> 8) & 0x7, ga & 0xff)

def pa2str(pa):
	return "%d.%d.%d" % (pa >> 12, (pa >> 8) & 0xf, pa & 0xff)

##############################################################
#		Main
##############################################################

if (os.path.exists(OUTFILE)):
	os.remove(OUTFILE)

tree = ET.parse('/home/niko/Arbeitsfläche/P-024F/0.xml')
root = tree.getroot()
buildings = root.find('.//' + FIND_BUILDINGS)

if buildings is None:
	print "Buildings not found"
else:
	with open(OUTFILE, 'w') as f:
		if IGNORE_TOP_LEVEL:
			for part in buildings[0]:
				processBuildingPart(root, part, 0, f)
		else:
			for part in buildings:
				processBuildingPart(root, part, 0, f)


