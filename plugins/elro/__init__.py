#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
#
#  This file is part of SmartHome.py.    http://mknx.github.io/smarthome/
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
#

import logging
import re
import socket

logger = logging.getLogger('elro')


class Elro():

    def __init__(self, smarthome, elro_host="localhost", elro_port=6700):
        self._sh = smarthome
        self._host = elro_host
        self._port = int(elro_port)
        logger.info("ELRO WAS CREATED")

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        # Check if there are elro_system_code, elro_unit_code and elro_send fields for a item
        if 'elro_system_code' in item.conf:
            if 'elro_unit_code' in item.conf:
                if 'elro_send' in item.conf:
                    # Add method to trigger if a button was pressed
                    item.add_method_trigger(self._send)
    
    def _send(self, item, caller=None, source=None, dest=None):
        if (caller != 'Elro'):
            # Send informations to server (e.g. "0.0.0.0.1;2;0")
            self.send("%s;%s;%s" % (item.conf['elro_system_code'], item.conf['elro_unit_code'], int(item())))
    
    def send(self, payload, host=None, port=None):
        
        # Check if host and/or port was given
        if host == None:
            host = self._host
        if port == None:
            port = self._port
        
        # Create socket
        s = socket.socket()
        
        # Connect to server
        s.connect((self._host, self._port))
        
        # Write payload to server
        s = s.makefile(mode = "rw")
        s.write(payload)
        s.flush()
        
        # Close server-connection
        s.close()
