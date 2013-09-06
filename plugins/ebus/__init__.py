#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#
# Copyright 2012-2013 KNX-User-Forum e.V.       http://knx-user-forum.de/
#
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
#

import logging
import socket
import threading
import time

logger = logging.getLogger('eBus')


class eBus():
    _attribute = {}

    def __init__(self,	smarthome,	host,	port,	cycle):
        self._sh = smarthome
        self._cycle = float(cycle)
        self._sock = False
        self.is_connected = False
        self.host = host
        self.port = int(port)
        self._connection_attempts = 0
        self._connection_errorlog = 60
        self._sh.monitor_connection(self)
        self._lock = threading.Lock()
        self.refresh_cycle = self._cycle

    def parse_item(self, item):
        #	Attribute und Parameter werden regelmäßig ausgelesen
        if 'ebus_type' in item.conf:
            ebus_type = item.conf['ebus_type']
            ebus_cmd = item.conf['ebus_cmd']  # Wert hinter "ebusd_cmd = "
            self._attribute[ebus_type, ebus_cmd] = item  # makes array
            logger.debug("eBus: new set = item:{0} type:{1} cmd:{2}".format(item, ebus_type, ebus_cmd))
            return self.update_item

    def run(self):
        refresh_cycle = self._cycle / int(len(self._attribute))
        logger.debug("eBus: item-cycle: {0}".format(refresh_cycle))
        self.alive = True
        logger.info("eBus: Initial read values !!! ")
        for cmds in self._attribute:
            try:
                time.sleep(0.1)
                item = self._attribute[cmds]
                self.refresh(item)
            except Exception as e:
                logger.warning("ebusd:	exception:	{0}".format(e))
        logger.info("eBus: Start cyclic read values !!! ")
        while self.alive:
            for cmds in self._attribute:
                try:
                    if self.alive:
                        #logger.info("ebusd:sleep for {0} seconds".format(refresh_cycle))
                        pass
                    if self.alive:
                        item = self._attribute[cmds]
                    if self.alive:
                        self.refresh(item)
                    if self.alive:
                        time.sleep(refresh_cycle)
                except Exception as e:
                    logger.warning("ebusd:	exception:	{0}".format(e))

    def request(self,	request):
        if not self.is_connected:
            logger.info("not connected")
            time.sleep(10)
        try:
            self._sock.send(request)
            logger.debug("REQUEST: {0}".format(request))
        except Exception,	e:
            self._lock.release()
            self.close()
            logger.debug("error	sending	request:	{0}".format(e))
        try:
            answer = self._sock.recv(256)
            ####[:-2] entfernt Zeilenumbruch/letzte 2 Zeichen
            logger.debug("ANSWER: {0}".format(answer[:-2]))
        except socket.timeout:
            self._lock.release()
            logger.error("error	receiving answer: timeout")
        except Exception,	e:
            self._lock.release()
            self.close()
            logger.error("error	receiving answer: {0}".format(e))
        return answer[:-2]

    def connect(self):
        self._lock.acquire()
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(2)
            self._sock.connect((self.host, self.port))
        except Exception, e:
            self._connection_attempts -= 1
            if self._connection_attempts <= 0:
                logger.error('eBus:	could not connect to {0}:{1}: {2}'.format(self.host, self.port, e))
                self._connection_attempts = self._connection_errorlog
            return
        logger.info('Connected to {0}:{1}'.format(self.host, self.port))
        self._lock.release()
        self.is_connected = True
        self._connection_attempts = 0

    def close(self):
        self.is_connected = False
        try:
            self._sock.close()
            self._sock = False
            logger.info(
                'Connection	closed to {0}:{1}'.format(self.host, self.port))
        except:
            pass

    def stop(self):
        self.close()
        self.alive = False
        handle_close()

    def refresh(self, item):
        ebus_type = item.conf['ebus_type']
        ebus_cmd = item.conf['ebus_cmd']
        logger.debug(
            "REFRESH parameter: item:{0} cmd:{1}".format(item, ebus_cmd))
        if ebus_cmd == "cycle":
            request = ebus_type + " " + ebus_cmd  # build command
        else:
            request = "get" + " " + ebus_cmd  # build	command
        answer = self.request(request)
        if (item._type == 'bool'):
            # convert	to	get	'0'/'1'	instead	of	'True'/'False'
            answer = bool(answer)
        else:
            answer = float(answer)
        item(answer, 'eBus', 'refresh')

    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'eBus':
            if (item._type == 'bool'):
                logger.info("Item is: {0}".format(item()))
                # convert	to	get	'0'/'1'	instead	of	'True'/'False'
                value = int(item())
            else:
                value = int(item())
            logger.info("Called to refresh item: {0}".format(item))
            self.set_parameter(item.conf['ebus_cmd'], item, value)

    def set_parameter(self, cmd, item, value):
        logger.debug("SET parameter: item:{0} cmd:{1} value:{2}".format(item, cmd, value))
        request = "set " + cmd + " " + str(value)
        self.request(request)
        self.check_set(item, cmd)

    def check_set(self, item, cmd):
        logger.debug("CHECK parameter: item:{0} cmd:{1}".format(item, cmd))
        request = "get " + cmd
        answer = self.request(request)
        item(answer, 'eBus', 'checked')
