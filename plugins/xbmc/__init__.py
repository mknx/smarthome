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

import logging
import json

logger = logging.getLogger('')

import lib.my_asynchat


class XBMC(lib.my_asynchat.AsynChat):

    _notification_time = 10000

    def __init__(self, smarthome, host, port=9090):
        lib.my_asynchat.AsynChat.__init__(self, smarthome, host, port)
        self._sh = smarthome
        smarthome.monitor_connection(self)
        self._id = 0

    def run(self):
        self.alive = True

    def _send(self, method, params):
        self._id += 1
        data = {"jsonrpc": "2.0", "id": self._id, "method": method, 'params': params}
        self.push(json.dumps(data, separators=(',',':')))

    def notify(self, title, message):
        self._send('GUI.ShowNotification', {'title': title, 'message': message, 'displaytime': self._notification_time})

    def stop(self):
        self.alive = False
