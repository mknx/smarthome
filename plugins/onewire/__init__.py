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


class OwBase():

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
            self._sock.settimeout(2)
            self._sock.connect((self.host, self.port))
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

    def write(self, path, value):
        return self._request(path, cmd=3, value=value)

    def dir(self, path='/'):
        return self._request(path, cmd=9).strip('\x00').split(',')

    def tree(self, path='/'):
        try:
            items = self.dir(path)
        except Exception:
            return
        for item in items:
            print item
            if item.endswith('/'):
                self.tree(item)

    def _request(self, path, cmd=10, value=None):
        if value is not None:
            payload = path + '\x00' + str(value) + '\x00'
            data = len(str(value)) + 1
        else:
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
            if len(header) != 24:
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
        if header['payload'] == 0:
            self._lock.release()
            if cmd != 3:
                raise owex('no payload for {0}'.format(path))
            return
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
        return payload.strip()

    def close(self):
        self.is_connected = False
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            self._sock = False
        except:
            pass

    def identify_sensor(self, path):
        try:
            typ = self.read(path + 'type')
        except Exception:
            return
        addr = path.split("/")[-2]
        if typ == 'DS18B20':  # Temperature
            return {'T': 'temperature', 'T9': 'temperature9', 'T10': 'temperature10', 'T11': 'temperature11', 'T12': 'temperature12'}
        elif typ == 'DS2438':  # Multi
            try:
                page3 = self.read(path + 'pages/page.3').encode('hex').upper()
            except Exception:
                return
            try:
                vis = float(self.read(path + 'vis'))
            except Exception:
                vis = 0
            if vis > 0:
                keys = {'T': 'temperature', 'H': 'HIH4000/humidity', 'L': 'vis'}
            else:
                keys = {'T': 'temperature', 'H': 'HIH4000/humidity'}
            try:
                vdd = float(self.read(path + 'VDD'))
            except Exception:
                vdd = None
            if vdd is not None:
                logger.debug("1-Wire: sensor {0} voltage: {1}".format(addr, vdd))
                keys['VDD'] = 'VDD'
            if page3[:2] == '19':
                return keys
            elif page3[:2] == 'F2':  # BMS
                return keys
            elif page3[:2] == 'F3':  # AMSv2 TH
                return keys
            elif page3[:2] == 'F4':  # AMSv2 V
                return {'V': 'VAD'}
            elif page3 == '48554D4944495433':  # DataNab
                keys['H'] = 'humidity'
                return keys
            else:
                logger.info("1-Wire: unknown sensor {0} {1} page3: {2}".format(addr, typ, page3))
                keys.update({'V': 'VAD', 'VDD': 'VDD'})
                return keys
        elif typ == 'DS2401':  # iButton
            return {'B': 'iButton'}
        elif typ in ['DS2413', 'DS2406']:  # I/O
            return {'IA': 'sensed.A', 'IB': 'sensed.B', 'OA': 'PIO.A', 'OB': 'PIO.B'}
        elif typ == 'DS1420':  # Busmaster
            return {'BM': 'Busmaster'}
        else:
            logger.info("1-Wire: unknown sensor {0} {1}".format(addr, typ))
            return


