#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 Robert Budde                        robert@projekt131.de
#########################################################################
#  This software is based on Stuart Pittaway's "NANODE SMA PV MONITOR"
#  https://github.com/stuartpittaway/nanodesmapvmonitor
#
#  SMA-Plugin for SmartHome.py.   http://mknx.github.com/smarthome/
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

from bluetooth import *
import struct
import logging
import time
from datetime import datetime
from dateutil import tz

BCAST_ADDR = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
ZERO_ADDR = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

SMANET2_HDR = [0x7E, 0xFF, 0x03, 0x60, 0x65]

FCSTAB = [
    0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
    0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
    0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
    0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
    0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
    0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
    0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
    0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
    0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
    0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
    0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
    0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
    0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
    0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
    0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
    0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
    0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
    0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
    0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
    0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
    0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
    0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
    0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
    0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
    0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
    0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
    0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
    0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
    0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
    0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
    0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
    0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78,
    ]

# Start-Address, End-Address, ?, (Länge der einzelnen Datenfelder?)
TOTAL_YIELD = (0x2601, 0x2601, 0xA009, [0x80, 0x00, 0x02, 0x00, 0x54])
DAY_YIELD = (0x2622, 0x2622, 0xA009, [0x80, 0x00, 0x02, 0x00, 0x54])
AC_POWER = (0x263F, 0x263F, 0xA109, [0x80, 0x00, 0x02, 0x00, 0x51], 0x0E)
# works as well!!?? AC_POWER    = (0x263F, 0x263F, 0xA109, [0x80,0x00,0x02,0x00,0x51])
DC_POWER = (0x2500, 0x25FF, 0xE009, [0x83, 0x00, 0x02, 0x80, 0x53])
DC_VOLTAMPS = (0x4500, 0x45FF, 0xE009, [0x83, 0x00, 0x02, 0x80, 0x53])
AC_DATA = (0x2000, 0x50FF, 0xA109, [0x80, 0x00, 0x02, 0x00, 0x51], 0x0E)

# works but unknown response
AC_DATA2 = (0x2000, 0x50FF, 0xA009, [0x80, 0x00, 0x02, 0x80, 0x51])
#2013-06-15 21:31:40,713 sma.update   DEBUG    sma: value_code=0x2148 / value=35 -- __init__.py:_inv_get_value:537
#2013-06-15 21:31:40,714 sma.update   DEBUG    sma: value_code=0x4132 / value=303 -- __init__.py:_inv_get_value:537
#2013-06-15 21:31:40,714 sma.update   DEBUG    sma: value_code=0x4133 / value=303 -- __init__.py:_inv_get_value:537
#2013-06-15 21:31:40,715 sma.update   DEBUG    sma: value_code=0x4149 / value=302 -- __init__.py:_inv_get_value:537
#2013-06-15 21:31:40,715 sma.update   DEBUG    sma: value_code=0x414a / value=336 -- __init__.py:_inv_get_value:537
#2013-06-15 21:31:40,716 sma.update   DEBUG    sma: value_code=0x414b / value=302 -- __init__.py:_inv_get_value:537
#2013-06-15 21:31:40,716 sma.update   DEBUG    sma: value_code=0x4164 / value=51 -- __init__.py:_inv_get_value:537
#2013-06-15 21:31:40,717 sma.update   DEBUG    sma: value_code=0x4165 / value=557 -- __init__.py:_inv_get_value:537

logger = logging.getLogger('SMA')


