#!/usr/bin/env python
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
#########################################################################

import logging
import time
import asynchat
import asyncore
import socket
import threading
import urllib

logger = logging.getLogger('')


class TCPHandler(asynchat.async_chat):

    terminator = '\n'

    def __init__(self, socket_map, parser, dest, sock, source):
        asynchat.async_chat.__init__(self, sock=sock, map=socket_map)
        self.parser = parser
        self._lock = threading.Lock()
        self.dest = dest
        self.buffer = ''
        self.source = source

    def initiate_send(self):
        self._lock.acquire()
        asynchat.async_chat.initiate_send(self)
        self._lock.release()

    def collect_incoming_data(self, data):
        self.buffer += data

    def found_terminator(self):
        data = self.buffer
        self.buffer = ''
        self.parser(self.source, self.dest, data.strip())
        self.close()


class TCPDispatcher(asyncore.dispatcher):

    def __init__(self, parser, socket_map, ip, port):
        asyncore.dispatcher.__init__(self, map=socket_map)
        self.socket_map = socket_map
        self.parser = parser
        self.dest = 'tcp:' + ip + ':' + port
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind((ip, int(port)))
            self.listen(5)
            self.listening = True
        except Exception, e:
            logger.error("Could not bind TCP socket on %s:%s" % (ip, port))
            self.listening = False

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, (ip, port) = pair
            logger.debug('%s Incoming connection from %s:%s' % (self.dest, ip, port))
            TCPHandler(self.socket_map, self.parser, self.dest, sock, ip)


class HTTPHandler(asynchat.async_chat):

    terminator = "\r\n\r\n"

    def __init__(self, socket_map, parser, dest, sock, source):
        asynchat.async_chat.__init__(self, sock=sock, map=socket_map)
        self.parser = parser
        self._lock = threading.Lock()
        self.dest = dest
        self.buffer = ''
        self.source = source

    def initiate_send(self):
        self._lock.acquire()
        asynchat.async_chat.initiate_send(self)
        self._lock.release()

    def collect_incoming_data(self, data):
        self.buffer += data

    def found_terminator(self):
        data = self.buffer
        self.buffer = ''
        for line in data.splitlines():
            if line.startswith('GET'):
                request = line.split(' ')[1].strip('/')
                self.parser(self.source, self.dest, urllib.unquote(request))
                break
        self.close()


class HTTPDispatcher(asyncore.dispatcher):

    def __init__(self, parser, socket_map, ip, port):
        asyncore.dispatcher.__init__(self, map=socket_map)
        self.socket_map = socket_map
        self.parser = parser
        self.dest = 'http:' + ip + ':' + port
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind((ip, int(port)))
            self.listen(5)
            self.listening = True
        except Exception, e:
            logger.error("Could not bind TCP socket for HTTP on %s:%s" % (ip, port))
            self.listening = False

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, (ip, port) = pair
            logger.debug('%s Incoming connection from %s:%s' % (self.dest, ip, port))
            HTTPHandler(self.socket_map, self.parser, self.dest, sock, ip)


class UDPDispatcher(asyncore.dispatcher):

    def __init__(self, parser, socket_map, ip, port):
        asyncore.dispatcher.__init__(self, map=socket_map)
        self.dest = 'udp:' + ip + ':' + port
        self.parser = parser
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.set_reuse_addr()
            self.bind((ip, int(port)))
            self.listening = True
        except Exception, e:
            logger.error("Could not bind UDP socket on %s:%s" % (ip, port))
            self.listening = False

    def handle_read(self):
        data, (ip, port) = self.recvfrom(4096)
        logger.debug('%s Incoming connection from %s:%s' % (self.dest, ip, port))
        self.parser(ip, self.dest, data.strip())

    def writable(self):
        return False


class UDPSend(asyncore.dispatcher_with_send):

    def __init__(self, socket_map, host, port, data):
        asyncore.dispatcher_with_send.__init__(self, map=socket_map)
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.connect((host, int(port)))
        except Exception, e:
            logger.warning("Could not connect to %s:%s, to send data: %s." % (host, port, data))
            return
        self.send(data)

    def writable(self):
        if len(self.out_buffer) > 0 and self.connected:
            return True
        else:
            self.close()
            return False

    def readable(self):
        return False

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()


