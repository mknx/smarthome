#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.    http://mknx.github.io/smarthome/
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
import threading
import datetime
import time
import lib.log

logger = logging.getLogger('')


class MemLog():
    _log = None
    _items = {}

    def __init__(self, smarthome, name, mapping = ['time', 'thread', 'level', 'message'], items = [], maxlen = 50):
        self._sh = smarthome
        self.name = name
        self._log = lib.log.Log(smarthome, name, mapping, maxlen)
        self._items = items

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        if 'memlog' in item.conf and item.conf['memlog'] == self.name:
            return self.update_item
        else:
            return None

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'MemLog':
            if item.conf['memlog'] == self.name:
                if len(self._items) == 0:
                    log = [self._sh.now(), threading.current_thread().name, 'INFO', item()]
                else:
                    log = []
                    for item in self._items:
                        log.append(self._sh.return_item(item)())
                self._log.add(log)

