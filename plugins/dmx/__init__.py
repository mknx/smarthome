#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011 KNX-User-Forum e.V.            http://knx-user-forum.de/
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

import logging
import threading
import serial

logger = logging.getLogger('')


class DMX():
    # _dim = 10^((n-1)/(253/3)-1) by JNK from KNX UF
    #_dim = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 12, 12, 12, 13, 13, 13, 14, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25, 26, 26, 27, 28, 29, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 50, 51, 52, 54, 55, 57, 58, 60, 62, 63, 65, 67, 69, 71, 73, 75, 77, 79, 81, 83, 86, 88, 90, 93, 95, 98, 101, 104, 106, 109, 112, 115, 119, 122, 125, 129, 132, 136, 140, 144, 148, 152, 156, 160, 165, 169, 174, 179, 184, 189, 194, 199, 205, 211, 216, 222, 228, 235, 241, 248, 255 ]

    def __init__(self, smarthome, tty):
        self._sh = smarthome
        self._is_connected = False
        self._lock = threading.Lock()

        try:
            self._port = serial.Serial(tty, 38400, timeout=1)
        except:
            logger.error("Could not open %s." % tty)
            return
        else:
            self._is_connected = True
        if not self._send("C?"):
            logger.warning("Could not communicate with dmx adapter.")
            self._is_connected = False

    def _send(self, data):
        if not self._is_connected:
            return False
        self._lock.acquire()
        try:
            self._port.write(data)
            ret = self._port.read(1)
        except:
            logger.warning("Problem sending data to dmx adapter.")
            ret = 'F'
        self._lock.release()
        if ret == 'G':
            return True
        else:
            return False

    def run(self):
        self.alive = True

    def stop(self):
        self._port.close()
        self.alive = False

    def send(self, channel, value):
        self._send("C{0:03d}L{1:03d}".format(int(channel), int(value)))

    def parse_node(self, node):
        if 'dmx_ch' in node.conf:
            channels = node.conf['dmx_ch']
            if isinstance(channels, str):
                channels = [channels, ]
            channels = map(int, channels)
            node.conf['dmx_ch'] = channels
            return self.update_node
        else:
            return None

    def update_node(self, node, caller=None, source=None):
        #logger.debug("update dmx channel {0:03d}".format(node.dmx_ch))
        for channel in node.conf['dmx_ch']:
            self.send(channel, node())
