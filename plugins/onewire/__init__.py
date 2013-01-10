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

import logging
import socket
import threading
import struct
import time

logger = logging.getLogger('')


class owex(Exception):
    pass


class owexpath(Exception):
    pass


class Owconnection():

    def __init__(self, host='127.0.0.1', port=4304):
        self.host = host
        self.port = int(port)
        self._sock = False
        self._lock = threading.Lock()
        self._flag = 0x00000100   # ownet
        self._flag += 0x00000004  # persistence
        self._flag += 0x00000002  # list special directories
        self.is_connected = False
        self._connection_attempts = 0
        self._connection_errorlog = 60

    def connect(self):
        self._lock.acquire()
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self.host, self.port))
            self._sock.settimeout(2)
        except Exception, e:
            self._connection_attempts -= 1
            if self._connection_attempts <= 0:
                logger.error('Onewire: could not connect to {0}:{1}: {2}'.format(self.host, self.port, e))
                self._connection_attempts = self._connection_errorlog
            return
        finally:
            self._lock.release()
        logger.info('Onewire: connected to {0}:{1}'.format(self.host, self.port))
        self.is_connected = True
        self._connection_attempts = 0
        try:
            self.read('/system/process/pid')  # workaround read to avoid owserver timeout
        except Exception, e:
            pass

    def read(self, path):
        return self._request(path, cmd=2)

    def dir(self, path='/'):
        return self._request(path, cmd=9)

    def write(self, path, value):
        return self._request(path, cmd=3)

    def _request(self, path, cmd=10, value=None):
        payload = path + '\x00'
        data = 65536
        header = struct.pack('IIIIII',
            socket.htonl(0),             # version
            socket.htonl(len(payload)),  # payload length
            socket.htonl(cmd),           # message type
            socket.htonl(self._flag),    # format flags -- 266 for alias upport
            socket.htonl(data),          # size of data element for read or write
            socket.htonl(0)              # offset for read or write
        )
        if not self.is_connected:
            raise owex("No connection to owserver.")

        self._lock.acquire()
        try:
            self._sock.sendall(header + payload)
        except Exception, e:
            self._lock.release()
            self.close()
            raise owex("error sending request: {0}".format(e))

        while True:  # ignore ping packets
            try:
                header = self._sock.recv(24)
            except socket.timeout:
                self._lock.release()
                raise owex("error receiving header: timeout")
            except Exception, e:
                self._lock.release()
                self.close()
                raise owex("error receiving header: {0}".format(e))
            if len(header) == 0:
                self._lock.release()
                self.close()
                raise owex("error receiving header: no data")
            header = struct.unpack('IIIIII', header)
            header = map(socket.ntohl, header)
            fields = ['version', 'payload', 'ret', 'flags', 'size', 'offset']
            header = dict(zip(fields, header))

            if not header['payload'] == 4294967295:
                break

        if header['ret'] == 4294967295:  # unknown path
            self._lock.release()
            raise owexpath("path '{0}' not found.".format(path))
            #raise owex("error: unknown path {0}".format(path))

        if header['payload'] == 0:
            self._lock.release()
            raise owex('no payload for {0}'.format(path))

        try:
            payload = self._sock.recv(header['payload'])
        except socket.timeout:
            self._lock.release()
            raise owex("error receiving payload: timeout")
        except Exception, e:
            self._lock.release()
            self.close()
            raise owex("error receiving payload: {0}".format(e))

        self._lock.release()

        if payload.startswith('/'):
            return payload.strip('\x00').split(',')
        else:
            payload = payload.strip()
            if payload.replace('.', '').lstrip('-').isdigit():
                return float(payload)
            else:
                return payload

    def tree(self, path='/'):
        try:
            items = self.dir(path)
        except Exception, e:
            return
        for item in items:
            print item
            if item.endswith('/'):
                self.tree(item)

    def close(self):
        self.is_connected = False
        try:
            self._sock.close()
            self._sock = False
        except:
            pass


