#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2011 KNX-User-Forum e.V.           http://knx-user-forum.de/
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

import json
import requests

logger = logging.getLogger("Pushbullet")

class Pushbullet():
    _apiurl = "https://api.pushbullet.com/api/pushes"
    
    def __init__(self, smarthome, apikey=None, deviceid=None):
        self._apikey = apikey
        self._deviceid = deviceid
        self._sh = smarthome

    def run(self):
        pass

    def stop(self):
        pass

    def note(self, title, body, deviceid=None, apikey=None):
        self._push(data={"type": "note", "title": title, "body": body}, deviceid=deviceid, apikey=apikey)

    def link(self, title, url, apikey=None):
        self._push(data={"type": "link", "url": url, "body": body}, deviceid=deviceid, apikey=apikey)

    def address(self, name, address, apikey=None):
        self._push(data={"type": "address", "name": name, "address": address}, deviceid=deviceid, apikey=apikey)

    def list(self, title, items, apikey=None):
        self._push(data={"type": "list", "title": title, "items": items}, deviceid=deviceid, apikey=apikey)

    def file(self, filepath, apikey=None):
        self._push(data={"type": "file"}, file={"file": open(filepath, "rb")}, deviceid=deviceid, apikey=apikey)

    def _push(self, data, deviceid=deviceid, apikey=None, file={}):
        data["device_iden"] = self._deviceid
        if deviceid:
            data["device_iden"] = deviceid
        
        headers = {"User-Agent": "SmartHome.py"}
        if not file:
            headers["Content-Type"] = "application/json"
        
        try:
            response = requests.post(self._apiurl, data=json.dumps(data), headers=headers, files=file, auth=(self._apikey, ""))
            if (response.status_code == 200):
                logger.debug("Pushbullet returns: Notification submitted.")
            elif (response.status_code == 400):
                logger.warning("Pushbullet returns: Bad Request - Often missing a required parameter.")
            elif (response.status_code == 401):
                logger.warning("Pushbullet returns: Unauthorized - No valid API key provided.")
            elif (response.status_code == 402):
                logger.warning("Pushbullet returns: Request Failed - Parameters were valid but the request failed.")
            elif (response.status_code == 403):
                logger.warning("Pushbullet returns: Forbidden - The API key is not valid for that request.")
            elif (response.status_code == 404):
                logger.warning("Pushbullet returns: Not Found - The requested item doesn't exist.")
            elif (response.status_code >= 500):
                logger.warning("Pushbullet returns: Server errors - something went wrong on PushBullet's side.")
            else:
                logger.error("Pushbullet returns unknown HTTP status code = {0}".format(response.status_code))
        except Exception as e:
            logger.warning("Could not send Pushbullet notification. Error: {0}".format(e))
