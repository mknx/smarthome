#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.   http://mknx.github.com/smarthome/
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

# nma notifications
logger = logging.getLogger('NMA')


class NMA():
    _apiuri = 'https://www.notifymyandroid.com/publicapi/notify'

    def __init__(self, smarthome, apikey=None):
        self._apikey = apikey

    def run(self):
        pass

    def stop(self):
        pass

    def __call__(self, event='', description='', priority=None, url=None, apikey=None, application='SmartHome'):
        data = {}
        if apikey:
            data['apikey'] = apikey
        else:
            data['apikey'] = self._apikey
        data['application'] = application[:256].encode('utf-8')
        data['event'] = event[:1000].encode('utf-8')
        data['description'] = description[:1000].encode('utf-8')
        if priority:
            data['priority'] = priority
        if url:
            data['url'] = url[:2000]

        try:
            p = urllib2.urlopen(self._apiuri, urllib.urlencode(data), 4)
            status_code = p.getcode()
            if (status_code == 200):
                logger.debug("NMA returns: Notification submitted.")
            elif (status_code == 400):
                logger.warning("NMA returns: The data supplied is in the wrong format, invalid length or null.")
            elif (status_code == 401):
                logger.warning("NMA returns: None of the API keys provided were valid.")
            elif (status_code == 402):
                logger.warning("NMA returns: Maximum number of API calls per hour exceeded.")
            elif (status_code == 500):
                logger.warning("NMA returns: Internal server error. Please contact our support if the problem persists.")
            else:
                logger.error("NAME returns unknown HTTP status code = {0}".format(p.getcode()))
            p.read(1)
            p.fp._sock.recv = None
            p.close()
            del(p)
        except Exception, e:
            logger.warning("Could not send NMA notification: {0}. Error: {1}".format(event, e))
