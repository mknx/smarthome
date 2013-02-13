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
#  along with SmartHome.py.  If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import os
import types
import rrdtool

logger = logging.getLogger('')


class RRD():

    def __init__(self, smarthome, step=300, rrd_dir=None):
        self._sh = smarthome
        if rrd_dir is None:
            rrd_dir = smarthome.base_dir + '/var/rrd/'
        self._rrd_dir = rrd_dir
        self._rrds = {}
        self.step = int(step)

    def run(self):
        self.alive = True
        # create rrds
        for itempath in self._rrds:
            rrd = self._rrds[itempath]
            if not os.path.isfile(rrd['rrdb']):
                self._create(rrd)
        offset = 100  # wait 100 seconds for 1-Wire to update values
        self._sh.scheduler.add('rrd', self._update_cycle, cycle=self.step, offset=offset, prio=5)

    def stop(self):
        self.alive = False

    def _update_cycle(self):
        for itempath in self._rrds:
            rrd = self._rrds[itempath]
            value = 'N:' + str(float(rrd['item']()))
            try:
                rrdtool.update(
                    rrd['rrdb'],
                    value
                )
            except Exception, e:
                logger.warning("error updating rrd for %s: %s" % (itempath, e))
                return
        data = []
        time = self._sh.now()
        time = int(time.strftime("%s")) + time.utcoffset().seconds
        for itempath in self._rrds:
            item = self._rrds[itempath]['item']
            if 'visu' in item.conf:
                data.append([item.id(), item()])
        for listener in self._sh.return_listeners():
            listener({'cmd': 'rrd', 'time': time, 'rrd': data})

    def parse_item(self, item):
        if 'rrd' not in item.conf:
            return
        rrdb = self._rrd_dir + item.id() + '.rrd'
        rrd_min = False
        rrd_max = False
        if 'rrd_min' in item.conf['rrd']:
            rrd_min = True
        if 'rrd_max' in item.conf['rrd']:
            rrd_max = True
        # adding average and export method to the item
        item.average = types.MethodType(self._average, item, item.__class__)
        item.export = types.MethodType(self._export, item, item.__class__)
        self._rrds[item.id()] = {'item': item, 'rrdb': rrdb, 'max': rrd_max, 'min': rrd_min}

    def _simplify(self, value):
        if value[0] is not None:
            return round(value[0], 2)

    def _export(self, item, frame='1d'):
        rrdb = self._rrd_dir + item.id() + '.rrd'
        tmp, name = item.id().split('.')
        try:
            meta, names, data = rrdtool.fetch(rrdb, 'AVERAGE', '--start', 'now-' + frame)
        except Exception, e:
            logger.warning("error reading %s data: %s" % (item, e))
            return None
        start, end, step = meta
        start += self._sh.now().utcoffset().seconds
        data = map(self._simplify, data)
        if data[-2] is None:
            del data[-2]
        if data[-1] is None:
            data[-1] = item()
        return {'cmd': 'rrd', 'frame': frame, 'start': start, 'step': step, 'rrd': [[item.id(), data]]}

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None):
        pass

    def _average(self, item, timeframe):
        values = self.read(item, timeframe)
        if values is None:
            return None
        values = filter(None, values)
        if len(values) == 0:
            return None
        else:
            return sum(values) / len(values)

    def read(self, item, timeframe='1d', cf='AVERAGE'):
        if not hasattr(item, 'rrd'):
            logger.warning("rrd not enabled for %s" % item)
            return
        rrdb = self._rrd_dir + item.path + '.rrd'
        try:
            env, name, data = rrdtool.fetch(
                rrdb,
                cf,
                '--start', 'e-' + timeframe
            )
            return list(i[0] for i in data)  # flatten reply
        except Exception, e:
            logger.warning("error reading %s data: %s" % (item, e))
            return None

    def _create(self, rrd):
        insert = []
        tmp, sep, item_id = rrd['item'].id().rpartition('.')
        insert.append('DS:' + item_id + ':GAUGE:' + str(2 * self.step) + ':U:U')
        if rrd['min']:
            insert.append('RRA:MIN:0.5:' + str(int(86400 / self.step)) + ':1825')  # 24h/5y
        if rrd['max']:
            insert.append('RRA:MAX:0.5:' + str(int(86400 / self.step)) + ':1825')  # 24h/5y
        try:
            rrdtool.create(
                rrd['rrdb'],
                '--step', str(self.step),
                insert,
                'RRA:AVERAGE:0.5:1:' + str(int(86400 / self.step) * 7 + 8),  # 7 days
                'RRA:AVERAGE:0.5:' + str(int(1800 / self.step)) + ':1536',   # 0.5h/32 days
                'RRA:AVERAGE:0.5:' + str(int(3600 / self.step)) + ':9600',   # 1h/400 days
                'RRA:AVERAGE:0.5:' + str(int(86400 / self.step)) + ':1826'   # 24h/5y
            )
            logger.debug("Creating rrd ({0}) for {1}.".format(rrd['rrdb'], rrd['item']))
        except Exception, e:
            logger.warning("Error creating rrd ({0}) for {1}: {2}".format(rrd['rrdb'], rrd['item'], e))
