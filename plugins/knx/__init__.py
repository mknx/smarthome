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
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import struct
import lib.my_asynchat
import dpts

KNXREAD = 0x00
KNXRESP = 0x40
KNXWRITE = 0x80

logger = logging.getLogger('')


class KNX(lib.my_asynchat.AsynChat):

    def __init__(self, smarthome, time_ga=None, date_ga=None, send_time=False, busmonitor=False, host='127.0.0.1', port=6720):
        lib.my_asynchat.AsynChat.__init__(self, smarthome, host, port)
        self._sh = smarthome
        self.gal = {}
        self.gar = {}
        self._init_ga = []
        self._cache_ga = []
        self.time_ga = time_ga
        self.date_ga = date_ga
        if smarthome.string2bool(busmonitor):
            self._busmonitor = logger.info
        else:
            self._busmonitor = logger.debug
        if send_time:
            self._sh.scheduler.add('knx.time', self._send_time, prio=5, cycle=int(send_time))
        smarthome.monitor_connection(self)

    def _send(self, data):
        send = ''
        if len(data) < 2 or len(data) > 0xffff:
            logger.debug('Illegal data size: %s' % repr(data))
            return False
        # prepend data length
        data = [(len(data) >> 8) & 0xff, (len(data)) & 0xff] + data
        for i in data:
            send += chr(i)
        self.push(send)

    def groupwrite(self, ga, payload, dpt, flag='write'):
        pkt = [0, 39] + self.encode(ga, 'ga') + [0]
        pkt += self.encode(payload, dpt)
        if flag == 'write':
            flag = KNXWRITE
        elif flag == 'response':
            flag = KNXRESP
        else:
            logger.warning("Groupwrite telegram for {0} with unknown flag: {1}. Please choose beetween write and response.".format(ga, flag))
            return
        pkt[5] = flag | pkt[5]
        self._send(pkt)

    def _cacheread(self, ga):
        pkt = [0, 116] + self.encode(ga, 'ga') + [0, 0]
        self._send(pkt)

    def groupread(self, ga):
        pkt = [0, 39] + self.encode(ga, 'ga') + [0, KNXREAD]
        self._send(pkt)

    def _send_time(self):
        now = self._sh.now()
        if self.time_ga:
            self.groupwrite(self.time_ga, now, '10')
        if self.date_ga:
            self.groupwrite(self.date_ga, now.date(), '11')

    def send_time(self, time_ga=None, date_ga=None):
        now = self._sh.now()
        if time_ga:
            self.groupwrite(time_ga, now.time(), '10')
        if date_ga:
            self.groupwrite(date_ga, now.date(), '11')

    def handle_connect(self):
        self.discard_buffers()
        enable_cache = [0, 112]
        self._send(enable_cache)
        self.parse_data = self.parse_length
        if self._cache_ga != []:
            if self.is_connected:
                logger.debug('knx: read cache')
                for ga in self._cache_ga:
                    self._cacheread(ga)
                self._cache_ga = []
        logger.debug('knx: enable group monitor')
        init = [0, 38, 0, 0, 0]
        self._send(init)
        self.terminator = 2
        if self._init_ga != []:
            if self.is_connected:
                logger.debug('knx: init read')
                for ga in self._init_ga:
                    self.groupread(ga)
                self._init_ga = []

#   def collect_incoming_data(self, data):
#       ba = bytearray(data)
#       print('#  bin   h  d')
#       for i in ba:
#           print("{0:08b} {0:02x} {0:02d}".format(i))
#       self.buffer += data

    def found_terminator(self):
        data = self.buffer
        self.buffer = ''
        self.parse_data(data)

    def parse_length(self, length):
        self.parse_data = self.parse_telegram
        try:
            self.terminator = struct.unpack(">H", length)[0]
        except:
            logger.error("knx: problem unpacking length: {0}".format(length))
            self.close()

    def encode(self, data, dpt):
        return dpts.encode[str(dpt)](data)

    def decode(self, data, dpt):
        return dpts.decode[str(dpt)](data)

    def parse_telegram(self, telegram):
        self.parse_data = self.parse_length  # reset parser and terminator
        self.terminator = 2
        # 2 byte type
        # 2 byte src
        # 2 byte dst
        # 2 byte command/data
        # x byte data
        typ = struct.unpack(">H", telegram[:2])[0]
        if (typ != 39 and typ != 116) or len(telegram) < 8:
