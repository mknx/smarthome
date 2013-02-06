#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011-2013 KNX-User-Forum e.V.       http://knx-user-forum.de/
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
##########################################################################

import logging
import time
import datetime
import sys
import Queue
import threading
import os
import types
import random
import subprocess

from dateutil.relativedelta import *
from dateutil.tz import tzutc

logger = logging.getLogger('')


class Scheduler(threading.Thread):

    _workers = []
    _worker_num = 5
    _worker_max = 50
    _worker_delta = 60  # wait 60 seconds before adding another worker thread
    _scheduler = {}
    _runq = Queue.PriorityQueue()
    _triggerq = Queue.PriorityQueue()

    def __init__(self, smarthome):
        threading.Thread.__init__(self, name='Scheduler')
        logger.info('Init Scheduler')
        self._sh = smarthome
        self._lock = threading.Lock()

    def run(self):
        self.alive = True
        logger.debug("creating {0} workers".format(self._worker_num))
        for i in range(self._worker_num):
            self._add_worker()
        while self.alive:
            now = self._sh.now()
            if self._runq.qsize() > len(self._workers):
                delta = now - self._last_worker
                if delta.seconds > self._worker_delta:
                    if len(self._workers) < self._worker_max:
                        self._add_worker()
                    else:
                        logger.warning("Needing more worker threads than the specified maximum of {0}!".format(self._worker_max))
            while self._triggerq.qsize() > 0:
                try:
                    dt, prio, name, obj, by, source, value = self._triggerq.get()
                except Exception, e:
                    logger.warning("Trigger queue exception: {0}".format(e))
                    break

                if dt < now:  # run it
                    self._runq.put((prio, name, obj, by, source, value))
                else:  # put last entry back and break while loop
                    self._triggerq.put((dt, prio, name, obj, by, source, value))
                    break
            self._lock.acquire()
            for name in self._scheduler:
                task = self._scheduler[name]
                if task['next'] != None:
                    if task['next'] < now:
                        self._runq.put((task['prio'], name, task['obj'], 'Scheduler', None, task['value']))
                        task['next'] = None
                    else:
                        continue
                else:
                    if None == task['cron'] == task['cycle']:
                        continue
                    else:
                        self._next_time(name)
            self._lock.release()
            time.sleep(0.2)

    def stop(self):
        self.alive = False

    def trigger(self, name, obj=None, by='Logic', source=None, value=None, prio=3, dt=None):
        if obj == None:
            if name in self._scheduler:
                obj = self._scheduler[name]['obj']
            else:
                logger.warning("Logic name not found: {0}".format(name))
                return
        if dt == None:
            logger.debug("Triggering {0} - by: {1} source: {2} value: {3}".format(name, by, source, str(value)[:20]))
            self._runq.put((prio, name, obj, by, source, value))
        else:
            if not isinstance(dt, datetime.datetime):
                logger.warning("Trigger: Not a valid timezone aware datetime for {0}. Ignoring.".format(name))
                return
            if dt.tzinfo == None:
                logger.warning("Trigger: Not a valid timezone aware datetime for {0}. Ignoring.".format(name))
                return
            logger.debug("Triggering {0} - by: {1} source: {2} value: {3} at: {4}".format(name, by, source, value, dt))
            self._triggerq.put((dt, prio, name, obj, by, source, value))

    def remove(self, name):
        self._lock.acquire()
        if name in self._scheduler:
            del(self._scheduler[name])
        self._lock.release()

    def return_next(self, name):
        if name in self._scheduler:
            return self._scheduler[name]['next']

    def add(self, name, obj, prio=3, cron=None, cycle=None, value=None, offset=None):
        self._lock.acquire()
        if isinstance(cron, str):
            _cron = {}
            for entry in cron.split('|'):
                desc, sep, value = entry.partition('=')
                desc = desc.strip()
                if value != '':
                    value = value.strip()
                else:
                    value = None
                _cron[desc] = value
            cron = _cron
            if 'init' in cron and offset == None:
                offset = random.randint(1, 4)  # spread init jobs
        if isinstance(cycle, str):
            cycle, sep, value = cycle.partition('=')
            try:
                cycle = int(cycle.strip())
            except Exception, e:
                logger.warning("Scheduler: invalid cycle entry for {0} {1}".format(name, cycle))
                return
            if value != '':
                value = value.strip()
            else:
                value = None
            cycle = {cycle: value}
            if offset == None:
                offset = random.randint(10, 20)  # spread cycle jobs
        elif isinstance(cycle, int):
            cycle = {cycle: None}
            if offset == None:
                offset = random.randint(10, 20)  # spread cycle jobs
        self._scheduler[name] = {'prio': prio, 'obj': obj, 'cron': cron, 'cycle': cycle, 'value': value, 'next': None}
        self._next_time(name, offset)
        self._lock.release()

    def change(self, name, **kwargs):
        if name in self._scheduler:
            for key in kwargs:
                if key in self._scheduler[name]:
                    if key == 'cron':
                        if isinstance(kwargs[key], str):
                            kwargs[key] = kwargs[key].split('|')
                    self._scheduler[name][key] = kwargs[key]
                else:
                    logger.warning("Attribute {0} for {1} not specified. Could not change it.".format(key, name))
            if 'cycle' in kwargs or 'cron' in kwargs:
                self._next_time(name)
        else:
            logger.warning("Could not change {0}. No logic/method with this name found.".format(name))

    def _next_time(self, name, offset=None):
        job = self._scheduler[name]
        if None == job['cron'] == job['cycle']:
            self._scheduler[name]['next'] = None
            return
        next_time = None
        value = None
        now = self._sh.now()
        now = now.replace(microsecond=0)
        if job['cycle'] != None:
            cycle = job['cycle'].keys()[0]
            value = job['cycle'][cycle]
            if offset == None:
                offset = cycle
            next_time = now + relativedelta(seconds=offset)
        if job['cron'] != None:
            if 'init' in job['cron']:
                value = job['cron']['init']
                del self._scheduler[name]['cron']['init']
                if self._scheduler[name]['cron'] == {}:
                    self._scheduler[name]['cron'] = None
                self._scheduler[name]['next'] = now
                self._scheduler[name]['value'] = value
                return
            for entry in job['cron']:
                ct = self._crontab(entry)
                if next_time != None:
                    if ct < next_time:
                        next_time = ct
                        value = job['cron'][entry]
                else:
                    next_time = ct
                    value = job['cron'][entry]
        self._scheduler[name]['next'] = next_time
        self._scheduler[name]['value'] = value
        if name != 'sh.con':
            logger.debug("{0} next time: {1}".format(name, next_time))

    def __iter__(self):
        for job in self._scheduler:
            yield job

    def _add_worker(self):
        self._last_worker = self._sh.now()
        t = threading.Thread(target=self._worker)
        t.start()
        self._workers.append(t)
        if len(self._workers) > self._worker_num:
            logger.info("Adding worker thread. Total: {0}".format(len(self._workers)))

    def _worker(self):
        while self.alive:
            try:
                prio, name, obj, by, source, value = self._runq.get(timeout=0.5)
                self._runq.task_done()
            except Queue.Empty:
                continue
            self._task(name, obj, by, source, value)

    def _task(self, name, obj, by, source, value):
        threading.current_thread().name = name
        logger = logging.getLogger(name)
        if obj.__class__.__name__ == 'Logic':
            trigger = {'by': by, 'source': source, 'value': value}
            logic = obj
            sh = self._sh
            try:
                exec(obj.bytecode)
            except Exception, e:
                logger.warning("Logic {0} exception: {1}".format(name, e))
        elif obj.__class__.__name__ == 'Item':
            try:
                if value != None:
                    obj(value, caller="Scheduler")
            except Exception, e:
                logger.warning("Item {0} exception: {1}".format(name, e))
        else:  # method
            try:
                if value == None:
                    obj()
                else:
                    obj(**value)
            except Exception, e:
                logger.warning("Method {0} exception: {1}".format(name, e))

        threading.current_thread().name = 'idle'

    def _crontab(self, crontab):
        # process sunrise/sunset
        if crontab.startswith('sun'):
            return self._sun(crontab)

        minute, hour, day, wday = crontab.split(' ')
        # evaluate the crontab strings
        minute_range = self._range(minute, 00, 59)
        hour_range = self._range(hour, 00, 23)
        # FIXME fix day range for days > 28
        if wday == '*' and day == '*':
            day_range = self._day_range('0, 1, 2, 3, 4, 5, 6')
        elif wday != '*' and day == '*':
            day_range = self._day_range(wday)
        elif wday != '*' and day != '*':
            day_range = self._day_range(wday)
            day_range = day_range + self._range(day, 01, 28)
        else:
            day_range = self._range(day, 01, 28)

        # combine the differnt ranges
        event_range = sorted([str(day) + '-' + str(hour) + '-' + str(minute) for minute in minute_range for hour in hour_range for day in day_range])

        # find the next event
        now = self._sh.now()
        now_str = now.strftime("%d-%H-%M")
        next_event = self._next(lambda event: event > now_str, event_range)

        if next_event:  # found an event after today
            next_time = now
        else:  # skip to next month
            next_event = event_range[0]
            next_time = now + relativedelta(months=+1)
        day, hour, minute = next_event.split('-')
        next_time = next_time.replace(day=int(day), hour=int(hour), minute=int(minute), second=0, microsecond=0)
        return next_time

    def _next(self, f, seq):
        for item in seq:
            if f(item):
                return item

    def _sun(self, crontab):
        if not hasattr(self._sh, 'sun'):  # no sun object created
            logger.warning('No latitude/longitued specified. You could not use sunrise/sunset as crontab entry.')
            return datetime.datetime.now(tzutc()) + relativedelta(years=+10)

        offset = None
        tmp, op, os = crontab.rpartition('+')
        if op:
            offset = float(os)
        tmp, op, os = crontab.rpartition('-')
        if op:
            offset = -float(os)

        if crontab.startswith('sunrise'):
            next_time = self._sh.sun.rise(offset)
        elif crontab.startswith('sunset'):
            next_time = self._sh.sun.set(offset)
        else:
            logger.error('Wrong syntax. Should be (sunrise|sunset)[+|-][offset]')
            return datetime.datetime.now(tzutc()) + relativedelta(years=+10)

        return next_time

    def _range(self, entry, low, high):
        result = []
        item_range = []
        if entry == '*':
            item_range = range(low, high + 1)
        else:
            for item in entry.split(','):
                item_range.append(int(item))
        for entry in item_range:
            result.append('%0*d' % (2, entry))
        return result

    def _day_range(self, days):
        now = datetime.date.today()
        wdays = [MO, TU, WE, TH, FR, SA, SU]
        result = []
        for day in days.split(','):
            wday = wdays[int(day)]
            # add next weekday occurence
            day = now + relativedelta(weekday=wday)
            result.append(day.strftime("%d"))
            # safety add-on if weekday equals todays weekday
            day = now + relativedelta(weekday=wday(+2))
            result.append(day.strftime("%d"))
        return result
