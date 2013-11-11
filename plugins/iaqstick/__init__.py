#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2013 Robert Budde                       robert@projekt131.de
#########################################################################
#  iAQ-Stick plugin for SmartHome.py.    http://mknx.github.io/smarthome/
#
#  This plugin is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This plugin is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this plugin. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

#/etc/udev/rules.d/99-iaqstick.rules
#SUBSYSTEM=="usb", ATTR{idVendor}=="03eb", ATTR{idProduct}=="2013", MODE="666"
#udevadm trigger

import logging
import usb.core
import usb.util
from time import sleep

logger = logging.getLogger('iAQ_Stick')

class iAQ_Stick():
    def __init__(self, smarthome, update_cycle = "10"):
        self._sh = smarthome
        self._update_cycle = int(update_cycle)
        self._info_tags = {}

    def xfer_type1(self, msg):
        out_data = bytes('@{:04X}{}\n@@@@@@@@@@'.format(self._type1_seq, msg), 'utf-8')
        self._type1_seq = (self._type1_seq + 1) & 0xFFFF
        ret = self._dev.write(0x02, out_data[:16], self._intf, 1000)
        in_data = bytes()
        while True:
            ret = bytes(self._dev.read(0x81, 0x10, self._intf, 1000))
            if len(ret) == 0:
                break
            in_data += ret
        return in_data.decode('iso-8859-1')

    def xfer_type2(self, msg):
        out_data = bytes('@', 'utf-8') + self._type2_seq.to_bytes(1, byteorder='big') + bytes('{}\n@@@@@@@@@@@@@'.format(msg), 'utf-8')
        self._type2_seq = (self._type2_seq + 1) if (self._type2_seq < 0xFF) else 0x67
        ret = self._dev.write(0x02, out_data[:16], self._intf, 1000)
        in_data = bytes()
        while True:
            ret = bytes(self._dev.read(0x81, 0x10, self._intf, 1000))
            if len(ret) == 0:
                break
            in_data += ret
        return in_data

    def run(self):
        self._dev = usb.core.find(idVendor=0x03eb, idProduct=0x2013)
        if self._dev is None:
            logger.error('iaqstick: iAQ Stick not found')
            return
        self._intf = 0
        self._type1_seq = 0x0001
        self._type2_seq = 0x67
        
        try:
            if self._dev.is_kernel_driver_active(self._intf):
                self._dev.detach_kernel_driver(self._intf)
            
            self._dev.set_configuration(0x01)
            usb.util.claim_interface(self._dev, self._intf)
            self._dev.set_interface_altsetting(self._intf, 0x00)
            
            manufacturer = usb.util.get_string(self._dev, 0x101, 0x01, 0x409)
            product = usb.util.get_string(self._dev, 0x101, 0x02, 0x409)
            logger.info('iaqstick: Manufacturer: {} - Product: {}'.format(manufacturer, product))
            ret = self.xfer_type1('*IDN?')
            #print(ret)
            self._dev.write(0x02, bytes('@@@@@@@@@@@@@@@@', 'utf-8'), self._intf, 1000)
            ret = self.xfer_type1('KNOBPRE?')
            #print(ret)
            ret = self.xfer_type1('WFMPRE?')
            #print(ret)
            ret = self.xfer_type1('FLAGS?')
            #print(ret)
        except Exception as e:
            logger.error("iaqstick: init interface failed - {}".format(e))
        
        self.alive = True 
        self._sh.scheduler.add('iAQ_Stick', self._update_values, prio = 5, cycle = self._update_cycle)
        logger.info("iaqstick: init successful")

    def stop(self):
        self.alive = False
        try:
            usb.util.release_interface(self._dev, self._intf)
        except Exception as e:
            logger.error("iaqstick: releasing interface failed - {}".format(e))
        try:
            self._sh.scheduler.remove('iAQ_Stick')
        except Exception as e:
            logger.error("iaqstick: removing iAQ_Stick from scheduler failed - {}".format(e))

    def _update_values(self):
        #logger.debug("iaqstick: update")
        try:
            self.xfer_type1('FLAGGET?')
            meas = self.xfer_type2('*TR')
            ppm = int.from_bytes(meas[2:4], byteorder='little')
            logger.debug('iaqstick: ppm: {}'.format(ppm))
            #logger.debug('iaqstick: debug?: {}'.format(int.from_bytes(meas[4:6], byteorder='little')))
            #logger.debug('iaqstick: PWM: {}'.format(int.from_bytes(meas[6:7], byteorder='little')))
            #logger.debug('iaqstick: Rh: {}'.format(int.from_bytes(meas[7:8], byteorder='little')*0.01))
            #logger.debug('iaqstick: Rs: {}'.format(int.from_bytes(meas[8:12], byteorder='little')))
            if 'ppm' in self._info_tags:
                for item in self._info_tags['ppm']['items']:
                    item(ppm, 'iAQ_Stick', 'USB')
        except Exception as e:
            logger.error("iaqstick: update failed - {}".format(e))

    def parse_item(self, item):
        if 'iaqstick_info' in item.conf:
            logger.debug("parse item: {0}".format(item))
            info_tag = item.conf['iaqstick_info'].lower()
            if not info_tag in self._info_tags:
                self._info_tags[info_tag] = {'items': [item], 'logics': []}
            else:
                self._info_tags[info_tag]['items'].append(item)
        return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    myplugin = Plugin('iAQ_Stick')
    myplugin.run()

#Application Version: 2.19.0 (Id: Form1.frm 1053 2010-06-30 11:00:09Z patrik.arven@appliedsensor.com )
#
#Device 0:
#Name: iAQ Stick
#Firmware: 1.12p5 $Revision: 346 $
#Protocol: 5
#Hardware: C
#Processor: ATmega32U4
#Serial number: S/N:48303230303415041020
#Web address: 
#Plot title: Air Quality Trend
#
#Channels: 5
#... Channel 0:CO2/VOC level
#... Channel 1:Debug
#... Channel 2:PWM
#... Channel 3:Rh
#... Channel 4:Rs
#Knobs: 8
#... Knob CO2/VOC level_warn1:1000
#... Knob CO2/VOC level_warn2:1500
#... Knob Reg_Set:151
#... Knob Reg_P:3
#... Knob Reg_I:10
#... Knob Reg_D:0
#... Knob LogInterval:0
#... Knob ui16StartupBits:1
#Flags: 5
#... WARMUP=&h0000&
#... BURN-IN=&h0000&
#... RESET BASELINE=&h0000&
#... CALIBRATE HEATER=&h0000&
#... LOGGING=&h0000&
#
#@013E;;DEBUG:
#Log:
#buffer_size=&h1400;
#address_base=&h4800;
#readindex=&h0040;
#Write index=&h0000;
#nValues=&h0000;
#Records=&h0000;
#nValues (last)=&h0000;
#uint16_t g_u16_loop_cnt_100ms=&h08D4;
#;\x0A