class Network():

    generic_listeners = {}
    special_listeners = {}
    input_seperator = '|'
    socket_warning = 10
    socket_warning = 2

    def __init__(self, smarthome, ip='0.0.0.0', port='2727', udp='no', tcp='no', http='no', udp_acl='*', tcp_acl='*', http_acl='*'):
        self._sh = smarthome
        self.socket_map = smarthome.socket_map
        self.tcp_acl = self.parse_acl(tcp_acl)
        self.udp_acl = self.parse_acl(udp_acl)
        self.http_acl = self.parse_acl(http_acl)
        if tcp == 'yes':
            self.add_listener('tcp', ip, port, tcp_acl, generic=True)
        if udp == 'yes':
            self.add_listener('udp', ip, port, udp_acl, generic=True)
        if http != 'no':
            self.add_listener('http', ip, http, http_acl, generic=True)

    # XXX
    #def tcp(self, host, port, data):
    #    self._send_data('tcp', host, port, data)

    def udp(self, host, port, data):
        UDPSend(self.socket_map, host, port, data)

    def add_listener(self, proto, ip, port, acl='*', generic=False):
        dest = proto + ':' + ip + ':' + port
        logger.debug("Adding listener on: %s" % dest)
        if proto == 'tcp':
            dispatcher = TCPDispatcher(self.parse_input, self.socket_map, ip, port)
        elif proto == 'udp':
            dispatcher = UDPDispatcher(self.parse_input, self.socket_map, ip, port)
        elif proto == 'http':
            dispatcher = HTTPDispatcher(self.parse_input, self.socket_map, ip, port)
        else:
            return
        if not dispatcher.listening:
            return False
        acl = self.parse_acl(acl)
        if generic:
            self.generic_listeners[dest] = {'items': {}, 'logics': {}, 'acl': acl}
        else:
            self.special_listeners[dest] = {'items': {}, 'logics': {}, 'acl': acl}
        return True

    def parse_acl(self, acl):
        if acl == '*':
            return False
        if isinstance(acl, str):
            return [acl]
        return acl

    def parse_input(self, source, dest, data):
        if dest in self.generic_listeners:
            inp = data.split(self.input_seperator, 2)  # max 3 elements
            if len(inp) < 3:
                logger.info("Ignoring input %s. Format not recognized." % data)
                return False
            typ, name, value = inp
            gacl = self.generic_listeners[dest]['acl']
            if typ == 'item':
                if name not in self.generic_listeners[dest]['items']:
                    logger.error("Item '%s' not available in the generic listener." % name)
                    return False
                iacl = self.generic_listeners[dest]['items'][name]['acl']
                if iacl:
                    if source not in iacl:
                        logger.error("Item '%s' acl doesn't permit updates from %s." % (name, source))
                        return False
                elif gacl:
                    if source not in gacl:
                        logger.error("Generic network acl doesn't permit updates from %s." % (source))
                        return False
                item = self.generic_listeners[dest]['items'][name]['item']
                item(value, 'network', source)

            elif typ == 'logic':
                if name not in self.generic_listeners[dest]['logics']:
                    logger.error("Logic '%s' not available in the generic listener." % name)
                    return False
                lacl = self.generic_listeners[dest]['logics'][name]['acl']
                if lacl:
                    if source not in lacl:
                        logger.error("Logic '%s' acl doesn't permit triggering from %s." % (name, source))
                        return False
                elif gacl:
                    if source not in gacl:
                        logger.error("Generic network acl doesn't permit triggering from %s." % (source))
                        return False
                logic = self.generic_listeners[dest]['logics'][name]['logic']
                logic.trigger('network', source, value)

            elif typ == 'log':
                if gacl:
                    if source not in gacl:
                        logger.error("Generic network acl doesn't permit log entries from %s." % (source))
                        return False
                if name == 'info':
                    logger.info(value)
                elif name == 'warning':
                    logger.warning(value)
                elif name == 'error':
                    logger.error(value)
                else:
                    logger.warning("Unknown logging priority '%s'. Data: '%s'" % (name, data))
            else:
                logger.error("Unsupporter key element %s. Data: %s" % (typ, data))
                return False
        elif dest in self.special_listeners:
            proto, t1, t2 = dest.partition(':')
            if proto == 'udp':
                gacl = self.udp_acl
            elif proto == 'tcp':
                gacl = self.tcp_acl
            else:
                return
            for entry in self.special_listeners[dest]['logics']:
                lacl = self.special_listeners[dest]['logics'][entry]['acl']
                logic = self.special_listeners[dest]['logics'][entry]['logic']
                if lacl:
                    if source not in lacl:
                        logger.error("Logic '%s' acl doesn't permit triggering from %s." % (logic.name, source))
                        return False
                elif gacl:
                    if source not in gacl:
                        logger.error("Generic network acl doesn't permit triggering from %s." % (source))
                        return False
                logic.trigger('network', source, data)
        else:
            logger.error("Destination %s, not in listeners!" % dest)
            return False

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False

    def parse_logic(self, logic):
        self.parse_obj(logic, 'logic')

    def parse_item(self, item):
        self.parse_obj(item, 'item')

    def parse_obj(self, obj, obj_type):
        # nw_acl, nw_udp, nw_tcp
        if obj_type == 'item':
            oid = obj.id()
        elif obj_type == 'logic':
            oid = obj.id()
        else:
            return

        if 'nw_acl' in obj.conf:
            acl = obj.conf['nw_acl']
        else:
            acl = False

        if 'nw' in obj.conf:  # adding object to generic listeners
            if self._sh.string2bool(obj.conf['nw']):
                for dest in self.generic_listeners:
                    self.generic_listeners[dest][obj_type + 's'][oid] = {obj_type: obj, 'acl': acl}

        if 'nw_udp_listen' in obj.conf:
            ip, sep, port = obj.conf['nw_udp_listen'].rpartition(':')
            if not ip:
                ip = '0.0.0.0'
            dest = 'udp:' + ip + ':' + port
            if dest not in self.special_listeners:
                if self.add_listener('udp', ip, port):
                    self.special_listeners[dest][obj_type + 's'][oid] = {obj_type: obj, 'acl': acl}
                else:
                    logger.warning("Could not add listener %s for %s" % (dest, oid))
            else:
                self.special_listeners[dest][obj_type + 's'][oid] = {obj_type: obj, 'acl': acl}

        if 'nw_tcp_listen' in obj.conf:
            ip, sep, port = obj.conf['nw_tcp_listen'].rpartition(':')
            if not ip:
                ip = '0.0.0.0'
            dest = 'tcp:' + ip + ':' + port
            if dest not in self.special_listeners:
                if self.add_listener('tcp', ip, port):
                    self.special_listeners[dest][obj_type + 's'][oid] = {obj_type: obj, 'acl': acl}
                else:
                    logger.warning("Could not add listener %s for %s" % (dest, oid))
            else:
                self.special_listeners[dest][obj_type + 's'][oid] = {obj_type: obj, 'acl': acl}