class OneWire(Owconnection):
    _buses = []
    _sensors = {}
    _ibuttons = {}
    _ibutton_buses = {}
    _ibutton_masters = {}
    _intruders = []
    alive = True

    def __init__(self, smarthome, cycle=300, host='127.0.0.1', port=4304):
        Owconnection.__init__(self, host, port)
        self._sh = smarthome
        smarthome.monitor_connection(self)
        self._cycle = int(cycle)

    def run(self):
        self.alive = True
        self._sh.scheduler.add('ow.bus', self._busmaster_discovery, prio=5, cycle=600, offset=1)
        self._sh.scheduler.add('ow', self._sensor_cycle, cycle=self._cycle, prio=5, offset=4)
        if self._ibutton_masters != {}:
            self._ibutton_loop()

    def stop(self):
        self.alive = False

    def _busmaster_discovery(self):
        self._intruders = []  # reset intrusion detection
        if not self.is_connected:
            return
        try:
            listing = self.dir('/')
        except Exception, e:
            return
        if type(listing) != list:
            logger.warning("OneWire: listing '{0}' is not a list.".format(listing))
            return
        for path in listing:
            if path.startswith('/bus.'):
                bus = path.split("/")[-2]
                if bus not in self._buses:
                    try:
                        busmaster = self._bus_master(path)
                    except Exception, e:
                        continue
                    if busmaster in self._ibutton_masters:
                        logger.info("Found {0} with ibutton busmaster {1}".format(bus, busmaster))
                        self._ibutton_buses[bus] = self._ibutton_masters[busmaster]
                    else:
                        logger.info("Found {0} with busmaster {1}".format(bus, busmaster))
                    self._buses.append(bus)

    def _bus_master(self, path='/bus.0'):
        for sensor in self.dir(path):
            try:
                sensor_type = self.read(sensor + 'type')
            except:
                pass
            else:
                if sensor_type in ['DS1420']:
                    return sensor.split("/")[-2]

    def _sensor_cycle(self):
        if not self.is_connected:
            return
        for sensor in self._sensors:
            typ = self._sensors[sensor]['sensor']
            path = "/" + sensor + '/' + typ
            item = self._sensors[sensor]['item']
            try:
                value = self.read(path)
            except Exception, e:
                logger.info("Could not read {0} ({1}): {2}".format(item, sensor, e))
                if self.is_connected:
                    continue
                else:
                    break
            if type(value) != float:
                logger.warning("OneWire: value {0} for {1} is not a float.".format(repr(value), path))
                continue
            if typ.startswith('temperature'):
                value = round(value, 1)
            elif typ == 'humidity':
                value = round(value)
            self._sensors[sensor]['item'](value, '1-Wire')

    def _ibutton_loop(self):
        threading.currentThread().name = 'iButton'
        logger.debug("Starting iButton detection")
        cycle = 0.3
        while self.alive:
            found = []
            error = False
            for bus in self._ibutton_buses:
                path = '/uncached/' + bus + '/'
                ignore = ['interface', 'simultaneous', 'alarm'] + self._intruders + self._ibutton_masters.keys()
                try:
                    sensors = self.dir(path)
                except Exception, e:
                    time.sleep(cycle)
                    error = True
                    continue
                name = self._ibutton_buses[bus]
                for sensor in sensors:
                    sensor = sensor.split("/")[-2]
                    if sensor in self._ibuttons:
                        found.append(sensor)
                        self._ibuttons[sensor](True, '1-Wire', source=name)
                    elif sensor in ignore:
                        pass
                    else:
                        self._intruders.append(sensor)
                        self.ibutton_hook(sensor, name)

            if not error:
                for ibutton in self._ibuttons:
                    if ibutton not in found:
                        self._ibuttons[ibutton](False, '1-Wire')
            time.sleep(cycle)

    def ibutton_hook(self, ibutton, name):
        pass

    def parse_item(self, item):
        if 'ow_id' not in item.conf:
            return
        elif 'ow_sensor' not in item.conf:
            logger.warning(u"No ow_sensor for %s defined".format(item))
            return
        ow_id = item.conf['ow_id']
        ow_sensor = item.conf['ow_sensor']
        if ow_sensor == 'ibutton':
            self._ibuttons[ow_id] = item
        elif ow_sensor == 'ibutton_master':
            self._ibutton_masters[ow_id] = item
        else:
            self._sensors[ow_id] = {'sensor': ow_sensor, 'item': item}
