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

    def push_note(self, title, body, apikey=None):
        self._push({"type": "note", "title": title, "body": body}, apikey)

    def push_link(self, title, url, apikey=None):
        self._push({"type": "link", "url": url, "body": body}, apikey)

    def push_address(self, name, address, apikey=None):
        self._push({"type": "address", "name": name, "address": address}, apikey)

    def push_list(self, title, items, apikey=None):
        self._push({"type": "list", "title": title, "items": items}, apikey)

    def push_file(self, filepath, apikey=None):
        self._push({"type": "file"}, apikey, {"file": open(filepath, "rb")})

    def _push(self, data, apikey=None, file={}):
        data["device_iden"] = self._deviceid
        headers = {"User-Agent": "SmartHome.py"}
        if not file:
            headers["Content-Type"] = "application/json"
        try:
            resp = requests.post(self._apiurl, data=json.dumps(data), headers=headers, files=file, auth=(self._apikey, ""))
            if (resp.status_code == 200):
                logger.debug("Pushbullet returns: Notification submitted.")
            elif (resp.status_code == 400):
                logger.warning("Pushbullet returns: Bad Request - Often missing a required parameter.")
                logger.warning("Response text: {0}".format(resp.text))
            elif (resp.status_code == 401):
                logger.warning("Pushbullet returns: Unauthorized - No valid API key provided.")
                logger.warning("Response text: {0}".format(resp.text))
            elif (resp.status_code == 402):
                logger.warning("Pushbullet returns: Request Failed - Parameters were valid but the request failed.")
                logger.warning("Response text: {0}".format(resp.text))
            elif (resp.status_code == 403):
                logger.warning("Pushbullet returns: Forbidden - The API key is not valid for that request.")
                logger.warning("Response text: {0}".format(resp.text))
            elif (resp.status_code == 404):
                logger.warning("Pushbullet returns: Not Found - The requested item doesn't exist.")
                logger.warning("Response text: {0}".format(resp.text))
            elif (resp.status_code >= 500):
                logger.warning("Pushbullet returns: Server errors - something went wrong on PushBullet's side.")
                logger.warning("Response text: {0}".format(resp.text))
            else:
                logger.error("Pushbullet returns unknown HTTP status code = {0}".format(resp.status_code))
                logger.warning("Response text: {0}".format(resp.text))
        except Exception as e:
            logger.warning("Could not send Pushbullet notification. Error: {0}".format(e))
