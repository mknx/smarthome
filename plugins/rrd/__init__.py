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
        #for itempath in self._rrds:
        #    rrd = self._rrds[itempath]
        #    if not os.path.isfile(rrd['rrdb']):
        #        self._create(rrd)
        #for area in self._sh.return_areas():
        #    if hasattr(area, 'rrd_graph'):
        #        self.parse_area(area)

        #offset = 100 # wait 100 seconds for 1-Wire to update values
        #self._sh.scheduler.add('rrd', self._update_rrd, cycle=self.step, offset=offset, prio=5)

        # create graphs
        #self.generate_graphs()

    def stop(self):
        self.alive = False

    def _update_rrd(self):
        for itempath in self._rrds:
            rrd = self._rrds[itempath]
            value = 'N:' + str(rrd['item']())
            try:
                rrdtool.update(
                    rrd['rrdb'],
                    value
                )
            except Exception, e:
                logger.warning("error updating rrd for %s: %s" % ( itempath, e ) )

    def parse_item(self, item):
        if 'rrd' in item.conf:
            print item.conf['rrd']

        return
        if hasattr(item, 'rrd'):
            if not self._sh.string2bool(item.rrd):
                return
        else:
            return
        # adding average method to the item
        item.average = types.MethodType(self.average, item, item.__class__)
        rrd_min = False
        rrd_max = False
        if hasattr(item, 'rrd_min'):
            if self._sh.string2bool(item.rrd_min):
                rrd_min = True
        if hasattr(item, 'rrd_max'):
            if self._sh.string2bool(item.rrd_max):
                rrd_max = True

        rrdb = self._rrd_dir + item.path + '.rrd'
        self._rrds[item.path] = { 'item': item, 'rrdb': rrdb, 'max': rrd_max, 'min': rrd_min }

        if hasattr(item, 'rrd_graph'):
            if not self._sh.string2bool(item.rrd_graph):
                return
            graph = []
            area, sep, name = item.path.rpartition('.')
            area = item.area
            title = area.name + ': ' + item.name
            graph.append('DEF:' + name  + '=' + rrdb + ':' + name + ':AVERAGE')
            graph.append('LINE1:' + name + '#' + self._linecolor + ':')
            if hasattr(item, 'rrd_opt'):
                if isinstance(item.rrd_opt, list):
                    graph += item.rrd_opt
                else:
                    graph.append(item.rrd_opt)
            else:
                if name == 'temperature':
                    graph += ['--vertical-label', '°C']
                elif name == 'humidity':
                    graph += ['--vertical-label', '%']

            self._graphs[item.path] = { 'obj': item, 'title': title, 'graph': graph }

    def parse_area(self, area):
        if not hasattr(area, 'rrd_graph'):
            return
        graph = []

        if not isinstance(area.rrd_graph, list):
            logger.warning("%s.rrd_graph is not a list of rrds. Ignoring." % area)
            return
        if not hasattr(area, 'rrd_opt'):
            logger.warning("no rrd_opt for %s specified. Ignoring." % area)
            return

        for path in area.rrd_graph:
            item = self._sh.return_item(path)
            if not hasattr(item, 'rrd'):
                logger.warning("%s.rrd_graph reference to %s, but rrd logging isn't enabled" % (area, item))
                return
            tmp, name = item.path.split('.')
            rrdb = self._rrd_dir + item.path + '.rrd'
            graph.append('DEF:' + name  + '=' + rrdb + ':' + name + ':AVERAGE')

        if isinstance(area.rrd_opt, list):
            graph += area.rrd_opt
        else:
            graph.append(area.rrd_opt)
        title = area.name
        self._graphs[area.path] = { 'obj': area, 'title': title, 'graph': graph }

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None):
        pass

    def generate_graphs(self, timeframe='1d'):
        for graph in self._graphs:
            self._graph(self._graphs[graph], timeframe)

    def _graph(self, graph, timeframe='1d'):
        defs = []
        obj = graph['obj']
        png = self._png_dir + obj.path + '-' + timeframe + '.png'
        web = self._web_dir + obj.path + '-' + timeframe + '.png'
        try:
            width, height, string =  rrdtool.graph(
                png,
                '--title', graph['title'],
                '--imgformat', 'PNG',
                self._style,
                '--start', 'e-' + timeframe,
                graph['graph']
            )
            # adding rrd_img attribute to item
            vars(obj)['rrd_img_' + timeframe] = "<img src=\"%s\" width=\"%s\" height=\"%s\" alt=\"%s\" />" % (web, width, height, graph['title'])
        except Exception, e:
            logger.warning("error creating graph for %s: %s" % ( png, e ))

    def average(self, item, timeframe):
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
            logger.warning("rrd not enabled for %s" % item )
            return
        rrdb = self._rrd_dir + item.path + '.rrd'
        try:
            env, name, data = rrdtool.fetch(
                rrdb,
                cf,
                '--start', 'e-' + timeframe
            )
            return list(i[0] for i in data) # flatten reply
        except Exception, e:
            logger.warning("error reading %s data: %s" % ( item, e ))
            return None

    def _create(self, rrd):
        insert = []
        area, item = rrd['item'].path.split('.')
        insert.append('DS:' + item + ':GAUGE:' + str(2*self.step) + ':U:U')
        if rrd['min']:
            insert.append('RRA:MIN:0.5:'   + str(int(86400/self.step)) + ':1825')  # 24h/5y
        if rrd['max']:
            insert.append('RRA:MAX:0.5:'   + str(int(86400/self.step)) + ':1825')  # 24h/5y

        try:
            rrdtool.create(
                rrd['rrdb'],
                '--step', str(self.step),
                insert,
                'RRA:AVERAGE:0.5:1:' + str(int(86400/self.step)*30),        # 30 days
                'RRA:AVERAGE:0.5:'   + str(int(3600/self.step))  + ':8760', # 1h/365 days
                'RRA:AVERAGE:0.5:'   + str(int(86400/self.step)) + ':1825'  # 24h/5y
            )
            logger.debug("Creating rrd ({0}) for {1}.".format( rrd['rrdb'], rrd['item'] ))
        except Exception, e:
            logger.warning("Error creating rrd ({0}) for {1}: {2}".format( rrd['rrdb'], rrd['item'], e ))

