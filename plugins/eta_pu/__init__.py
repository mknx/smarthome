#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
#
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
#

import logging
import base64
import http.client
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

__ETA_PU__ = 'eta_pu'

logger = logging.getLogger(__ETA_PU__)


class ETA_PU():

    def __init__(self, smarthome, address, port, setpath, setname):
        self._sh = smarthome
        self._cycle = 30
        self._uri = dict()
        self._timeout = 2
        self._address = address
        self._port = port
        self._setpath = setpath
        self._setname = setname

    def __request__(self, req_type, url, timeout=2, username=None, password=None, value=None):
        lurl = url.split('/')
        # extract HOST http(s)://HOST/path/...
        host = lurl[2]
        # rebuild path from parts
        purl = '/' + '/'.join(lurl[3:])
        # select protocol: http or https
        if url.startswith('https'):
            conn = http.client.HTTPSConnection(host, timeout=timeout)
        else:
            conn = http.client.HTTPConnection(host, timeout=timeout)
        # add headers
        hdrs = {'Accept': 'text/plain'}
        if username and password:
            hdrs['Authorization'] = 'Basic ' + \
                base64.b64encode(username + ':' + password)

        if 'POST' == req_type:
            hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
            conn.request(req_type, purl,
                         urllib.parse.urlencode({'@value': value}), hdrs)
        elif 'PUT' == req_type:
            conn.request(req_type, purl, body=value, headers=hdrs)
        else:  # 'GET' or 'DELETE'
            conn.request(req_type, purl, headers=hdrs)
        resp = conn.getresponse()
        conn.close()
        # success status: 201/Created for PUT request, else 200/Ok
        if resp.status in (http.client.OK, http.client.CREATED):
            return resp.read()
        logger.warning("request failed: {0}: ".format(url))
        logger.debug(
            "{0} response: {1} {2}".format(req_type, resp.status, resp.reason))
        return None

    # build and request an URL
    def request(self, req_type, path, uri=None, value=None):
        url = 'http://' + self._address + ':' + self._port + path
        if uri:
            url += uri
        return self.__request__(req_type, url, self._timeout, value=value)

    # delete the default uri-set
    def del_set(self, name):
        rc = 'OK'
        if None is self.request('DELETE', '{0}/{1}'.format(self._setpath, name)):
            rc = 'FAILED'
        logger.info("deleting var_set named {0}: {1}".format(name, rc))

    # add an empty uri-set
    def add_set(self, name):
        rc = 'OK'
        if None is self.request('PUT', '{0}/{1}'.format(self._setpath, name)):
            rc = 'FAILED'
        logger.info("creating var_set named {0}: {1}".format(name, rc))

    # add the list of URIs to an existing varset
    def fill_set(self, var_set):
        for uri in self._uri:
            path = '/'.join((self._setpath, var_set, uri))
            rc = 'OK'
            if None is self.request('PUT', path):
                rc = 'FAILED'
            logger.info('adding {0}: {1}'.format(path, rc))

    def run(self):
        # del varset
        self.del_set(self._setname)
        # add varset
        self.add_set(self._setname)
        # fill varset
        self.fill_set(self._setname)
        # active updates
        self._sh.scheduler.add(
            __ETA_PU__, self.update_status, cycle=self._cycle)
        self.alive = True

    def stop(self):
        self.alive = False

    # for each item having an eta_pu_type entry
    # add the item to its parent URI
    def parse_item(self, item):
        if 'eta_pu_type' not in item.conf:
            return None
        parent_item = item.return_parent()
        if (parent_item is None) or (False == ('eta_pu_uri' in parent_item.conf)):
            logger.error(
                "skipping item: found 'eta_pu_type' but parent has no 'eta_pu_uri'")
            return
        uri = parent_item.conf['eta_pu_uri']
        if uri not in self._uri:
            self._uri[uri] = []
        self._uri[uri].append(item)
        return self.update_item

    def update_item(self, item, caller=None, source=None, dest=None):
        return None

    def update_status(self):
        url = 'http://' + self._address + ':' + \
            self._port + self._setpath + '/' + self._setname
        # read xml response
        xml = self._sh.tools.fetch_url(url, timeout=2)
        root = ET.fromstring(xml)

        for elem in root.iter():
            for key in list(self._uri.keys()):
                try:
                    if key == elem.attrib['uri']:
                        for i in self._uri[key]:
                            pu_type = i.conf['eta_pu_type']
                            i(elem.attrib[pu_type], caller='eta_pu')
                except:
                    pass
