#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
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

import re
import datetime
import urllib
import logging


logger = logging.getLogger('')


class SolarLog():

    def __init__(self, smarthome, host):
        self._sh = smarthome
        self._host = host
        self._count_inverter = 0
        self._count_strings = []
        self._items = {}
        self._last_datetime = None

    def run(self):
        self.alive = True
        self._read_base_vars()
        
        self._count_inverter = int(vars(self)['AnzahlWR'])
        for x in range(0, self._count_inverter):
            self._count_strings.append(int(vars(self)['WRInfo'][x][5]))

        cycle = 300
        if vars(self).has_key('Intervall'):
            cycle = int(vars(self)['Intervall'])
        self._sh.scheduler.add('solarlog', self._refresh_rrd, cycle=cycle)

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        if 'solarlog' in item.conf:
            self._items[item.conf['solarlog']] = item
       
        return None

    def parse_logic(self, logic):
        pass

    def _refresh_rrd(self):
        now = self._sh.now()
        time_start = int(vars(self)['time_start'][now.month-1])
        time_end = int(vars(self)['time_end'][now.month-1])
        is_online = bool(vars(self)['isOnline'])
        
        # we start refreshing one hour earlier as set by the device
        if now.hour < (time_start - 1):
            return

        # in the evening we stop refreshing when the device is offline
        if now.hour >= time_end and not is_online:
            return
        
        self.refresh()
        groups = self._read_min_day()

        if groups:
            for name in groups.keys():
                if self._items.has_key(name):
                    self._items[name](groups[name])

    def _read_base_vars(self):
        self._read_javascript('base_vars.js')

    def refresh(self):
        self._read_javascript('base_vars.js')
        self._read_javascript('min_cur.js')

        # set state and error messages
        for x in range(0, self._count_inverter):
            if self._items.has_key('curStatusCode_{0}'.format(x)):
                item = self._items['curStatusCode_{0}'.format(x)]
                if isinstance(item(), str):
                    item(vars(self)['StatusCodes'][x][int(vars(self)['curStatusCode'][x])])
                else:
                    item(vars(self)['curStatusCode'][x])
            if self._items.has_key('curFehlerCode_{0}'.format(x)):
                item = self._items['curFehlerCode_{0}'.format(x)]
                if isinstance(item(), str):
                    item(vars(self)['FehlerCodes'][x][int(vars(self)['curFehlerCode'][x])])
                else:
                    item(vars(self)['curFehlerCode'][x])

        # set all other values
        for name in vars(self).keys():
            if self._items.has_key(name):
                self._items[name](vars(self)[name])

    def _read_javascript(self, filename):
        re_var = re.compile(r'^var\s+(?P<varname>\w+)\s*=\s*"?(?P<varvalue>[^"]+)"?;?')
        re_array = re.compile(r'^var\s+(?P<varname>\w+)\s*=\s*new\s*Array\s*\((?P<arrayvalues>.*)\)')
        re_array_1st_level = re.compile(r'\s*(?P<varname>\w+)\[(?P<idx1>[0-9]+)\]((\s*=\s*(?:new\s*Array)?\((?P<arrayvalues>.*)\))|(\s*=\s*(?P<arraystring>.*)))')
        re_array_2nd_level = re.compile(r'\s*(?P<varname>\w+)\[(?P<idx1>[0-9]+)\]\s*\[(?P<idx2>[0-9]+)\]\s*=\s*new\s*Array\s*\((?P<arrayvalues>.*)\)')
        
        f = self._read(filename)

        if f:
            for line in f.splitlines():
                matches = re_array.match(line)

                if matches:
                    name, value = matches.groups()

                    vars(self)[name] = []

                    if vars(self).has_key(value):
                        vars(self)[name] = [None] * int(vars(self)[value])
                    else:
                        try:
                            vars(self)[name] = [None] * int(value)
                        except:
                            vars(self)[name] = [x.strip(' "') for x in value.split(',')]
                    continue
                
                matches = re_var.match(line)

                if matches:
                    name, value = matches.groups()
                    vars(self)[name] = value
                    continue

                matches = re_array_1st_level.match(line)

                if matches:
                    name = matches.group('varname')
                    idx1 = int(matches.group('idx1'))

                    if vars(self).has_key(name):
                        values = matches.group('arrayvalues')
                        if not values:
                            values = matches.group('arraystring')
                        if ',' in values:
                            vars(self)[name][idx1] = [x.strip(' "') for x in values.split(',')]
                        else:
                            vars(self)[name][idx1] = values
                    continue

                matches = re_array_2nd_level.match(line)

                if matches:
                    name, idx1, idx2, value = matches.groups()

                    if vars(self).has_key(name):
                        vars(self)[name][int(idx1)][int(idx2)] = [x.strip(' "') for x in value.split(',')]
                    continue

    def _read_years(self):
        pattern = r'ye\[yx\+\+\]=.(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{2})'
        
        for x in range(0, self._count_inverter):
            pattern += '\|(?P<out_{0}>[0-9]*)'.format(x)

        pattern += '\"'
        re_entry = re.compile(pattern)

        years = self._read('years.js')

        if years:
            for line in years.splitlines():
                matches = re_entry.match(line)

                if matches:
                    logger.debug(matches.groups())

    def _read_months(self):
        pattern = r'mo\[mx\+\+\]=.(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{2})'
        
        for x in range(0, self._count_inverter):
            pattern += '\|(?P<out_{0}>[0-9]*)'.format(x)

        pattern += '\"'
        re_entry = re.compile(pattern)

        months = self._read('months.js')

        if months:
            for line in months.splitlines():
                matches = re_entry.match(line)

                if matches:
                    logger.debug(matches.groups())

    def _read_days(self, history=False):
        pattern = r'da\[dx\+\+\]=.(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{2})'
        
        for x in range(0, self._count_inverter):
            pattern += '\|(?P<out_{0}>[0-9]*);(?P<pac_max_{0}>[0-9]*)'.format(x)

        pattern += '\"'
        re_entry = re.compile(pattern)

        if history:
            days = self._read('days_hist.js')
        else:
            days = self._read('days.js')

        if days:
            for line in days.splitlines():
                matches = re_entry.match(line)

                if matches:
                    logger.debug(matches.groups())


    def _read_min_day(self, date=None, read_all=False):
        pattern = r'm\[mi\+\+\]=.(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{2})\s(?P<hour>\d{2})\:(?P<minute>\d{2})\:(?P<second>\d{2})'
        
        # TODO: add a pattern that matches sensor boxes
        # ATM only inverters and strings supported
        for x in range(0, self._count_inverter):
            pattern += '\|(?P<pac_{0}>[0-9]*)'.format(x)

            for y in range(0, self._count_strings[x]):
                pattern += ';(?P<pdc_{0}_{1}>[0-9]*)'.format(x,y)

            pattern += ';(?P<out_{0}>[0-9]*)'.format(x)

            for y in range(0, self._count_strings[x]):
                pattern += ';(?P<udc_{0}_{1}>[0-9]*)'.format(x,y)

            if len(vars(self)['WRInfo'][x]) > 12:
                if vars(self)['WRInfo'][x][12] == '1':
                    pattern += ';(?P<tmp_{0}>[0-9]*)'.format(x)

        pattern += '\"'
        re_entry = re.compile(pattern)

        if date:
            min_day = self._read('min{0}.js'.format(date.strftime('%y%m%d')))
        else:
            min_day = self._read('min_day.js')
        
        groups = []

        if min_day:
            for line in min_day.splitlines():
                matches = re_entry.match(line)

                if matches:
                    if read_all:
                        groups.append(matches.groupdict())
                    else:
                        return matches.groupdict()

        return groups if read_all else None

    def _read(self, filename):
        url = self._host + filename
        f = urllib.urlopen(url)
        return f.read()

