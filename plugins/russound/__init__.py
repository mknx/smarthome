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

REQ_DELIMITER = '\r'
RESP_DELIMITER = '\r\n'

class Russound(asynchat.async_chat):

    lock = threading.Condition()
    buffer = ''
    resp = None

    def __init__(self, smarthome):
        asynchat.async_chat.__init__(self, maü=self.socket_map)
        logger.info('Starting russound')
        self._sh = smarthome
        self.all_zones = {}
        self.controller = {}
        self.set_terminator(RESP_DELIMITER)

        if 'russound' not in smarthome:
            logger.warning("No russound configuration found!")
            return None

        for zone in smarthome['russound']:
            self.all_zones[zone] = RussoundZone(smarthome, zone)
            self.controller[zone.controller][zone.zone] = zone

    def parse_item(self, item):
        if item.parent in self.all_zones.keys():
            return self.all_zones[item.parent].update_item
        else:
            return None

    def send_set(self, zone, cmd, value):
        self.send_cmd('SET C[%d].Z[%d].%s="%s"\r' % zone.controller, zone.zone, cmd, value)

    def send_event(self, zone, cmd, value1=None, value2=None):
        self.send_cmd('EVENT C[%d].Z[%d]!%s %s %s\r' % zone.controller, zone.zone, cmd, value)
        
    def watch_zone(self, controller, zone, value):
        self.send_cmd('WATCH C[%d].Z[%d] %s\r' % controller, zone, 'ON' if value else 'OFF')

    def watch_system(self, value):
        self.send_cmd('WATCH System %s\r' % 'ON' if value else 'OFF')

    def send_cmd(self, cmd):
        logger.debug("Request: %s" % cmd)
        self.lock.acquire()
        self.resp = None
        self.push(cmd)
        self.lock.wait(0.5)
        resp = self.resp
        self.lock.release()
        logger.debug("Response: %s" % resp)
        return resp

    def _handle_response(self, resp):
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
                
                self.controllers[c][z].item[cmd](value, 'RUSSOUND')
            elif resp.startswith('System.status'):
                return
            elif resp[0] == 'S':
                return


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
        self.watch_system(True)

        for c in self.controllers:
            for z in self.controllers[c]:
                self.watch_zone(c, z, True)
            
        while self.alive:
            if self.connected:
                asyncore.loop(timeout=1, count=1, map=self.socket_map)
            else:
                self._connect()

    def stop(self):
        self.alive = False
        self.watch_system(False)

        for c in self.controllers:
            for z in self.controllers[c]:
                self.watch_zone(c, z, False)

        asyncore.close_all(map=self.socket_map)
        self.close()

    def parse_logic(self, logic):
        pass


class RussoundZone:
    def __init__(self, smarthome, russound, item):
        self._sh = smarthome
        self.russound = russound
        self.controller = config['controller']
        self.zone = config['zone']
        self._item = item

    def update_item(self, item, caller=None, source=None):
        if caller != 'RUSSOUND':
            cmd = item.id().split('.')[-1]

            if cmd == 'bass':
                self.russound.send_set(self, cmd, round(item() / (128 / 10)))
            elif cmd == 'treble':
                self.russound.send_set(self, cmd, round(item() / (128 / 10)))
            elif cmd == 'balance':
                self.russound.send_set(self, cmd, round(item() / (128 / 10)))
            elif cmd == 'loudness':
                self.russound.send_set(self, cmd, 'ON' if item() else 'OFF')
            elif cmd == 'turnOnVolume':
                self.russound.send_set(self, cmd, round(item() / (255 / 50)))
            elif cmd == 'power':
                self.russound.send_event(self, 'ZoneOn' if item() else 'ZoneOff')
            elif cmd == 'partyMode':
                self.russound.send_event(self, 'PartyMode', item().tolower())
            elif cmd == 'doNotDisturb':
                self.russound.send_event(self, 'DoNotDisturb', 'on' if item() else 'off')
            elif cmd == 'volume':
                self.russound.send_event(self, 'KeyPress', 'Volume', round(item() / (255 / 50)))
            elif cmd == 'currentSource':
                self.russound.send_event(self, 'SelectSource', item())
            elif cmd == 'mute':
                if item():
                    self.russound.send_event(self, 'KeyRelease', 'Mute')
                else:
                    self.russound.send_event(self, 'KeyPress', 'Volume', round(self.item.volume() / (255 / 50)))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    myplugin = Russound('smarthome-dummy')
    myplugin.run()
