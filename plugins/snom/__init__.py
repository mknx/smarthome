#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012-2013 KNX-User-Forum e.V.       http://knx-user-forum.de/
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
import base64
import xml.etree.cElementTree

logger = logging.getLogger('')


class Snom():

    def __init__(self, smarthome, username=None, password=None, phonebook=None):
        self._sh = smarthome
        self._phonebook = phonebook
        self._username = username
        self._password = password

    def run(self):
        self.alive = True
        # if you want to create child threads, do not make them daemon = True!
        # They will not shutdown properly. (It's a python bug)

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        if 'snom_key' in item.conf:
            logger.debug("parse item: {0}".format(item))
            if 'snom_host' in item.conf:
                return self.update_item
            else:
                parent = item.return_parent()
                if hasattr(parent, 'conf'):
                    if 'snom_host' in parent.conf:
                        item.conf['snom_host'] = parent.conf['snom_host']
                        return self.update_item
            logger.warning("No 'snom_host' specified for {0}".format(item.id()))

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None):
        if caller != 'HTTP':
            uri = "https://{0}/dummy.htm".format(item.conf['snom_host'])
            try:
                req = urllib2.Request("{0}?settings=save&store_settings=save&{1}={2}".format(uri, item.conf['snom_key'], urllib.quote(str(item()))))
                req.add_header('Authorization', 'Basic ' + base64.b64encode(self._username + ':' + self._password))
                u = urllib2.urlopen(req, timeout=2)
                u.fp._sock.recv = None
                u.close()
                del(u, req)
            except Exception, e:
                logger.warning("Error updating Snom Phone ({0}): {1}".format(item.conf['snom_host'], e))

    def phonebook_add(self, name, number):
        if self._phonebook is None:
            logger.warning("Snom: No Phonebook specified")
            return
        root = xml.etree.cElementTree.Element('SnomIPPhoneDirectory')
        root.text = "\n"
        tree = xml.etree.cElementTree.ElementTree(root)
        try:
            root = tree.parse(self._phonebook)
        except IOError, e:
            logger.warning("Could not read {0}: {1}".format(self._phonebook, e))
        except Exception, e:
            logger.warning("Problem reading {0}: {1}".format(self._phonebook, e))
            return
        found = False
        for entry in tree.findall('DirectoryEntry'):
            ename = entry.findtext('Name')
            if ename == name:
                # update number
                entry.find('Telephone').text = number
                found = True
        if not found:
            # add new element
            new = xml.etree.cElementTree.SubElement(tree.getroot(), 'DirectoryEntry')
            new.tail = "\n"
            xml.etree.cElementTree.SubElement(new, 'Name').text = name
            xml.etree.cElementTree.SubElement(new, 'Telephone').text = number
            # sort
            data = []
            for entry in tree.findall('DirectoryEntry'):
                key = entry.findtext("Name")
                data.append((key, entry))
            data.sort()
            root[:] = [item[-1] for item in data]
        try:
            tree.write(self._phonebook, encoding="UTF-8", xml_declaration=True)
        except Exception, e:
            logger.warning("Problem writing {0}: {1}".format(self._phonebook, e))