#           logger.debug("Ignore telegram.")
            return
        if (ord(telegram[6]) & 0x03 or (ord(telegram[7]) & 0xC0) == 0xC0):
            logger.debug("Unknown APDU")
            return
        src = self.decode(telegram[2:4], 'pa')
        dst = self.decode(telegram[4:6], 'ga')
        flg = ord(telegram[7]) & 0xC0
        if flg == KNXWRITE:
            flg = 'write'
        elif flg == KNXREAD:
            flg = 'read'
        elif flg == KNXRESP:
            flg = 'response'
        else:
            logger.warning("Unknown flag: {0:02x} src: {1} dest: {2}".format(flg, src, dst))
            return
        if len(telegram) == 8:
            payload = chr(ord(telegram[7]) & 0x3f)
        else:
            payload = telegram[8:]
        if flg == 'write' or flg == 'response':
            if dst not in self.gal:  # update item/logic
                self._busmonitor("knx: {0} set {1} to {2}".format(src, dst, self.decode(payload, 'hex')))
                return
            dpt = self.gal[dst]['dpt']
            val = self.decode(payload, dpt)
            if val is not None:
                self._busmonitor("knx: {0} set {1} to {2}".format(src, dst, val))
                #print "in:  {0}".format(self.decode(payload, 'hex'))
                #out = ''
                #for i in self.encode(val, dpt):
                #    out += " {0:x}".format(i)
                #print "out:{0}".format(out)
                for item in self.gal[dst]['items']:
                    item(val, 'KNX', src, dst)
                for logic in self.gal[dst]['logics']:
                    logic.trigger('KNX', src, val, dst)
            else:
                logger.warning("Wrong payload '{2}' for ga '{1}' with dpt '{0}'.".format(dpt, dst, self.decode(payload, 'hex')))
        elif flg == 'read':
            logger.debug("{0} read {1}".format(src, dst))
            if dst in self.gar:  # read item
                if self.gar[dst]['item'] is not None:
                    item = self.gar[dst]['item']
                    self.groupwrite(dst, item(), item.conf['knx_dpt'], 'response')
                if self.gar[dst]['logic'] is not None:
                    self.gar[dst]['logic'].trigger('KNX', src, 'read', dst)

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False
        self.handle_close()

    def parse_item(self, item):
        if 'knx_dtp' in item.conf:
            logger.warning("knx: Ignoring {0}: please change knx_dtp to knx_dpt.".format(item))
            return None
        if 'knx_dpt' in item.conf:
            dpt = item.conf['knx_dpt']
            if dpt not in dpts.decode:
                logger.warning("knx: Ignoring {0} unknown dpt: {1}".format(item, dpt))
                return None
        else:
            return None

        if 'knx_listen' in item.conf:
            knx_listen = item.conf['knx_listen']
            if isinstance(knx_listen, str):
                knx_listen = [knx_listen, ]
            for ga in knx_listen:
                logger.debug("knx: {0} listen on {1}".format(item, ga))
                if not ga in self.gal:
                    self.gal[ga] = {'dpt': dpt, 'items': [item], 'logics': []}
                else:
                    if not item in self.gal[ga]['items']:
                        self.gal[ga]['items'].append(item)

        if 'knx_init' in item.conf:
            ga = item.conf['knx_init']
            logger.debug("knx: {0} listen on and init with {1}".format(item, ga))
            if not ga in self.gal:
                self.gal[ga] = {'dpt': dpt, 'items': [item], 'logics': []}
            else:
                if not item in self.gal[ga]['items']:
                    self.gal[ga]['items'].append(item)
            self._init_ga.append(ga)

        if 'knx_cache' in item.conf:
            ga = item.conf['knx_cache']
            logger.debug("knx: {0} listen on and init with cache {1}".format(item, ga))
            if not ga in self.gal:
                self.gal[ga] = {'dpt': dpt, 'items': [item], 'logics': []}
            else:
                if not item in self.gal[ga]['items']:
                    self.gal[ga]['items'].append(item)
            self._cache_ga.append(ga)

        if 'knx_reply' in item.conf:
            knx_reply = item.conf['knx_reply']
            if isinstance(knx_reply, str):
                knx_reply = [knx_reply, ]
            for ga in knx_reply:
                logger.debug("knx: {0} reply to {1}".format(item, ga))
                if ga not in self.gar:
                    self.gar[ga] = {'dpt': dpt, 'item': item, 'logic': None}
                else:
                    logger.warning("knx: {0} knx_reply ({1}) already defined for {2}".format(item, ga, self.gar[ga]['item']))

        if 'knx_send' in item.conf or 'knx_status' in item.conf:
            if isinstance(item.conf['knx_send'], str):
                item.conf['knx_send'] = [item.conf['knx_send'], ]
            if isinstance(item.conf['knx_status'], str):
                item.conf['knx_status'] = [item.conf['knx_status'], ]
            return self.update_item
        else:
            return None

    def parse_logic(self, logic):
        if 'knx_dpt' in logic.conf:
            dpt = logic.conf['knx_dpt']
            if dpt not in dpts.decode:
                logger.warning("knx: Ignoring {0} unknown dpt: {1}".format(logic, dpt))
                return None
        else:
            return None

        if 'knx_listen' in logic.conf:
            knx_listen = logic.conf['knx_listen']
            if isinstance(knx_listen, str):
                knx_listen = [knx_listen, ]
            for ga in knx_listen:
                logger.debug("knx: {0} listen on {1}".format(logic, ga))
                if not ga in self.gal:
                    self.gal[ga] = {'dpt': dpt, 'items': [], 'logics': [logic]}
                else:
                    self.gal[ga]['logics'].append(logic)

        if 'knx_reply' in logic.conf:
            knx_reply = logic.conf['knx_reply']
            if isinstance(knx_reply, str):
                knx_reply = [knx_reply, ]
            for ga in knx_reply:
                logger.debug("knx: {0} reply to {1}".format(logic, ga))
                if ga in self.gar:
                    if self.gar[ga]['logic'] is False:
                        obj = self.gar[ga]['item']
                    else:
                        obj = self.gar[ga]['logic']
                    logger.warning("knx: {0} knx_reply ({1}) already defined for {2}".format(logic, ga, obj))
                else:
                    self.gar[ga] = {'dpt': dpt, 'item': None, 'logic': logic}

    def update_item(self, item, caller=None, source=None, dest=None):
        if 'knx_send' in item.conf:
            if caller != 'KNX':
                for ga in item.conf['knx_send']:
                    self.groupwrite(ga, item(), item.conf['knx_dpt'])
        if 'knx_status' in item.conf:
            for ga in item.conf['knx_status']:  # send status update
                if ga != dest:
                    self.groupwrite(ga, item(), item.conf['knx_dpt'])
