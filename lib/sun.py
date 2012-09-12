#!/usr/bin/env python
#
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
import datetime

import ephem
from dateutil.relativedelta import *
from dateutil.tz import tzutc

logger = logging.getLogger('')

class Sun():

    def __init__(self, lon, lat, elev):
        self.obs = ephem.Observer()
        self.obs.long = str(lon)
        self.obs.lat = str(lat)
        if elev:
            self.obs.elevation = int(elev)
        self.sun = ephem.Sun()

    def rise(self, offset=0, center=True):
        # workaround if rise is 0.001 seconds in the past
        self.obs.date = datetime.datetime.utcnow() + relativedelta(seconds=2)
        self.obs.horizon = str(offset)
        if offset != 0:
            next_rising = self.obs.next_rising(self.sun, use_center=center).datetime()
        else:
            next_rising = self.obs.next_rising(self.sun).datetime()
        return next_rising.replace(tzinfo=tzutc())

    def set(self, offset=0, center=True):
        # workaround if set is 0.001 seconds in the past
        self.obs.date = datetime.datetime.utcnow() + relativedelta(seconds=2)
        self.obs.horizon = str(offset)
        if offset != 0:
            next_setting = self.obs.next_setting(self.sun, use_center=center).datetime()
        else:
            next_setting = self.obs.next_setting(self.sun).datetime()
        return next_setting.replace(tzinfo=tzutc())

    def pos(self, offset=None): # offset in minutes
        now = datetime.datetime.utcnow()
        if offset:
            self.obs.date = now + relativedelta(minutes=offset)
        else:
            self.obs.date = now
        angle = ephem.Sun(self.obs)
        return (angle.az, angle.alt)

