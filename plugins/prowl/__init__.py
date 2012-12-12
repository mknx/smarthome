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
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import urllib
import urllib2

# prowl notifications
logger = logging.getLogger('Prowl')


class Prowl():
    _apiuri = 'https://api.prowlapp.com/publicapi/add'

    def __init__(self, smarthome, apikey=None):
        self._apikey = apikey

    def run(self):
        pass

    def stop(self):
        pass

    def __call__(self, event='', description='', priority=None, url=None, apikey=None, application='SmartHome'):
        data = {}
        data['event'] = event[:1024].encode('utf-8')
        data['description'] = description[:10000].encode('utf-8')
        data['application'] = application[:256].encode('utf-8')
        if apikey:
            data['apikey'] = apikey
        else:
            data['apikey'] = self._apikey
        if priority:
            data['priority'] = priority
        if url:
            data['url'] = url[:512]

        try:
            p = urllib2.urlopen(self._apiuri, urllib.urlencode(data), 4)
            p.read(1)
            p.fp._sock.recv=None
            p.close()
            del(p)
        except Exception, e:
            logger.warning("Could not send prowl notification: {0}. Error: {1}".format(event, e))