class SMA():

    def __init__(self, smarthome, bt_addr, password="0000", update_cycle="60"):
        self._sh = smarthome
        self._val = {}
        self._inv_bt_addr = bt_addr
        self._inv_password = password
        self._inv_last_read_datetime = datetime.fromtimestamp(0, tz.tzlocal())
        self._inv_last_read = self._inv_last_read_datetime.strftime("%d.%m.%Y %H:%M:%S")
        self._inv_serial = 0
        self._own_bt_addr_le = BCAST_ADDR
        self._btsocket = BluetoothSocket(RFCOMM)
        if not (is_valid_address(self._inv_bt_addr)):
            logger.warning("sma: inverter bluetooth address is invalid: %s" % self._inv_bt_addr)
            return
        self._inv_bt_name = lookup_name(self._inv_bt_addr, timeout=8)
        if (self._inv_bt_name == None):
            logger.warning("sma: inverter bluetooth name could not be looked up")
            self._inv_bt_name = "unknown"

        self._btsocket.connect((self._inv_bt_addr, 1))

        logger.debug("sma: via bluetooth connected to %s (%s)" % (self._inv_bt_name, self._inv_bt_addr))
        self._inv_connect()
        self._inv_login()
        self._sh.scheduler.add('sma.update', self._update_values, prio=5, cycle=int(update_cycle))

    def _update_values(self):
        #logger.warning("sma: signal strength = %d%%" % self._inv_get_bt_signal_strength())

        data = self._inv_get_value(TOTAL_YIELD)
        if (data != []):
            self._inv_last_read_timestamp_utc = data[0][1]
            logger.debug("sma: total yield = %dWh" % data[0][2])
            if 'TOTAL_YIELD' in self._val:
                for item in self._val['TOTAL_YIELD']['items']:
                    item(data[0][2], 'SMA', self._inv_bt_addr)
        else:
            logger.warning("sma: could not read total yield!")

        data = self._inv_get_value(DAY_YIELD)
        if (data != []):
            self._inv_last_read_timestamp_utc = data[0][1]
            logger.debug("sma: day yield = %dWh" % data[0][2])
            if 'DAY_YIELD' in self._val:
                for item in self._val['DAY_YIELD']['items']:
                    item(data[0][2], 'SMA', self._inv_bt_addr)
        else:
            logger.warning("sma: could not read day yield!")

        data = self._inv_get_value(AC_POWER)
        if (data != []):
            self._inv_last_read_timestamp_utc = data[0][1]
            logger.debug("sma: current AC power = %dW" % data[0][2])
            if 'AC_POWER' in self._val:
                for item in self._val['AC_POWER']['items']:
                    item(data[0][2], 'SMA', self._inv_bt_addr)
        else:
            logger.warning("sma: could not read current AC power!")

        data = self._inv_get_value(DC_POWER)
        if (data != []):
            self._inv_last_read_timestamp_utc = data[0][1]
            logger.debug("sma: current DC power string 1 = %dW / string 2 = %dW" % (data[0][2], data[1][2]))
            if 'DC_POWER_STRING1' in self._val:
                for item in self._val['DC_POWER_STRING1']['items']:
                    item(data[0][2], 'SMA', self._inv_bt_addr)
            if 'DC_POWER_STRING2' in self._val:
                for item in self._val['DC_POWER_STRING2']['items']:
                    item(data[1][2], 'SMA', self._inv_bt_addr)
        else:
            logger.warning("sma: could not read current DC power!")

        data = self._inv_get_value(DC_VOLTAMPS)
        if (data != []):
            self._inv_last_read_timestamp_utc = data[0][1]
            string1_voltage = float(data[0][2]) / 100
            string1_current = float(data[2][2]) / 1000
            string2_voltage = float(data[1][2]) / 100
            string2_current = float(data[3][2]) / 1000
            logger.debug("sma: current DC voltage/currents string 1 = %.2fV/%.3fA / string 2 = %.2fV/%.3fA" % (string1_voltage, string1_current, string2_voltage, string2_current))
            if 'DC_VOLTAGE_STRING1' in self._val:
                for item in self._val['DC_VOLTAGE_STRING1']['items']:
                    item(string1_voltage, 'SMA', self._inv_bt_addr)
            if 'DC_CURRENT_STRING1' in self._val:
                for item in self._val['DC_CURRENT_STRING1']['items']:
                    item(string1_current, 'SMA', self._inv_bt_addr)
            if 'DC_VOLTAGE_STRING2' in self._val:
                for item in self._val['DC_VOLTAGE_STRING2']['items']:
                    item(string2_voltage, 'SMA', self._inv_bt_addr)
            if 'DC_CURRENT_STRING2' in self._val:
                for item in self._val['DC_CURRENT_STRING2']['items']:
                    item(string2_current, 'SMA', self._inv_bt_addr)
        else:
            logger.warning("sma: could not read current DC voltages/currents!")

        #data = self._inv_get_value(AC_DATA)

        # extract time(utc)
        self._inv_last_read_datetime = datetime.fromtimestamp(self._inv_last_read_timestamp_utc, tz.tzlocal())
        self._inv_last_read = self._inv_last_read_datetime.strftime("%d.%m.%Y %H:%M:%S")

        logger.debug("sma: last successful update = %s" % self._inv_last_read)
        if 'LAST_UPDATE' in self._val:
            for item in self._val['LAST_UPDATE']['items']:
                item(self._inv_last_read, 'SMA', self._inv_bt_addr)

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False
        try:
            self._btsocket.close()
            self._btsocket = False
        except:
            pass

    def parse_item(self, item):
        if 'sma' in item.conf:
            sma_value = item.conf['sma']
            logger.debug("sma: {0} connected to value of {1}".format(item, sma_value))
            if not sma_value in self._val:
                self._val[sma_value] = {'items': [item], 'logics': []}
            else:
                if not item in self._val[sma_value]['items']:
                    self._val[sma_value]['items'].append(item)

            if (sma_value == 'OWN_ADDRESS'):
                item(self._own_bt_addr, 'SMA', self._inv_bt_addr)
            if (sma_value == 'INV_ADDRESS'):
                item(self._inv_bt_addr, 'SMA', self._inv_bt_addr)
            if (sma_value == 'INV_SERIAL'):
                item(self._inv_serial, 'SMA', self._inv_bt_addr)

        # return None to indicate "read-only"
        return None

    # receive function for SMANET1 messages
    def _recv_smanet1_msg(self, timeout=1.0):
        try:
            # wait for sfd
            recv_char = 0
            self._btsocket.settimeout(timeout)
            while (recv_char != chr(0x7E)):
                recv_char = self._btsocket.recv(1)
            msg = [ord(recv_char)]

            # get level 1 length and validate
            while (len(msg) < 4):
                # receive at most only precisely the number of bytes that are missing for the next step (allow follow-up msgs))
                recv_char = self._btsocket.recv(4 - len(msg))
                msg += [ord(i) for i in recv_char]
            if ((msg[1] ^ msg[2] ^ msg[3]) != 0x7E):
                logger.warning("sma: rx: length fields invalid")
                return []
            length = (msg[2] << 8) + msg[1]
            if (length < 18):
                logger.warning("sma: rx: length to small: %d" % length)
                return []

            # get remaining bytes
            while (len(msg) < length):
                # receive at most only precisely the number of bytes that are missing for this msg (allow follow-up msgs))
                recv_char = self._btsocket.recv(length - len(msg))
                msg += [ord(i) for i in recv_char]

            # check src and dst addr and check
            if (msg[4:10] != self._inv_bt_addr_le):
                logger.warning("sma: rx: unknown src addr")
                return []
            if (msg[10:16] != self._own_bt_addr_le) and (msg[10:16] != ZERO_ADDR) and (msg[10:16] != BCAST_ADDR):
                logger.warning("sma: rx: wrong dst addr")
                return []

            #print "rx: SMANET1 msg: len=%d / data=[%s]" % (len(msg), ' '.join(['0x%02x' % b for b in msg]))
        except bluetooth.btcommon.BluetoothError:
            logger.warning("sma: rx: timeout exception - could not receive msg within %ds" % timeout)
            msg = []
        except:
            logger.warning("sma: rx: exception - %s" % sys.exc_info()[0])
            msg = []
        return msg

    def _recv_smanet2_msg(self, cmdcodes_expected=[0x0001]):
        retries = 10
        smanet2_msg = []
        while True:
            retries -= 1
            if (retries == 0):
                logger.warning("sma: recv smanet2 msg - retries used up!")
                return []
            smanet1_msg = self._recv_smanet1_msg()
            # get cmdcode
            if (smanet1_msg == []):
                break

            smanet2_msg += smanet1_msg[18::]

            cmdcode_recv = (smanet1_msg[17] << 8) + smanet1_msg[16]
            if (cmdcode_recv in cmdcodes_expected):
                break

        if (smanet2_msg[0:5] != SMANET2_HDR):
            logger.warning("sma: no SMANET2 msg")
            logger.warning("sma: recv: len=%d / data=[%s]" % (len(smanet2_msg), ' '.join(['0x%02x' % b for b in smanet2_msg])))
            return []

        # remove escape characters
        i = 0
        while (i < len(smanet2_msg)):
            if (smanet2_msg[i] == 0x7d):
                del smanet2_msg[i]
                smanet2_msg[i] ^= 0x20
            i += 1
        #logger.debug("sma: escape chars removed")
        crc = self._calc_crc16(smanet2_msg[1:-3])
        if (((crc >> 8) != smanet2_msg[-2]) or ((crc & 0xFF) != smanet2_msg[-3])):
            logger.warning("sma: crc: crc16 error - %04x" % crc)
            logger.warning("sma: crc: len=%d / data=[%s]" % (len(smanet2_msg), ' '.join(['0x%02x' % b for b in smanet2_msg])))
            return []

        #print "rx: SMANET2 msg: len=%d / data=[%s]\n" % (len(msg), ' '.join(['0x%02x' % b for b in msg]))
        return smanet2_msg

    def _recv_smanet1_msg_with_cmdcode(self, cmdcodes_expected=[0x0001]):
        retries = 3
        while True:
            retries -= 1
            if (retries == 0):
                logger.warning("sma: recv msg with cmdcode - retries used up!")
                return []
            msg = self._recv_smanet1_msg()
            # get cmdcode
            if (msg != []) and (((msg[17] << 8) + msg[16]) in cmdcodes_expected):
                break
        return msg

    def _send_msg(self, msg):
        if (len(msg) >= 0x3a):
            # calculate crc starting with byte 19 and append with LE byte-oder
            crc = self._calc_crc16(msg[19::])
            msg += [crc & 0xff, (crc >> 8) & 0xff]
            # add escape sequences starting with byte 19
            msg = msg[0:19] + self._add_escapes(msg[19::])
            # add msg delimiter
            msg += [0x7e]
        # set length fields - msg[1] is exact overall length, msg[3] = 0x73-msg[1]
        msg[1] = len(msg) & 0xff
        msg[2] = (len(msg) >> 8) & 0xff
        msg[3] = msg[1] ^ msg[2] ^ 0x7e
        #print "tx: len=%d %s\n" % (len(msg), ' '.join(['0x%02x' % b for b in msg]))
        send = ''.join(chr(i) for i in msg)
        self._btsocket.send(send)

    def _calc_crc16(self, msg):
        crc = 0xFFFF
        for i in msg:
            crc = (crc >> 8) ^ FCSTAB[(crc ^ i) & 0xFF]
        crc ^= 0xFFFF
        #print("crc16 = %x") % crc
        return crc

    def _add_escapes(self, msg):
        escaped = []
        for i in msg:
            if (i == 0x7d) or (i == 0x7e) or (i == 0x11) or (i == 0x12) or (i == 0x13):
                escaped += [0x7d, i ^ 0x20]
            else:
                escaped += [i]
        return escaped

    def _inv_connect(self):
        self._send_count = 0
        self._inv_bt_addr_le = [int(x, 16) for x in self._inv_bt_addr.split(':')]
        self._inv_bt_addr_le = self._inv_bt_addr_le[::-1]
        # receive broadcast-msg from inverter
        msg = self._recv_smanet1_msg_with_cmdcode([0x0002])

        # extract net-id from the 0x0002 msg
        self._net_id = msg[22]

        # reply with wildcard src addr
        msg[4:10] = ZERO_ADDR
        msg[10:16] = self._inv_bt_addr_le
        self._send_msg(msg)

        # receive msg from inverter
        msg = self._recv_smanet1_msg_with_cmdcode([0x000a])
        # receive msg from inverter
        msg = self._recv_smanet1_msg_with_cmdcode([0x0005, 0x000c])
        # receive msg from inverter
        msg = self._recv_smanet1_msg_with_cmdcode([0x0005])

        # extract own bluetooth addr
        self._own_bt_addr_le = msg[26:32]
        logger.debug("sma: own bluetooth address: %s" % ':'.join(['%02x' % b for b in self._own_bt_addr_le[::-1]]))

        # first SMA net2 msg
        retries = 10
        while (retries > 0):
            retries -= 1
            # level1
            cmdcode = 0x0001
            msg = [0x7E, 0, 0, 0] + self._own_bt_addr_le + self._inv_bt_addr_le + [cmdcode & 0xFF, (cmdcode >> 8) & 0xFF]
            # sma-net2 level
            ctrl = 0xA009
            self._send_count += 1
            if (self._send_count > 75):
                self._send_count = 1
            msg += SMANET2_HDR + [ctrl & 0xFF, (ctrl >> 8) & 0xFF] + BCAST_ADDR + [0x00, 0x00] + self._inv_bt_addr_le + [0x00] + [0x00] + [0, 0, 0, 0] + [self._send_count]
            msg += [0x80, 0x00, 0x02, 0x00] + [0x00] + [0x00, 0x00, 0x00, 0x00] + [0x00, 0x00, 0x00, 0x00]
            # send msg to inverter
            self._send_msg(msg)
            # receive msg from inverter
            msg = self._recv_smanet2_msg()
            if (msg != []):
                break

        if (retries == 0):
            logger.warning("sma: connect - retries used up!")
            return

        # second SMA net2 msg
        cmdcode = 0x0001
        msg = [0x7E, 0x00, 0x00, 0x00] + self._own_bt_addr_le + self._inv_bt_addr_le + [cmdcode & 0xFF, (cmdcode >> 8) & 0xFF]
        # sma-net2 level
        ctrl = 0xA008
        self._send_count += 1
        if (self._send_count > 75):
            self._send_count = 1
        msg += SMANET2_HDR + [ctrl & 0xFF, (ctrl >> 8) & 0xFF] + BCAST_ADDR + [0x00, 0x03] + self._inv_bt_addr_le + [0x00] + [0x03] + [0, 0, 0, 0] + [self._send_count]
        msg += [0x80, 0x0E, 0x01, 0xFD, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        # send msg
        self._send_msg(msg)

    def _inv_login(self):
        timestamp_utc = int(time.time())
        password_pattern = [0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88]
        password_pattern[0:len(self._inv_password)] = [((0x88 + ord(char)) & 0xff) for char in self._inv_password]

        retries = 10
        while (retries > 0):
            retries -= 1
            # level1
            cmdcode = 0x0001
            msg = [0x7E, 0, 0, 0] + self._own_bt_addr_le + self._inv_bt_addr_le + [cmdcode & 0xFF, (cmdcode >> 8) & 0xFF]
            # sma-net2 level
            ctrl = 0xA00E
            self._send_count += 1
            if (self._send_count > 75):
                self._send_count = 1
            msg += SMANET2_HDR + [ctrl & 0xFF, (ctrl >> 8) & 0xFF] + BCAST_ADDR + [0x00, 0x01] + self._inv_bt_addr_le + [0x00] + [0x01] + [0, 0, 0, 0] + [self._send_count]
            msg += [0x80, 0x0C, 0x04, 0xFD, 0xFF, 0x07, 0x00, 0x00, 0x00, 0x84, 0x03, 0x00, 0x00]
            msg += [timestamp_utc & 0xff, (timestamp_utc >> 8) & 0xff, (timestamp_utc >> 16) & 0xff, (timestamp_utc >> 24) & 0xff]
            msg += [0x00, 0x00, 0x00, 0x00] + password_pattern
            # send msg to inverter
            self._send_msg(msg)
            # send msg to inverter
            self._send_msg(msg)
            # receive msg from inverter
            msg = self._recv_smanet2_msg()
            if (msg != []):
                break

        if (retries == 0):
            logger.warning("sma: login - retries used up!")
            return

        # extract serial
        self._inv_serial = (msg[20] << 24) + (msg[19] << 16) + (msg[18] << 8) + msg[17]
        logger.debug("sma: inverter serial = %d" % self._inv_serial)

    def _inv_get_bt_signal_strength(self):
        cmdcode = 0x0003
        msg = [0x7E, 0, 0, 0] + self._own_bt_addr_le + self._inv_bt_addr_le + [cmdcode & 0xFF, (cmdcode >> 8) & 0xFF]
        msg += [0x05, 0x00]
        self._send_msg(msg)
        msg = self._recv_smanet1_msg_with_cmdcode([0x0004])
        # extract signal strength
        return ((msg[22] * 100.0) / 0xff)

    def _inv_get_value(self, value_set):
        # send request
        # level1
        cmdcode = 0x0001
        msg = [0x7E, 0, 0, 0] + self._own_bt_addr_le + self._inv_bt_addr_le + [cmdcode & 0xFF, (cmdcode >> 8) & 0xFF]
        # sma-net2 level
        self._send_count += 1
        if (self._send_count > 75):
            self._send_count = 1
        msg += SMANET2_HDR + [value_set[2] & 0xFF, (value_set[2] >> 8) & 0xFF] + BCAST_ADDR + [0x00, 0x00] + self._inv_bt_addr_le + [0x00] + [0x00] + [0, 0, 0, 0] + [self._send_count]
        msg += value_set[3] + [0x00] + [value_set[0] & 0xFF, (value_set[0] >> 8) & 0xFF] + [0x00, 0xFF] + [value_set[1] & 0xFF, (value_set[1] >> 8) & 0xFF] + [0x00]
        if (len(value_set) > 4):
            msg += [value_set[4]]
        # send msg to inverter
        self._send_msg(msg)

        # receive response from inverter
        data = []
        while (data == []):
            response = self._recv_smanet2_msg()
            if (response == []):
                logger.warning("sma: no response to request (timeout)!")
                return data
            if (len(response) >= 60):
                i = 42
                while (i < len(response) - 3):
                    value_code = (response[i + 1] << 8) + response[i]
                    timestamp_utc = (response[i + 6] << 24) + (response[i + 5] << 16) + (response[i + 4] << 8) + response[i + 3]
                    value = (response[i + 9] << 16) + (response[i + 8] << 8) + response[i + 7]
                    logger.debug("sma: value_code=0x%04x / value=%d" % (value_code, value))
                    data += [[value_code, timestamp_utc, value]]

                    if ((response[i + 2] == 0x00) or (response[i + 2] == 0x40)):
                        i += 28
                    elif ((response[i + 2] == 0x08) or (response[i + 2] == 0x10)):
                        i += 40
                    else:
                        logger.error("sma: rx - unknown data field width identifier=0x%02x" % response[i + 2])
                        data = []
                        break

            if (data == []):
                logger.warning("sma: rx - unknown/malformed response!")
                logger.warning("sma: rx - len=%d data=[%s]\n" % (len(response), ' '.join(['0x%02x' % b for b in response])))

        return data

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    myplugin = Plugin('SMA')
    myplugin.run()

# 0x80 0x01 0x02 0x00 0x51 0x00 0x3f 0x26 0x00 0xff 0x3f 0x26 0x00 0x8b 0xd0 0x7e
# stimmt mit letzter Zeile des request überein, aber im zweiten Byte it Bit 0 gesetzt = keine Daten?
#   0x83 0x01 0x02 0x80 0x53

# unknown msg periodically sent without request:
# 2013-06-17 19:49:22 sma.update   WARNING  sma: rx - len=84 data=[0x7e 0xff 0x03 0x60 0x65 0x13 0x90 0xfd 0xff 0xff 0xff 0xff 0xff 0x00 0xa0 0x8a 0x00 0xba 0x4d 0xf5 0x7e 0x00 0x00 0x00 0x00 0x00 0x00      0x6b 0xfd    0x0a 0x02 0x00 0x68 0x06 0x00 0x00 0x00 0x06 0x00 0x00 0x00 0x01 0x34 0x82 0x00     0xf6 0x4b 0xbf     0x51 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xfe 0xff 0xff 0xff 0xfe 0xff 0xff 0xff 0x04 0x03 0x55 0x02 0x04 0x03 0x55 0x02 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00      0x3c 0x18      0x7e]
# 2013-06-18 19:48:53 sma.update   WARNING  sma: rx - len=84 data=[0x7e 0xff 0x03 0x60 0x65 0x13 0x90 0xfd 0xff 0xff 0xff 0xff 0xff 0x00 0xa0 0x8a 0x00 0xba 0x4d 0xf5 0x7e 0x00 0x00 0x00 0x00 0x00 0x00      0xf0 0xfa    0x0a 0x02 0x00 0x68 0x06 0x00 0x00 0x00 0x06 0x00 0x00 0x00 0x01 0x34 0x82 0x00     0x79 0x9d 0xc0     0x51 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xfe 0xff 0xff 0xff 0xfe 0xff 0xff 0xff 0x04 0x03 0x55 0x02 0x04 0x03 0x55 0x02 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00      0x6d 0xde      0x7e]
# 2013-06-19 19:49:45 sma.update   WARNING  sma: rx - len=84 data=[0x7e 0xff 0x03 0x60 0x65 0x13 0x90 0xfd 0xff 0xff 0xff 0xff 0xff 0x00 0xa0 0x8a 0x00 0xba 0x4d 0xf5 0x7e 0x00 0x00 0x00 0x00 0x00 0x00      0x03 0xf7    0x0a 0x02 0x00 0x68 0x06 0x00 0x00 0x00 0x06 0x00 0x00 0x00 0x01 0x34 0x82 0x00     0xfa 0xee 0xc1     0x51 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0xfe 0xff 0xff 0xff 0xfe 0xff 0xff 0xff 0x04 0x03 0x55 0x02 0x04 0x03 0x55 0x02 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00      0x56 0xb6      0x7e]
