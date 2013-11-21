#!/usr/bin/env python3
#
###############################################################################
# Copyright (c) 2013 Marcus Popp
###############################################################################
#
#  This file is part of SmartHome.py.    http://mknx.github.io/smarthome/
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

"""

.. module:: wol
.. moduleauthor:: Marcus Popp <marcus@popp.mx>

"""

import logging
import socket

logger = logging.getLogger('')


class WOL():
    """This is a Wake On LAN Plugin.

        :param smarthome: reference to the root object
        :param host: the IP address or host name to connect to
        :param port: port number of the host to connect to

        """
    def __init__(self, smarthome):
        self._sh = smarthome

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        if 'wol_mac' in item.conf:
            mac = ''.join([p.zfill(2) for p in item.conf['wol_mac'].replace(':', ' ').split()])
            mac = bytearray.fromhex(mac)
            if len(mac) == 6:
                item.conf['wol_mac'] = mac
                return self.update_item
            else:
                logger.warning("WOL: {} mac address invalid!".format(item.id()))
                return None
        else:
            return None

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None, dest=None):
        if item():
            if 'wol_mac' in item.conf:
                mac = item.conf['wol_mac']
                magic = bytearray([255] * 6)
                magic.extend(mac * 16)
                try:
                    _s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    _s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    _s.connect('255.255.255.255', 9)
                    _s.sendall(magic)
                except:
                    pass
                finally:
                    try:
                        _s.close()
                    except:
                        pass
