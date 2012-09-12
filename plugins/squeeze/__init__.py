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
#  along with SmartHome.py.  If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import asynchat, asyncore, socket
import types
import logging
import time
import threading

logger = logging.getLogger('')

class Squeeze(asynchat.async_chat):

    EOL = '\n'
    socket_map = {}
    lock = threading.Condition()
    buffer = ''
    resp = None

    def __init__(self, smarthome, host='127.0.0.1', port=9090):
        asynchat.async_chat.__init__(self, map=self.socket_map)
        self._sh = smarthome
        self.host = host
        self.port = int(port)
        self.set_terminator(self.EOL)

    def play(self, item):
        resp = self.command(item, 'play')
        return resp

    def sstop(self, item): # collision with plugin stop
        resp = self.command(item, 'stop')
        return resp

    def command(self, item, command=''):
        if hasattr(item, 'squeeze_id'):
            request = "%s %s%s" % (item.squeeze_id, command, self.EOL)
        else:
            request = "%s %s%s" % (item, command, self.EOL)
        logger.debug("Request: %s" % request)
        self.lock.acquire()
        self.resp = None
        self.push(request)
        self.lock.wait(0.5)
        resp = self.resp
        self.lock.release()
        logger.debug("Response: %s" % resp)
        return resp

    def _connect(self):
        print 'connecting...'
        self.discard_buffers() # clear outgoing buffer
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (self.host, self.port) )
        self.connected=True
        time.sleep(1)

    def handle_error(self):
        logger.warning("Error with connection to %s:%s" % (self.host, self.port) )
        self.close()
        self.connected = False
        time.sleep(5)

    def handle_close(self):
        self.close()
        self.connected = False

    def collect_incoming_data(self, data):
        self.buffer += data

    def found_terminator(self):
        self.resp = self.buffer
        if not self.lock.acquire(false): # notify if lock is locked
            self.lock.notify()
        self.lock.release()
        self.buffer = ''

    def run(self):
        self.alive = True
        while self.alive:
            if self.connected:
                asyncore.loop(timeout=1, count=1, map=self.socket_map)
            else:
                self._connect()

    def stop(self):
        self.alive = False
        asyncore.close_all(map=self.socket_map)
        self.close()

    def parse_item(self, item):
        if hasattr(item, 'squeeze_id'):
            item.play = types.MethodType(self.play, item, item.__class__)
            item.stop = types.MethodType(self.sstop, item, item.__class__)
            item.command = types.MethodType(self.command, item, item.__class__)
            if hasattr(item, 'squeeze_command'):
                return self.update_item
        return None

    def parse_logic(self, logic):
        #if 'xxx' in logic:
            # self.function(logic['name'])
        pass

    def update_item(self, item, caller=None, source=None):
        if caller != 'squeeze':
            command = item.squeeze_command
            value = item()
            if command == 'mixer muting':
                value = int(value)
            command = "%s %s" % (command, value)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    myplugin = Squeeze('smarthome-dummy')
    myplugin.run()
