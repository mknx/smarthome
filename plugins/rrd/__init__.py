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
import os
import types
import rrdtool

logger = logging.getLogger('')


class RRD():

    def __init__(self, smarthome, step=300, style=[], rrd_dir='/usr/local/smarthome/var/rrd/', png_dir='/var/www/visu/rrd/', web_dir='/rrd/'):
        self._sh = smarthome
        self._rrd_dir = rrd_dir
        self._png_dir = png_dir
        self._web_dir = web_dir
        self._style = style
        self._rrds = {}
        self._graphs = {}
        self._linecolor = '222222'
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
        # create graphs
        #self.generate_graphs()

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
            if 'visu' in rrd['item'].conf:
                self._sh.visu.update_rrd(rrd['item'])
    #self.generate_graphs()

    def parse_item(self, item):
        rrdb = self._rrd_dir + item.id() + '.rrd'
        if 'rrd' in item.conf:
            rrd_min = False
            rrd_max = False
            if 'min' in item.conf['rrd']:
                rrd_min = True
            if 'max' in item.conf['rrd']:
                rrd_max = True
            # adding average and export method to the item
            item.average = types.MethodType(self._average, item, item.__class__)
            item.export = types.MethodType(self._export, item, item.__class__)
            self._rrds[item.id()] = {'item': item, 'rrdb': rrdb, 'max': rrd_max, 'min': rrd_min}
        if 'rrd_png' in item.conf:
            parent = str(item.return_parent())
            tmp, sep, item_id = item.id().rpartition('.')
            if '__main__' in parent:
                title = str(item)
            else:
                title = parent + ': ' + str(item)
            graph = []
            #if isinstance(item.conf['rrd_png'], list):  # graph for multiple items
            #    for i_path in item.conf['rrd_png']:
            #        i_item = self._sh.return_item(i_path)
            #        if i_item != None:
            #            graph += self._parse_item(i_item)
            #    if 'rrd_opt' not in item.conf:
            #        logger.warning("rrd_opt not specified for {0}. Ignoring.".format(item.id()))
            #        return
            #else:  # graph for one item
            #    graph += self._parse_item(item)
            #    graph.append('LINE1:' + item_id + '#' + self._linecolor + ':')
            #if 'rrd_opt' in item.conf:
            #    if isinstance(item.conf['rrd_opt'], list):
            #        graph += item.conf['rrd_opt']
            #    else:
            #        graph.append(item.conf['rrd_opt'])
            #self._graphs[item.id()] = {'obj': item, 'title': title, 'graph': graph}

    def _simplify(self, value):
        if value[0] != None:
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
        data = map(self._simplify,  data)
        while data[-1] == None and len(data) > 1:
            del data[-1]
        return {'id': item.id(), 'frame': frame, 'start': start, 'step': step, 'data': data}

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None):
        pass

    def _average(self, item, timeframe):
        values = self.read(item, timeframe)
        if values == None:
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
                'RRA:AVERAGE:0.5:1:' + str(int(86400 / self.step) * 7),     # 7 days
                'RRA:AVERAGE:0.5:' + str(int(1800 / self.step)) + ':1488',  # 0.5h/31 days
                'RRA:AVERAGE:0.5:' + str(int(3600 / self.step)) + ':8760',  # 1h/365 days
                'RRA:AVERAGE:0.5:' + str(int(86400 / self.step)) + ':1825'  # 24h/5y
            )
            logger.debug("Creating rrd ({0}) for {1}.".format(rrd['rrdb'], rrd['item']))
        except Exception, e:
            logger.warning("Error creating rrd ({0}) for {1}: {2}".format(rrd['rrdb'], rrd['item'], e))

    #def _parse_item(self, item):
    #        if 'rrd' not in item.conf:
    #            logger.warning("Could not generate png for {0}. No rrd available. Add 'rrd = yes' to {0}".format(item.id()))
    #            return []
    #        rrdb = self._rrd_dir + item.id() + '.rrd'
    #        tmp, sep, item_id = item.id().rpartition('.')
    #        graph = []
    #        graph.append('DEF:' + item_id + '=' + rrdb + ':' + item_id + ':AVERAGE')
    #        if item_id == 'temperature':
    #            graph += ['--vertical-label', '°C']
    #        elif item_id == 'humidity':
    #            graph += ['--vertical-label', '%']
    #        return graph

    #def generate_graphs(self, timeframe='1d'):
    #    for graph in self._graphs:
    #        self._graph(self._graphs[graph], timeframe)

    #def _graph(self, graph, timeframe='1d'):
    #    defs = []
    #    obj = graph['obj']
    #    png = self._png_dir + obj.id() + '-' + timeframe + '.png'
    #    web = self._web_dir + obj.id() + '-' + timeframe + '.png'
    #    try:
    #        width, height, string = rrdtool.graph(
    #            png,
    #            '--title', graph['title'],
    #            '--imgformat', 'PNG',
    #            self._style,
    #            '--start', 'e-' + timeframe,
    #            graph['graph']
    #        )
    #        # adding rrd_img attribute to item
    #        vars(obj)['rrd_img_' + timeframe] = "<img src=\"%s\" width=\"%s\" height=\"%s\" alt=\"%s\" />" % (web, width, height, graph['title'])
    #    except Exception, e:
    #        logger.warning("error creating graph for %s: %s" % (png, e))