class OneWire(OwBase):
    _buses = {}
    _sensors = {}
    _ios = {}
    _ibuttons = {}
    _ibutton_buses = {}
    _ibutton_masters = {}
    _intruders = []
    alive = True
    _discovered = False
    _flip = {0: '1', False: '1', 1: '0', True: '0', '0': True, '1': False}
    _supported = {'T': 'Temperature', 'H': 'Humidity', 'V': 'Voltage', 'BM': 'Busmaster', 'B': 'iButton', 'L': 'Light/Lux', 'IA': 'Input A', 'IB': 'Input B', 'OA': 'Output A', 'OB': 'Output B', 'T9': 'Temperature 9Bit', 'T10': 'Temperature 10Bit', 'T11': 'Temperature 11Bit', 'T12': 'Temperature 12Bit'}

    def __init__(self, smarthome, cycle=300, io_wait=5, button_wait=0.5, host='127.0.0.1', port=4304):
        OwBase.__init__(self, host, port)
        self._sh = smarthome
        self._io_wait = float(io_wait)
        self._button_wait = float(button_wait)
        self._cycle = int(cycle)
        self.connect()

    def wrapper(self, bus):  # dummy method not needed right now
        import types

        def method(bus):
            self._sensor_cycle(bus)
        return types.MethodType(method, bus)

    def run(self):
        self.alive = True
        self._sh.scheduler.add('1w-disc', self._discovery, prio=5, cycle=600, offset=0)
        while self.alive:  # wait for first discovery to finish
            time.sleep(0.5)
            if self._discovered:
                break
        if not self._discovered:
            return
        self._sh.scheduler.add('1w-sen', self._sensor_cycle, cycle=self._cycle, prio=5, offset=0)
        #self._sh.scheduler.add('1w', self.wrapper('bus.1'), cycle=self._cycle, prio=5, offset=4)
        if self._ibuttons != {} and self._ibutton_masters == {}:
            logger.debug("1-Wire: iButtons but no iButton Masters... moving to IOs")
            for addr in self._ibuttons:
                for key in self._ibuttons[addr]:
                    if key == 'B':
                        if addr in self._ios:
                            self._ios[addr][key] = {'item': self._ibuttons[addr][key]['item'], 'path': '/' + addr}
                        else:
                            self._ios[addr] = {key: {'item': self._ibuttons[addr][key]['item'], 'path': '/' + addr}}
            self._ibuttons = {}
        if self._ibutton_masters == {} and self._ios == {}:
            return
        elif self._ibutton_masters != {} and self._ios != {}:
            self._sh.scheduler.trigger('1w-io', self._io_loop, '1w', prio=5)
            self._ibutton_loop()
        elif self._ios != {}:
            self._io_loop()
        elif self._ibutton_masters != {}:
            self._ibutton_loop()

    def stop(self):
        self.alive = False

    def _io_loop(self):
        threading.currentThread().name = '1w-io'
        logger.debug("Starting I/O detection")
        while self.alive:
            # start = time.time()
            self._io_cycle()
            # cycletime = time.time() - start
            # logger.debug("cycle takes {0} seconds".format(cycletime))
            time.sleep(self._io_wait)

    def _io_cycle(self):
        if not self.is_connected:
            return
        for addr in self._ios:
            for key in self._ios[addr]:
                if key.startswith('O'):  # ignore Output
                    continue
                item = self._ios[addr][key]['item']
                path = self._ios[addr][key]['path']
                if path is None:
                    logger.debug("1-Wire: no path found for {0}".format(item.id()))
                    continue
                try:
                    if key == 'B':
                        entries = [entry.split("/")[-2] for entry in self.dir('/uncached')]
                        value = (addr in entries)
                    else:
                        value = self._flip[self.read('/uncached' + path)]
                except Exception:
                    logger.warning("1-Wire: problem reading {0}".format(addr))
                    continue
                item(value, '1-Wire', path)

    def _ibutton_loop(self):
        threading.currentThread().name = '1w-b'
        logger.debug("Starting iButton detection")
        while self.alive:
            self._ibutton_cycle()
            time.sleep(self._button_wait)

    def _ibutton_cycle(self):
        found = []
        error = False
        if not self.is_connected:
            return
        for bus in self._ibutton_buses:
            path = '/uncached/' + bus + '/'
            name = self._ibutton_buses[bus]
            ignore = ['interface', 'simultaneous', 'alarm'] + self._intruders + self._ibutton_masters.keys()
            try:
                entries = self.dir(path)
            except Exception:
                time.sleep(0.5)
                error = True
                continue
            for entry in entries:
                entry = entry.split("/")[-2]
                if entry in self._ibuttons:
                    found.append(entry)
                    self._ibuttons[entry]['B']['item'](True, '1-Wire', source=name)
                elif entry in ignore:
                    pass
                else:
                    self._intruders.append(entry)
                    self.ibutton_hook(entry, name)
        if not error:
            for ibutton in self._ibuttons:
                if ibutton not in found:
                    self._ibuttons[ibutton]['B']['item'](False, '1-Wire')

    def ibutton_hook(self, ibutton, name):
        pass

    def _sensor_cycle(self):
        if not self.is_connected:
            return
        start = time.time()
        for addr in self._sensors:
            for key in self._sensors[addr]:
                item = self._sensors[addr][key]['item']
                path = self._sensors[addr][key]['path']
                if path is None:
                    logger.debug("1-Wire: no path found for {0}".format(item.id()))
                    continue
                try:
                    value = self.read('/uncached' + path)
                except Exception:
                    logger.info("1-Wire: problem reading {0}".format(addr))
                    continue
                if key == 'L':  # light lux conversion
                    if value > 0:
                        value = round(10 ** ((float(value) / 47) * 1000))
                    else:
                        value = 0
                if key.startswith('T') and value == '85':
                    logger.info("1-Wire: problem reading {0}. Wiring problem?".format(addr))
                    continue
                item(value, '1-Wire', path)
        cycletime = time.time() - start
        logger.debug("cycle takes {0} seconds".format(cycletime))

    def _discovery(self):
        self._intruders = []  # reset intrusion detection
        if not self.is_connected:
            return
        try:
            listing = self.dir('/')
        except Exception:
            return
        if type(listing) != list:
            logger.warning("1-Wire: listing '{0}' is not a list.".format(listing))
            return
        for path in listing:
            if path.startswith('/bus.'):
                bus = path.split("/")[-2]
                if bus not in self._buses:
                    self._buses[bus] = []
                for sensor in self.dir(path):
                    addr = sensor.split("/")[-2]
                    if addr not in self._buses[bus]:
                        keys = self.identify_sensor(sensor)
                        if keys is None:
                            continue
                        self._buses[bus].append(addr)
                        logger.info("1-Wire: {0} with sensors: {1}".format(addr, ', '.join(keys.keys())))
                        if 'IA' in keys or 'IB' in keys:
                            table = self._ios
                        elif 'BM' in keys:
                            if addr in self._ibutton_masters:
                                self._ibutton_buses[bus] = self._ibutton_masters[addr]
                            continue
                        else:
                            table = self._sensors
                        if addr in table:
                            for ch in ['A', 'B']:
                                if 'I' + ch in table[addr] and 'O' + ch in keys:  # set to 0 and delete output PIO
                                    self.write(sensor + keys['O' + ch], 0)
                                    del(keys['O' + ch])
                            for key in keys:
                                if key in table[addr]:
                                    table[addr][key]['path'] = sensor + keys[key]
                            for ch in ['A', 'B']:  # init PIO
                                if 'O' + ch in table[addr]:
                                    self.write(table[addr][key]['path'], self._flip[table[addr][key]['item']()])
        self._discovered = True

    def parse_item(self, item):
        if 'ow_addr' not in item.conf:
            return
        if 'ow_sensor' not in item.conf:
            logger.warning(u"No ow_sensor for %s defined".format(item))
            return
        addr = item.conf['ow_addr']
        key = item.conf['ow_sensor']
        if key in ['IA', 'IB', 'OA', 'OB']:
            table = self._ios
        elif key == 'B':
            table = self._ibuttons
        elif key == 'BM':
            self._ibutton_masters[addr] = item.id()
            return
        else:
            table = self._sensors
        if key not in self._supported:  # unknown key
            path = '/' + addr + '/' + key
            logger.info("1-Wire: unknown sensor specified for {0} using path: {1}".format(item.id(), path))
        else:
            path = None
        if addr in table:
            table[addr][key] = {'item': item, 'path': path}
        else:
            table[addr] = {key: {'item': item, 'path': path}}
        if key.startswith('O'):
            item._ow_path = table[addr][key]
            return self.update_item

    def update_item(self, item, caller=None, source=None, dest=None):
        self.write(item._ow_path['path'], self._flip[item()])
