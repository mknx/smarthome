#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012-2013 KNX-User-Forum e.V.       http://knx-user-forum.de/
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
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import sys
import logging
import socket
import threading
import struct
import time
import datetime

logger = logging.getLogger('')

class ebusex(Exception):
    pass

class ebusBase():

    def __init__(self, host, port=8888):
        self.host = host
        self.port = int(port)
        self._sock = False
        self.is_connected = False
        self._connection_attempts = 0
        self._connection_errorlog = 60
        self._params = []
        self._attrs = []

    def connect(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(2)
            self._sock.connect((self.host, self.port))
        except Exception, e:
            self._connection_attempts -= 1
            if self._connection_attempts <= 0:
                logger.error('eBus: could not connect to {0}:{1}: {2}'.format(self.host, self.port, e))
                self._connection_attempts = self._connection_errorlog
            return
        logger.info('eBus: connected to {0}:{1}'.format(self.host, self.port))
        self.is_connected = True
        self._connection_attempts = 0

    def close(self):
        try:
            self._sock.close()
            self._sock = False
            self.is_connected = False
            logger.info('eBus: disconnected')
        except:
                logger.debug('eBus: failed to disconnect')

    def _request(self, request):
        if not self.is_connected:
            self.connect()
        else:
            pass
        
        logger.debug("eBus: REQUEST: {0}".format(request))
        self._sock.send(request)
        answer = self._sock.recv(256)
        logger.debug("eBus: ANSWER: {0}".format(answer[:-2]))
        logger.debug("eBus: request: {0} >>><<< answer: {1}".format(request,answer[:-2])) #### [:-2] entfernt Zeilenumbruch/letzte 2 Zeichen
        answer = answer.replace(" ", "") ### Remove whitespaces
        	
        self.close()
        self.is_connected = False 
        return answer[:-2]
            
    def set_parameter(self,cmd,item):
        logger.debug("eBus: set parameter: value:{0} cmd:{1}".format(item,cmd))
        request = "set " + cmd + " " + str(item)
        answer = self._request(request)
        logger.debug("eBus: command:{0}".format(request))
        logger.debug("eBus: answer:{0}".format(answer))
        #self.check_set(item())
        
    def check_set(self,item):
        logger.debug("eBus: {0}".format(item()))
        logger.debug("eBus: Check SET: value:{0} cmd:{1}".format(item,cmd))
        request = item.conf['ebus_type'] +" " + cmd + " " + str(item)
        #answer = self._request(request)
        logger.debug("eBus: command:{0}".format(request))
        logger.debug("eBus: answer:{0}".format(answer))        
        
    def refresh_attributes(self):
        self.refresh_id = 1
        
        for cmds in self._attribute:
            if cmds[0] == "cycle":
                request = cmds[0] + " " + cmds[1]     #build command
            else:
                request = "get" + " " + cmds[1]     #build command
                
            if self.refresh_id == self.id:
                answer = self._request(request)
                #logger.debug("eBus: Parameter/Refresh {0}/{1}".format(self.id,self.refresh_id))
                self._attribute[cmds](answer, 'eBus', 'refresh')   #according to item(answer)
                return answer
            else:
                self.refresh_id +=1

class eBus(ebusBase):
    _parameter = {}
    _attribute = {}
    alive = True
    
    def __init__(self, smarthome, host, port, cycle):
        ebusBase.__init__(self, host, port)
        self._sh = smarthome
        #logger.debug("eBus: cycle = {0} seconds".format(cycle)) 
        self._cycle = int(cycle)
        self.connect()
        self.id = 1
        self.refresh_id = 0

    def run(self):
        self.alive = True
        new_cycle = self._cycle/int(len(self._attribute))
        logger.debug("eBus: refresh-cycle = {0} seconds".format(new_cycle)) 
        self._sh.scheduler.add('eBus', self._refresh, cycle=new_cycle)
        
    def stop(self):
        self.alive = False

    def _refresh(self):
        start = time.time()

        if len(self._attribute) > 0:
            #logger.debug("eBus: attributes: {0}".format(self._attribute))
            val = self.refresh_attributes()
            #logger.debug("eBus: refreshed value {0}".format(val))

            if self.id >= len(self._attribute):
                self.id = 1
            else:
                self.id += 1
                #logger.debug("eBus: next cycle-id: {0}".format(self.id))
        #cycletime = time.time() - start
        #logger.debug("eBus: number of attributes {0}".format(len(self._attribute)))
        #logger.debug("cycle takes {0} seconds".format(cycletime))

    def parse_item(self, item):
        if 'ebus_type' in item.conf:							# Attribute und Parameter werden regelmäßig ausgelesen
            ebus_type = item.conf['ebus_type']
            ebus_cmd = item.conf['ebus_cmd']						# Wert hinter "ebusd_cmd = "
            self._attribute[ebus_type,ebus_cmd] = item				# makes array
            logger.debug("eBus: new set = item:{0} type:{1} cmd:{2}".format(item,ebus_type,ebus_cmd))
            return self.update_item
        
    def update_item(self, item, caller=None, source=None):
        if caller != 'eBus':
            logger.info("eBus: called to refresh item: {0}".format(item))
            self.set_parameter(item.conf['ebus_cmd'], item()) 
            