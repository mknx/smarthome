#!/usr/bin/env python
#
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
##########################################################################

import time
import sys
sys.path.append("/usr/local/smarthome")

import plugins.onewire

host = 'smart.home'
port = 4304

ow = plugins.onewire.Owconnection(host, port)
ow.connect()

old = []
while 1:
    new = ow.dir()
    dif = list(set(new)-set(old))
    for sensor in dif:
        try:
            typ = ow.read(sensor + 'type')
            print "new sensor: %s (%s)" % (sensor, typ)
        except Exception, e:
            pass
    old = new
    time.sleep(1)
