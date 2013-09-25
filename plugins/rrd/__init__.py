#!/usr/bin/env python3
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

import datetime
import functools
import logging
import os

import rrdtool

logger = logging.getLogger('')


class RRD():
    _cf = {'avg': 'AVERAGE', 'max': 'MAX', 'min': 'MIN'}

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
            except Exception as e:
                logger.warning("error updating rrd for {}: {}".format(itempath, e))
                return

    def parse_item(self, item):
        if 'rrd' not in item.conf:
            return
        rrdb = self._rrd_dir + item.id() + '.rrd'
        rrd_min = False
        rrd_max = False
        if 'rrd_min' in item.conf:
            rrd_min = self._sh.string2bool(item.conf['rrd_min'])
        if 'rrd_max' in item.conf:
            rrd_max = self._sh.string2bool(item.conf['rrd_max'])
        item.series = functools.partial(self._series, item=item.id())
        self._rrds[item.id()] = {'item': item, 'rrdb': rrdb, 'max': rrd_max, 'min': rrd_min}

    def parse_logic(self, logic):
        pass

    def _series(self, func, start, end='now', count=100, ratio=1, update=False, step=None, sid=None, item=None):
        query = ["{}{}.rrd".format(self._rrd_dir, item)]
        if func in self._cf:
            query.append(self._cf[func])
        else:
            logger.warning("RRD: unsupported consolidation function {} for {}".format(func, item))
            return
        if start.isdigit():
            query.extend(['--start', "{}".format(start)])
        else:
            query.extend(['--start', "now-{}".format(start)])
        if end != 'now':
            if end.isdigit():
                query.extend(['--end', "{}".format(end)])
            else:
                query.extend(['--end', "now-{}".format(end)])
        if step is not None:
            query.extend(['--resolution', step])
        try:
            meta, name, data = rrdtool.fetch(
                query
            )
        except Exception as e:
            logger.warning("error reading {0} data: {1}".format(item, e))
            return None
        if sid is None:
            sid = item + '|' + func + '|' + start + '|' + end
        reply = {'cmd': 'series', 'series': None, 'sid': sid}
        istart, iend, istep = meta
        mstart = istart * 1000
        mstep = istep * 1000
        tuples = [(mstart + i * mstep, v[0]) for i, v in enumerate(data)]
        reply['series'] = sorted(tuples)
        reply['params'] = {'update': True, 'item': item, 'func': func, 'start': str(iend), 'end': str(iend + istep), 'step': str(istep), 'sid': sid}
        reply['update'] = self._sh.now() + datetime.timedelta(seconds=istep)
        return reply

    def _single(self, func, start, end='now', item=None):
        pass

    def _create(self, rrd):
        insert = []
        tmp, sep, item_id = rrd['item'].id().rpartition('.')
        insert.append('DS:' + item_id[:19] + ':GAUGE:' + str(2 * self.step) + ':U:U')
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
        except Exception as e:
            logger.warning("Error creating rrd ({0}) for {1}: {2}".format(rrd['rrdb'], rrd['item'], e))
