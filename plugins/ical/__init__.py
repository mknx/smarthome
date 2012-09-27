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
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import datetime
import dateutil.tz
import dateutil.rrule
import dateutil.relativedelta
import urllib2
import logging

logger = logging.getLogger('')


class iCal():
    DAYS = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
    FREQ = ("YEARLY", "MONTHLY", "WEEKLY", "DAILY", "HOURLY", "MINUTELY", "SECONDLY")

    def __init__(self, smarthome):
        self._sh = smarthome

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False

    def _parse_date(self, value, dtzinfo, par=''):
        if par.startswith('TZID='):
            tmp, par, timezone = par.partition('=')
            tzinfo = dateutil.tz.gettz(timezone)
        else:
            tzinfo = dtzinfo
        if 'T' in value:  # ISO
            value, sep, offset = value.partition('Z')
            dt = datetime.datetime.strptime(value, "%Y%m%dT%H%M%S")
        else:  # date
            y = int(value[0:4])
            m = int(value[4:6])
            d = int(value[6:8])
            dt = datetime.datetime(y, m, d)
        dt = dt.replace(tzinfo=tzinfo)
        return dt

    def _parse_event(self, event, dtzinfo, start, end):
        if 'rrule' not in event:
            if event['start'] >= start and event['start'] <= end:
                yield(event['start'])
        else:
            kwargs = {}
            mapping = {'INTERVAL': 'interval', 'WKST': 'wkst', 'COUNT': 'count', }
            if 'FREQ' in event['rrule']:
                freq = self.FREQ.index(event['rrule']['FREQ'])
                del(event['rrule']['FREQ'])
                if 'DTSTART' not in event['rrule']:
                    event['rrule']['DTSTART'] = event['start']
                if 'WKST' in event['rrule']:
                    if event['rrule']['WKST'] in self.DAYS:
                        event['rrule']['WKST'] = self.DAYS.index(event['rrule']['WKST'])
                    else:
                        event['rrule']['WKST'] = int(event['rrule']['WKST'])
                if 'BYDAY' in event['rrule']:
                    day = event['rrule']['BYDAY']
                    if day.isalpha():
                        if day in self.DAYS:
                            day = self.DAYS.index(day)
                    else:
                        n = int(day[0:-2])
                        day = self.DAYS.index(day[-2:])
                        day = dateutil.rrule.weekday(day, n)
                    event['rrule']['BYWEEKDAY'] = day
                    del(event['rrule']['BYDAY'])
                if 'COUNT' in event['rrule']:
                    event['rrule']['COUNT'] = int(event['rrule']['COUNT'])
                if 'INTERVAL' in event['rrule']:
                    event['rrule']['INTERVAL'] = int(event['rrule']['INTERVAL'])
                if 'UNTIL' in event['rrule']:
                    try:
                        event['rrule']['UNTIL'] = self._parse_date(event['rrule']['UNTIL'], dtzinfo)
                    except Exception, e:
                        logger.warning("Problem parsing: {0}: {1}".format(event['summary'], e))
                for par in event['rrule']:
                    kwargs[par.lower()] = event['rrule'][par]
                rr = dateutil.rrule.rrule(freq, **kwargs)
                for date in rr.between(start, end):
                    if date not in event['exdate']:
                        yield(date)

    def __call__(self, file, delta=1, offset=0):
        event = {}
        events = {}
        tzinfo = self._sh.tzinfo()
        now = self._sh.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=offset)
        end = start.replace(hour=23, minute=59, second=59) + datetime.timedelta(days=delta)
        if 'http://' in file:
            try:
                ical = urllib2.urlopen(file)
            except Exception, e:
                logger.error('Could not open ical file {0}: {1}'.format(file, e))
                return {}
        else:
            try:
                ical = open(file, 'r')
            except IOError, e:
                logger.error('Could not open ical file {0}: {1}'.format(file, e))
                return {}
        for line in ical.readlines():
            line = line.strip()
            if line == 'BEGIN:VEVENT':
                event = {'exdate': []}
            elif line == 'END:VEVENT':
                for dt in self._parse_event(event, tzinfo, start, end):
                    time = dt.time()
                    date = dt.date()
                    if date not in events:
                        events[date] = [[time, event['summary']]]
                    else:
                        events[date].append([time, event['summary']])
            elif line.startswith('TZID:'):
                key, sep, tz = line.partition(':')
                tzinfo = dateutil.tz.gettz(tz)
            else:
                key, sep, value = line.partition(':')
                key, sep, par = key.partition(';')
                key = key.upper()
                if key == 'DTSTART':
                    try:
                        event['start'] = self._parse_date(value, tzinfo, par)
                    except Exception, e:
                        logger.warning("Problem parsing: {0}: {1}".format(file, e))
                elif key == 'DTEND':
                    try:
                        event['end'] = self._parse_date(value, tzinfo, par)
                    except Exception, e:
                        logger.warning("Problem parsing: {0}: {1}".format(file, e))
                elif key == 'SUMMARY':
                    event['summary'] = value
                elif key == 'RRULE':
                    event['rrule'] = dict(a.split('=') for a in value.upper().split(';'))
                elif key == 'EXDATE':
                    try:
                        event['exdate'].append(self._parse_date(value, tzinfo, par))
                    except Exception, e:
                        logger.warning("Problem parsing: {0}: {1}".format(file, e))
        ical.close()
        return events
