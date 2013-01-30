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

logger = logging.getLogger('')

try:
    import ephem
except ImportError, e:
    ephem = None

from dateutil.relativedelta import *
from dateutil.tz import tzutc


class Orb():

    def __init__(self, orb, lon, lat, elev=False):
        if ephem == None:
            return
        self._obs = ephem.Observer()
        self._obs.long = str(lon)
        self._obs.lat = str(lat)
        if elev:
            self._obs.elevation = int(elev)
        if orb == 'sun':
            self._orb = ephem.Sun()
        elif orb == 'moon':
            self._orb = ephem.Moon()
            self.phase = self._phase
            self.light = self._light

    def rise(self, offset=0, center=True):
        # workaround if rise is 0.001 seconds in the past
        self._obs.date = datetime.datetime.utcnow() + relativedelta(seconds=2)
        self._obs.horizon = str(offset)
        if offset != 0:
            next_rising = self._obs.next_rising(self._orb, use_center=center).datetime()
        else:
            next_rising = self._obs.next_rising(self._orb).datetime()
        return next_rising.replace(tzinfo=tzutc())

    def set(self, offset=0, center=True):
        # workaround if set is 0.001 seconds in the past
        self._obs.date = datetime.datetime.utcnow() + relativedelta(seconds=2)
        self._obs.horizon = str(offset)
        if offset != 0:
            next_setting = self._obs.next_setting(self._orb, use_center=center).datetime()
        else:
            next_setting = self._obs.next_setting(self._orb).datetime()
        return next_setting.replace(tzinfo=tzutc())

    def pos(self, offset=None):  # offset in minutes
        date = datetime.datetime.utcnow()
        if offset:
            date += relativedelta(minutes=offset)
        self._obs.date = date
        angle = self._orb.compute(self._obs)
        return (angle.az, angle.alt)

    def _light(self, offset=None):  # offset in minutes
        date = datetime.datetime.utcnow()
        if offset:
            date += relativedelta(minutes=offset)
        self._obs.date = date
        self._orb.compute(self._obs)
        return int(round(self._orb.moon_phase * 100))

    def _phase(self, offset=None):  # offset in minutes
        date = datetime.datetime.utcnow()
        cycle = 29.530588861
        if offset:
            date += relativedelta(minutes=offset)
        self._obs.date = date
        self._orb.compute(self._obs)
        last = ephem.previous_new_moon(self._obs.date)
        frac = (self._obs.date - last) / cycle
        return int(round(frac * 8))
