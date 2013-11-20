#!/usr/bin/python

import serial
import time
import sys
import logging
import math
from struct import *
logger = logging.getLogger('Roomba')

cmd_dict=dict(
    power_off = 133,            #change2passive
    spot = 134,                 #change2passive
    clean = 135,                #change2passive
    max = 136,                  #change2passive
    stop = [137,0,0,0,0],
    forward = [137,0,100,128,0],
    backward = [137,255,156,128,0], 
    spin_right = [137,0,100,255,255],
    spin_left = [137,0,100,0,1],
    dock = 143,                 #change2passive
)

# maybe supported later
# motors = 138,               #add 1 databyte
# leds = 139,                 #add 3 databytes
# song = 140,                 #add 2n + 2 databytes
# play = 141,                 #add 1 databyte


class Roomba(object):
    _items = []
    
    def __init__(self,smarthome,tty,baudrate,cycle):
        self._sh = smarthome
        self.tty = tty
        self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.tty, baudrate=self.baudrate, timeout=2)
        except:
            pass
        self.is_connected = 'False'
        self._cycle = int(cycle)
        if self._cycle > 0:
            self._sh.scheduler.add('Roomba', self.get_sensors, prio=5, cycle=self._cycle, offset=10)      
    
    def run(self):
        pass
    
    def init_command(self):
        self.send(128)  #start
        time.sleep(0.2)
        self.send(130)  #command
        time.sleep(0.2)
        
    def send(self, raw):
        if self.is_connected == 'False':
            try:
                self.connect()
            except:
                logger.error("Roomba: (Re)connect failed in send")
        if self.is_connected == 'True':
            if type(raw) is list:
                #print ("Send {0}".format(raw))
                logger.debug("Roomba: Send List:{0}".format(raw))
                try:
                    self.ser.write(bytearray(raw))
                except:
                    logger.error("Roomba: Send failed for {}!".format(raw))
                    
            else:
                #print ("Send [{0}]".format(raw))
                logger.debug("Roomba: Send Single:{0}".format([raw]))
                try:
                    self.ser.write(bytearray([raw]))
                except:
                    logger.error("Roomba: Send failed for {}!".format([raw]))

    def connect(self):
        logger.debug("Roomba: Try to connect")
        try:
            self.ser.open()
            self.ser.flushInput()
            logger.debug("Roomba: Connected")
            self.is_connected = 'True'
        except:
            logger.error("Roomba: Function connect failed")
            self.is_connected = 'False'
    
    def disconnect(self):
        self.ser.close()
        self.is_connected = 'False'
        logger.debug("Roomba: Disconnected")
    
    def parse_item(self, item):
        if 'roomba_get' in item.conf:
            sensor_string = item.conf['roomba_get']
            logger.debug("Roomba: {0} will get \'{1}\'".format(item, sensor_string))
            self._items.append(item)
            return self.update_item      
        if 'roomba_cmd' in item.conf:
            cmd_string = item.conf['roomba_cmd']
            logger.debug("Roomba: {0} will drive \'{1}\'".format(item, cmd_string))
            self._items.append(item)
            return self.update_item
        if 'roomba_raw' in item.conf:
            raw_list = item.conf['roomba_raw']
            logger.debug("Roomba: {0} send raw \'{1}\'".format(item, raw_list))
            self._items.append(item)
            return self.update_item	
            
    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'Roomba':
            if item():
                if 'roomba_cmd' in item.conf:
                    cmd_string = item.conf['roomba_cmd']
                    logger.debug("Roomba: item = true")
                    self.drive(cmd_string)
                if 'roomba_raw' in item.conf:
                    raw_string = item.conf['roomba_raw']
                    self.raw(raw_string)
                else:
                    pass
       
    def drive(self,cmd_string):
        self.init_command()
        if type(cmd_string) is list:
            for i in cmd_string:
                try:
                    wait = float(i)
                    time.sleep(wait)
                    #print ('SLEEP {0}'.format(wait))
                except:
                    self.send(cmd_dict[i])
                    #print (cmd_dict[i])
        else:
            #print (cmd_dict[cmd_string])
            self.send(cmd_dict[cmd_string])
        self.disconnect()
        
    def raw(self,raw_string):
        self.init_command()
        full_raw_cmd = []
        if type(raw_string) is list:
            for i in raw_string:
                i = int(i)
                full_raw_cmd.append(i)
            self.send(full_raw_cmd)
        else:
            self.send(int(raw_string))
        self.disconnect()
        
    def get_sensors(self):
        self.send([142,0])
        answer = self.ser.read(26)
        if len(answer) == 26:
            logger.debug("Roomba: Got sensor data.")
            answer = list(answer)
            #print (answer)
            
            #create sensor_dict
            sensor_dict = dict()
            
            #sensor_raw:
            _capacity = self.DecodeUnsignedShort(answer[25],answer[24]) #capacity
            sensor_dict['capacity']=_capacity
            
            _charge=self.DecodeUnsignedShort(answer[23],answer[22]) #charge
            sensor_dict['charge']=_charge
            
            _temperature = self.DecodeByte(answer[21]) #temperature
            sensor_dict['temperature']=_temperature
            
            _current=self.DecodeShort(answer[20],answer[19]) #current
            sensor_dict['current']=_current
            
            _voltage = self.DecodeUnsignedShort(answer[18],answer[17]) #voltage
            sensor_dict['voltage']=_voltage
            
            _charging_state = answer[16] #charging state
            sensor_dict['charging_state']=_charging_state
            #0=Not Charging, 1=Charging Recovery, 2=Charging, 3=Trickle Charging, 4=Waiting, 5=Charging Error
            
            _angle = self.Angle(answer[15], answer[14], 'degrees') #angle
            sensor_dict['angle']=_angle
            
            _distance = self.DecodeShort(answer[13],answer[12]) #distance
            sensor_dict['distance']=_distance
            
            _buttons = answer[11] #Button
            #returns max,clean,spot,power
            sensor_dict['buttons_max']=bool(_buttons & 0x01)
            sensor_dict['buttons_clean']=bool(_buttons & 0x02)
            sensor_dict['buttons_spot']=bool(_buttons & 0x04)
            sensor_dict['buttons_power']=bool(_buttons & 0x08)
            
            _remote_opcode = answer[10] #remote_opcode
            sensor_dict['remote_opcode']=_remote_opcode
            
            _dirt_detect_right = bool(answer[9]) #dirt detect right
            sensor_dict['dirt_detect_right']=_dirt_detect_right
            
            _dirt_detect_left = bool(answer[8]) #dirt detect left
            sensor_dict['dirt_detect_left']=_dirt_detect_left
            
            _motor_overcurrent = answer[7] #motor overcurrent
            #returns side-brush,vacuum,main-brush,drive-right,drive-left
            sensor_dict['motor_overcurrent_side_brush']=bool(_motor_overcurrent & 0x01)
            sensor_dict['motor_overcurrent_vacuum']=bool(_motor_overcurrent & 0x02)
            sensor_dict['motor_overcurrent_main_brush']=bool(_motor_overcurrent & 0x04)
            sensor_dict['motor_overcurrent_drive_right']=bool(_motor_overcurrent & 0x08)        
            sensor_dict['motor_overcurrent_drive_left']=bool(_motor_overcurrent & 0x010)
            
            _virtual_wall = answer[6]
            sensor_dict['virtual_wall']=bool(_virtual_wall)
            
            _cliff_right = answer[5]
            sensor_dict['cliff_right']=bool(_cliff_right)
            
            _cliff_front_right = answer[4]
            sensor_dict['cliff_front_right']=bool(_cliff_front_right)
            
            _cliff_front_left = answer[3]
            sensor_dict['cliff_front_left']=bool(_cliff_front_left)
            
            _cliff_left = answer[2]
            sensor_dict['cliff_left']=bool(_cliff_left)
            
            _wall = answer[1]
            sensor_dict['wall']=bool(_wall)
            
            _bumps_wheeldrops = answer[0]
            #returns bump-right,bump-left,wheel-drop-right,wheel-drop-left,wheel-drop-caster
            sensor_dict['bumps_wheeldrops_bump_right']=bool(_bumps_wheeldrops & 0x01) #bit 1
            sensor_dict['bumps_wheeldrops_bump_left']=bool(_bumps_wheeldrops & 0x02) #bit 2
            sensor_dict['bumps_wheeldrops_wheeldrop_right']=bool(_bumps_wheeldrops & 0x04) #bit 3
            sensor_dict['bumps_wheeldrops_wheeldrop_left']=bool(_bumps_wheeldrops & 0x08) #bit 4
            sensor_dict['bumps_wheeldrops_wheeldrop_caster']=bool(_bumps_wheeldrops & 0x10) #bit 5
            
            for item in self._items:
                if 'roomba_get' in item.conf:
                    sensor = item.conf['roomba_get']
                    if sensor in sensor_dict:
                        value = sensor_dict[sensor]
                        item(value, 'Roomba', 'get_sensors')
                        #print ("SENSOR: {0}  VALUE: {1}".format(sensor,value))
        else:
            logger.error("Roomba: Sensors not readable")
        self.disconnect()

    def DecodeUnsignedShort(self, low, high):
        bytearr = bytearray([high,low])
        value = unpack('>H', bytearr)
        return (value[0])
        
    def DecodeByte(self,byte):
        bytearr = bytearray([byte])
        value = unpack('b', bytearr)
        return (value[0])
        
    def DecodeShort(self, low, high):
        bytearr = bytearray([high,low])
        value = unpack('>h', bytearr)
        return (value[0])
    
    def Angle(self, low, high, unit=None):
        #Angle in radians = (2 * difference) / 258
        #Angle in degrees = (360 * difference) / (258 * Pi).
        if unit not in (None, 'radians', 'degrees'):
            pass
        angle = self.DecodeShort(low, high)
        if unit == 'radians':
            angle = (2 * angle) / 258
            #print ("{0} radians".format(angle))
            return angle
        if unit == 'degrees':
            angle /= math.pi
            #print ("{0} degrees".format(angle))
            return angle
        

        
