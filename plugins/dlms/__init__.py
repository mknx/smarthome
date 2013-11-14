#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2011 KNX-User-Forum e.V.           http://knx-user-forum.de/
#########################################################################
#  DLMS plugin for SmartHome.py.         http://mknx.github.io/smarthome/
#
#  This plugin is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This plugin is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this plugin. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import time
import serial
import re

logger = logging.getLogger('DLMS')


class DLMS():

    def __init__(self, smarthome, serialport, baudrate="auto", update_cycle="60"):
        self._sh = smarthome
        self._update_cycle = int(update_cycle)
        if (baudrate.lower() == 'auto'):
            self._baudrate = -1
        else:
            self._baudrate = int(baudrate)
        self._obis_codes = {}
        self._serial = serial.Serial(
            serialport, 300, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, timeout=2)
        self._request = bytearray('\x06000\r\n', 'ascii')

    def run(self):
        self.alive = True
        self._sh.scheduler.add('DLMS', self._update_values,
                               prio=5, cycle=self._update_cycle)

    def stop(self):
        self.alive = False
        self._serial.close()
        self._sh.scheduler.remove('DLMS')

    def _update_values(self):
        logger.debug("dlms: update")
        start = time.time()
        init_seq = bytes('/?!\r\n', 'ascii')
        self._serial.flushInput()
        self._serial.write(init_seq)
        response = bytes()
        prev_length = 0
        try:
            while self.alive:
                response += self._serial.read()
                length = len(response)
                # break if timeout or newline-character
                if (length == prev_length) or ((length > len(init_seq)) and (response[-1] == 0x0a)):
                    break
                prev_length = length
        except Exception as e:
            logger.warning("dlms: {0}".format(e))
        # remove echoed chars if present
        if (init_seq == response[:len(init_seq)]):
            response = response[len(init_seq):]
        if (len(response) >= 5) and ((response[4] - 0x30) in range(6)):
            if (self._baudrate == -1):
                baud_capable = 300 * (1 << (response[4] - 0x30))
            else:
                baud_capable = self._baudrate
            if baud_capable > self._serial.baudrate:
                try:
                    logger.debug(
                        "dlms: meter returned capability for higher baudrate {}".format(baud_capable))
                    # change request to set higher baudrate
                    self._request[2] = response[4]
                    self._serial.write(self._request)
                    logger.debug("dlms: trying to switch baudrate")
                    switch_start = time.time()
                    # Alt1:
                    #self._serial.baudrate = baud_capable
                    # Alt2:
                    #settings = self._serial.getSettingsDict()
                    #settings['baudrate'] = baud_capable
                    # self._serial.applySettingsDict(settings)
                    # Alt3:
                    port = self._serial.port
                    self._serial.close()
                    del self._serial
                    logger.debug("dlms: socket closed - creating new one")
                    self._serial = serial.Serial(
                        port, baud_capable, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, timeout=2)
                    logger.debug(
                        "dlms: Switching took: {:.2f}s".format(time.time() - switch_start))
                    logger.debug("dlms: switch done")
                except Exception as e:
                    logger.warning("dlms: {0}".format(e))
                    return
            else:
                self._serial.write(self._request)
        response = bytes()
        prev_length = 0
        try:
            while self.alive:
                response += self._serial.read()
                length = len(response)
                # break if timeout or "ETX"
                if (length == prev_length) or ((length >= 2) and (response[-2] == 0x03)):
                    break
                prev_length = length
        except Exception as e:
            logger.warning("dlms: {0}".format(e))
        logger.debug("dlms: Reading took: {:.2f}s".format(time.time() - start))
        # remove echoed chars if present
        if (self._request == response[:len(self._request)]):
            response = response[len(self._request):]
        # perform checks (start with STX, end with ETX, checksum match)
        checksum = 0
        for i in response[1:]:
            checksum ^= i
        if (len(response) < 5) or (response[0] != 0x02) or (response[-2] != 0x03) or (checksum != 0x00):
            logger.warning(
                "dlms: checksum/protocol error: response={} checksum={}".format(' '.join(hex(i) for i in response), checksum))
            return
        #print(str(response[1:-4], 'ascii'))
        for line in re.split('\r\n', str(response[1:-4], 'ascii')):
            # if re.match('[0-9]+\.[0-9]\.[0-9](.+)', line): # allows only
            # x.y.z(foo)
            if re.match('[0-9]+\.[0-9].+(.+)', line):  # allows also x.y(foo)
                try:
                    #data = re.split('[(*)]', line)
                    data = line.split('(')
                    data[1:3] = data[1].strip(')').split('*')
                    if (len(data) == 2):
                        logger.debug("dlms: {} = {}".format(data[0], data[1]))
                    else:
                        logger.debug(
                            "dlms: {} = {} {}".format(data[0], data[1], data[2]))
                    if data[0] in self._obis_codes:
                        for item in self._obis_codes[data[0]]['items']:
                            item(data[1], 'DLMS', 'OBIS {}'.format(data[0]))
                except Exception as e:
                    logger.warning(
                        "dlms: line={} exception={}".format(line, e))

    def parse_item(self, item):
        if 'dlms_obis_code' in item.conf:
            logger.debug("parse item: {0}".format(item))
            obis_code = item.conf['dlms_obis_code']
            if not obis_code in self._obis_codes:
                self._obis_codes[obis_code] = {'items': [item], 'logics': []}
            else:
                self._obis_codes[obis_code]['items'].append(item)
        return None
