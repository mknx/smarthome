#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012-2013 Marcus Popp
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
#########################################################################

import logging
import asynchat
import asyncore
import socket
import threading

logger = logging.getLogger('')


class CLIHandler(asynchat.async_chat):
    terminator = '\n'

    def __init__(self, smarthome, sock, source, updates):
        asynchat.async_chat.__init__(self, sock=sock, map=smarthome.socket_map)
        self.source = source
        self.updates_allowed = updates
        self.sh = smarthome
        self._lock = threading.Lock()
        self.buffer = ''
        self.push("SmartHome.py v%s\n" % self.sh.version)
        self.push("> ")

    def collect_incoming_data(self, data):
        self.buffer += data

    def initiate_send(self):
        self._lock.acquire()
        asynchat.async_chat.initiate_send(self)
        self._lock.release()

    def found_terminator(self):
        cmd = self.buffer.strip()
        self.buffer = ''
        if cmd.startswith('ls'):
            self.push("Items:\n======\n")
            self.ls(cmd.lstrip('ls').strip())
        elif cmd == 'la':
            self.la()
        elif cmd == 'lo':
            self.lo()
        elif cmd == 'cl':
            self.cl()
        elif cmd.startswith('update ') or cmd.startswith('up '):
            self.update(cmd.lstrip('update').strip())
        elif cmd.startswith('tr'):
            self.tr(cmd.lstrip('tr').strip())
        elif cmd.startswith('rl'):
            self.rl(cmd.lstrip('rl').strip())
        elif cmd.startswith('rr'):
            self.rr(cmd.lstrip('rr').strip())
        elif cmd == 'help' or cmd == 'h':
            self.usage()
        elif cmd in ('quit', 'q', 'exit', 'x'):
            self.push('bye\n')
            try:
                self.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.close()
            except:
                pass
            return
        self.push("> ")

    def cl(self):
        self.sh.log.clean(self.sh.now())

    def ls(self, path):
        if not path:
            for item in self.sh:
                self.push("{0}\n".format(item.id()))
        else:
            item = self.sh.return_item(path)
            if hasattr(item, 'id'):
                if item._type:
                    self.push(u"{0} = {1}\n".format(item.id(), item()))
                else:
                    self.push("%s\n" % (item.id()))
                for child in item:
                    self.ls(child.id())
            else:
                self.push("Could not find path: %s\n" % (path))

    def la(self):
        self.push("Items:\n======\n")
        for item in self.sh.return_items():
            if item._type:
                self.push(u"{0} = {1}\n".format(item.id(), item()))
            else:
                self.push("{0}\n".format(item.id()))

    def update(self, data):
        if not self.updates_allowed:
            self.push("Updating items is not allowed.\n")
            return
        path, sep, value = data.partition('=')
        path = path.strip()
        value = value.strip()
        if not value:
            self.push("You have to specify an item value. Syntax: up item = value\n")
            return
        item = self.sh.return_item(path)
        if not hasattr(item, '_type'):
            self.push("Could not find item with a valid type specified: '{0}'\n".format(path))
            return
        item(value, 'CLI', self.source)

    def tr(self, logic):
        if not self.updates_allowed:
            self.push("Logic triggering is not allowed.\n")
            return
        if logic in self.sh.return_logics():
            self.sh.trigger(logic, by='CLI')
        else:
            self.push("Logic '{0}' not found.\n".format(logic))

    def rl(self, name):
        if not self.updates_allowed:
            self.push("Logic triggering is not allowed.\n")
            return
        if name in self.sh.return_logics():
            logic = self.sh.return_logic(name)
            logic.generate_bytecode()
        else:
            self.push("Logic '{0}' not found.\n".format(name))

    def rr(self, name):
        if not self.updates_allowed:
            self.push("Logic triggering is not allowed.\n")
            return
        if name in self.sh.return_logics():
            logic = self.sh.return_logic(name)
            logic.generate_bytecode()
            logic.trigger(by='CLI')
        else:
            self.push("Logic '{0}' not found.\n".format(name))

    def lo(self):
        self.push("Logics:\n")
        for logic in self.sh.return_logics():
            nt = self.sh.scheduler.return_next(logic)
            if nt is not None:
                self.push("{0} (scheduled for {1})\n".format(logic, nt.strftime('%Y-%m-%d %H:%M:%S%z')))
            else:
                self.push("{0}\n".format(logic))

    def usage(self):
        self.push('cl: clean (memory) log\n')
        self.push('ls: list the first level items\n')
        self.push('ls item: list item and every child item (with values)\n')
        self.push('la: list all items (with values)\n')
        self.push('lo: list all logics and next execution time\n')
        self.push('update item = value: update the specified item with the specified value\n')
        self.push('up: alias for update\n')
        self.push('tr logic: trigger logic\n')
        self.push('rl logic: reload logic\n')
        self.push('rr logic: reload and run logic\n')
        self.push('quit: quit the session\n')
        self.push('q: alias for quit\n')


class CLI(asyncore.dispatcher):

    def __init__(self, smarthome, update='False', ip='127.0.0.1', port=2323):
        asyncore.dispatcher.__init__(self, map=smarthome.socket_map)
        self.sh = smarthome
        self.updates_allowed = smarthome.string2bool(update)
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind((ip, int(port)))
            self.listen(5)
        except Exception:
            logger.error("Could not bind socket on %s:%s" % (ip, port))

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, (ip, port) = pair
            logger.debug('Incoming connection from %s:%s' % (ip, port))
            CLIHandler(self.sh, sock, ip, self.updates_allowed)

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False
        try:
            self.shutdown(socket.SHUT_RDWR)
            self.close()
        except:
            pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    myplugin = CLI('smarthome-dummy')
    myplugin.run()
