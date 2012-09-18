#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011 KNX-User-Forum e.V.            http://knx-user-forum.de/
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

import configobj
import ephem
from dateutil.relativedelta import *
from dateutil.tz import tzutc

logger = logging.getLogger('')


class Logics():

    def __init__(self, smarthome, configfile):
        logger.info('Starting logics')
        self._sh = smarthome
        self._workers = []
        self._logics = {}
        self._bytecode = {}
        _num_workers = 10
        self.runq = Queue.PriorityQueue()
        self.alive = True

        logger.debug("reading logics from %s" % configfile)
        try:
            self._config = configobj.ConfigObj(configfile, file_error=True)
        except Exception, e:
            logger.critical(e)
            sys.exit(0)

        for name in self._config:
            #logger.debug("Logic: %s" % name)
            logic = Logic(self._sh, name, self._config[name])
            self._logics[name] = logic
            if hasattr(logic, 'bytecode'):
                self._sh.scheduler.add(name, logic, logic.prio, logic.crontab, logic.cycle)
            else:
                return

            # plugin hook
            for plugin in self._sh._plugins:
                if hasattr(plugin, 'parse_logic'):
                    plugin.parse_logic(logic)

            # item hook
            if hasattr(logic, 'watch_item'):
                for watch_item in logic.watch_item:
                    item = self._sh.return_item(watch_item)
                    if item != None:
                        item.add_logic_trigger(logic)

    def __iter__(self):
        for logic in self._logics:
            yield logic


class Logic():

    def __init__(self, smarthome, name, attributes):
        self._sh = smarthome
        self.name = name
        self.crontab = None
        self.cycle = None
        self.prio = 3
        self.last = None
        self.conf = attributes
        for attribute in attributes:
            vars(self)[attribute] = attributes[attribute]
        self._generate_bytecode()
        if hasattr(self, 'watch_item'):
            if isinstance(self.watch_item, str):
                self.watch_item = [self.watch_item, ]
        self.prio = int(self.prio)
        if self.cycle != None:
            self.cycle = float(self.cycle)
        if self.crontab != None:
            if isinstance(self.crontab, list):
                self.crontab = ','.join(self.crontab)
            self.crontab = self.crontab.split('|')
            self.crontab = [x.strip() for x in self.crontab]

    def id(self):
        return self.name

    def trigger(self, by='Logic', source=None, value=None, dt=None):
        self._sh.scheduler.trigger(self.name, self, prio=self.prio, by=by, source=source, value=value, dt=dt)

    def _generate_bytecode(self):
        if hasattr(self, 'filename'):
            filename = '/usr/local/smarthome/logics/' + self.filename
            if not os.access(filename, os.R_OK):
                logger.warning("%s: Could not access logic file (%s) => ignoring." % (self.name, self.filename))
                return
            try:
                self.bytecode = compile(open(filename).read(), self.filename, 'exec')
            except Exception, e:
                logger.warning("Exception: %s" % e)
        else:
            logger.warning("%s: No filename specified => ignoring." % self.name)
