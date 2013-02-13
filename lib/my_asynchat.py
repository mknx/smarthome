#!/usr/bin/env python
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
#########################################################################

import asynchat
import socket
import threading
import logging
#from errno import EINPROGRESS, EALREADY, EWOULDBLOCK

logger = logging.getLogger('')


class AsynChat(asynchat.async_chat):

    def __init__(self, smarthome, host='127.0.0.1', port=4711):
        self.connected = False
        self.addr = None
        self.closing = False
        self.acception = False
        asynchat.async_chat.__init__(self, map=smarthome.socket_map)
        self.addr = (host, int(port))
        self._send_lock = threading.Lock()
        self.buffer = ''
        self.terminator = '\r\n'
        self.is_connected = False
        self._sh = smarthome
        self._conn_lock = threading.Lock()
        self._connection_attempts = 0
        self._connection_errorlog = 60

    def connect(self):
        self._conn_lock.acquire()
        if self.is_connected:  # only allow one connection at a time
            logger.debug("Don't be hasty. Reduce connection attempts from: {0}".format(self.__class__.__name__))
            self._conn_lock.release()
            return
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.settimeout(4)
            self.socket.connect_ex(self.addr)
        except Exception, e:
            self._connection_attempts -= 1
            if self._connection_attempts <= 0:
                logger.error('{0}: could not connect to {1}:{2}: {3}'.format(self.__class__.__name__, self.addr[0], self.addr[1], e))
                self._connection_attempts = self._connection_errorlog
            self.is_connected = False
            self.handle_close()
            self._conn_lock.release()
            return
        logger.info('{0}: connected to {1}:{2}'.format(self.__class__.__name__, self.addr[0], self.addr[1]))
        self.connected = True
        self.is_connected = True
        self._connection_attempts = 0
        self.handle_connect()
        self._conn_lock.release()

    def collect_incoming_data(self, data):
        self.buffer += data

    def initiate_send(self):
        self._send_lock.acquire()
        asynchat.async_chat.initiate_send(self)
        self._send_lock.release()

    def handle_close(self):
        if self.is_connected:
            logger.info('{0}: connection to {1}:{2} closed'.format(self.__class__.__name__, self.addr[0], self.addr[1]))
        self.connected = False
        self.is_connected = False
        try:
            self.close()
        except:
            pass
