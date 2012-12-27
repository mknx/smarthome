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

import collections


class Log(collections.deque):

    def __init__(self, smarthome, name, log_string, maxlen=50):
        collections.deque.__init__(self, maxlen=maxlen)
        self.log_string = log_string
        self.update_hooks = []
        self._sh = smarthome
        self._name = name
        smarthome.add_log(name, self)

    def add(self, entry):
        self.append(entry)
        print "new: {0}".format(entry)
        for listener in self._sh.return_listeners():
            listener(['log', [self._name, [self.log_string.format(*entry)]]])


    def last(self, number):
        return(list(self)[-number:])

    def export(self, number):
        return map(lambda x: self.log_string.format(*x), list(self)[:number])
