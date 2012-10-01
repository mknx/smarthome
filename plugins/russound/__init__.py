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

import logging
import socket
import threading
import struct

import lib.my_asynchat

logger = logging.getLogger('')

REQ_DELIMITER = '\r'
RESP_DELIMITER = '\r\n'

class Russound(lib.my_asynchat.AsynChat):

    def __init__(self, smarthome, host, port=9261):
        lib.my_asynchat.AsynChat.__init__(self, smarthome, host, port)
        self.terminator = RESP_DELIMITER
        self._sh = smarthome
        self.params = {}
        smarthome.monitor_connection(self)

    def parse_item(self, item):
        if 'rus_path' in item.conf:
            path = item.conf['rus_path']
            parts = path.split('.', 2)
            
            if len(parts) is not 3:
                return None

            c = parts[0]
            z = parts[1]
            param = parts[2]

        else:
            if 'rus_controller' in item.conf:
                c = item.conf['rus_controller']
                path = c + '.'
            else:
                return None

            if 'rus_zone' in item.conf:
                z = item.conf['rus_zone']
                path += z + '.'
            else:
                return None

            if 'rus_parameter' in item.conf:
                param = item.conf['rus_parameter']
                path += param
            else:
                return None

            item.conf['rus_path'] = path

        self.params[path] = {'c': int(c), 'z': int(z), 'param':param, 'item':item}
        return self.update_item

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None):
        if caller != 'Russound':
            p = self.params[item.conf['rus_path']]
            self.update(p.c, p.z, p.param, item())
            cmd = p.param.tolower()

            if cmd == 'bass':
                self.send_set(self, cmd, round(item() / (128 / 10)))
            elif cmd == 'treble':
                self.send_set(self, cmd, round(item() / (128 / 10)))
            elif cmd == 'balance':
                self.send_set(self, cmd, round(item() / (128 / 10)))
            elif cmd == 'loudness':
                self.send_set(self, cmd, 'ON' if item() else 'OFF')
            elif cmd == 'turnonvolume':
                self.send_set(self, cmd, round(item() / (255 / 50)))
            elif cmd == 'status':
                self.send_event(self, 'ZoneOn' if item() else 'ZoneOff')
            elif cmd == 'partymode':
                self.send_event(self, 'PartyMode', item().tolower())
            elif cmd == 'donotdisturb':
                self.send_event(self, 'DoNotDisturb', 'on' if item() else 'off')
            elif cmd == 'volume':
                self.send_event(self, 'KeyPress', 'Volume', round(item() / (255 / 50)))
            elif cmd == 'currentsource':
                self.send_event(self, 'SelectSource', item())
            elif cmd == 'mute':
                self.send_event(self, 'KeyRelease', 'Mute')

    def send_set(self, c, z, cmd, value):
        self.send_cmd('SET C[%d].Z[%d].%s="%s"\r' % c, z, cmd, value)

    def send_event(self, c, z, cmd, value1=None, value2=None):
        self.send_cmd('EVENT C[%d].Z[%d]!%s %s %s\r' % c, z, cmd, value)
        
    def _watch_zone(self, controller, zone, value):
        self.send_cmd('WATCH C[%d].Z[%d] %s\r' % controller, zone, 'ON' if value else 'OFF')

    def _watch_system(self, value):
        self.send_cmd('WATCH System %s\r' % 'ON' if value else 'OFF')

    def _send_cmd(self, cmd):
        logger.debug("Request: %s" % cmd)
        self.push(cmd)

    def _parse_response(self, resp):
        if resp[0] == 'S':
            return 
        if resp[0] == 'E':
            logger.debug("Response error: %s" %s resp)
        elif resp[0] == 'N':
            resp = resp[2:]

            if resp[0] == 'C':
                c = int(resp[2])
                z = int(resp[6])
                resp = resp[10:]
                cmd = resp.split('=')[0]
                value = resp.split('"')[1]

                path = c + '.' + z + '.' + cmd
                if path in self.params.keys():
                    self.params[path].item(self._decode(cmd, value), 'Russound')
            elif resp.startswith('System.status'):
                return
            elif resp[0] == 'S':
                return

    def _decode(self, cmd, value):
        cmd = cmd.tolower()

        if cmd == 'bass' or cmd == 'treble' or cmd == 'balance':
            return round(value * (128 / 10))
        elif cmd == 'loudness' or cmd == 'status' or cmd == 'mute':
            return value == 'ON')
        elif cmd == 'turnonvolume' or cmd == 'volume':
            return round(value * (255 / 50))
        elif cmd == 'partymode' or cmd == 'donotdisturb':
            return value.tolower()
        elif cmd == 'currentsource':
            return value 

    def found_terminator(self):
        data = self.buffer
        self.buffer = ''
        self._parse_response(data)

    def run(self):
        self.alive = True
        self._watch_system(True)

        for p in self.params:
            self._watch_zone(p.c, p.z, True)
            
    def stop(self):
        self.alive = False
        self._watch_system(False)

        for p in self.params:
            self._watch_zone(p.c, p.z, False)

        self.handle_close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    myplugin = Russound('smarthome-dummy')
    myplugin.run()
