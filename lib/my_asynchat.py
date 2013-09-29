#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012-2013 Marcus Popp                          marcus@popp.mx
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
import os

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
        self.buffer = bytearray()
        self.terminator = '\r\n'
        self.is_connected = False
        self._sh = smarthome
        self._conn_lock = threading.Lock()
        self._connection_attempts = 0
        self._connection_errorlog = 60

    def connect(self):
        self._conn_lock.acquire()
        if self.is_connected:  # only allow one connection at a time
            logger.debug("Don't be hasty. Reduce connection attempts of: {0}".format(self.__class__.__name__))
            self._conn_lock.release()
            return
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.settimeout(1)
            err = self.socket.connect_ex(self.addr)
            if err in (114, 115):
                self._conn_lock.release()
                return
            if err not in (0, 106):
                self.handle_exception(err)
                self._conn_lock.release()
                return
            self.connected = True
            self.is_connected = True
            self.handle_connect_event()
            logger.info('{0}: connected to {1}:{2}'.format(self.__class__.__name__, self.addr[0], self.addr[1]))
        except Exception as err:
            self.handle_exception(err)
        self._conn_lock.release()

    def collect_incoming_data(self, data):
        self.buffer.extend(data)

    def initiate_send(self):
        self._send_lock.acquire()
        asynchat.async_chat.initiate_send(self)
        self._send_lock.release()

    def handle_exception(self, err):
        try:
            err = os.strerror(err)
        except:
            pass
        self._connection_attempts -= 1
        if self._connection_attempts <= 0:
            logger.warning('{0}: could not connect to {1}:{2}: {3}'.format(self.__class__.__name__, self.addr[0], self.addr[1], err))
            self._connection_attempts = self._connection_errorlog
        self.handle_close()

    def handle_connect_event(self):
        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err != 0:
            self.handle_exception(err)
            return
        self._connection_attempts = 0
        self.handle_connect()

    def handle_close(self):
        if self.is_connected:
            logger.info('{0}: connection to {1}:{2} closed'.format(self.__class__.__name__, self.addr[0], self.addr[1]))
        self.connected = False
        self.accepting = False
        self.is_connected = False
        self.del_channel(map=self._sh.socket_map)
        self.discard_buffers()
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.socket.close()
        except:
            pass
