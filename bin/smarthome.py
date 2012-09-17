#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011-2012 KNX-User-Forum e.V.       http://knx-user-forum.de/
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
##########################################################################

import signal
import subprocess
import sys
import os
import threading
import time
import logging
import logging.handlers
import collections
import configobj
import asyncore
import types
import datetime
import locale
import traceback

from configobj import ConfigObj
from dateutil.tz import gettz

BASE = '/usr/local/smarthome'
PID_FILE = BASE + '/var/run/smarthome.pid'
sys.path.append(BASE)

import lib.node
import lib.scheduler
import lib.logic
import lib.plugin
import lib.tools
import lib.sun

VERSION = 0.64

TZ = gettz('UTC')

logger = logging.getLogger('SmartHome.py')


class LogHandler(logging.StreamHandler):
    def __init__(self, log):
        logging.StreamHandler.__init__(self)
        self._log = log

    def emit(self, record):
        timestamp = datetime.datetime.fromtimestamp(record.created, TZ)
        self._log.append([timestamp, record.threadName, record.levelname, record.message])


class SmartHome():
    _plugin_conf = BASE + '/etc/plugin.conf'
    _nodes_dir = BASE + '/nodes/'
    _logic_conf = BASE + '/etc/logic.conf'
    _cache_dir = BASE + '/var/cache/'
    _logfile = BASE + '/var/log/smarthome.log'
    _log_buffer = 50
    socket_map = {}
    connections = {}
    _plugins = []
    __nodes = []
    _sub_nodes = []
    __node_dict = {}

    _utctz = TZ

    def __init__(self, smarthome_conf='/usr/local/smarthome/etc/smarthome.conf'):
        self.version = VERSION
        global TZ
        threading.currentThread().name = 'SmartHome.py'
        self._connections = []
        self.alive = True
        if DAEMON:  # fork
            pid = os.fork()  # fork first child
            if pid == 0:
                os.setsid()
                pid = os.fork()  # fork second child
                if pid == 0:
                    os.chdir('/')
                    os.umask(022)
                else:
                    os._exit(0)  # exit parent
            else:
                os._exit(0)  # exit parent

            # close files
            for fd in range(0, 1024):
                try:
                    os.close(fd)
                except OSError:
                    pass

            # redirect I/O
            os.open(os.devnull, os.O_RDWR)  # input
            os.dup2(0, 1)  # output
            os.dup2(0, 2)  # error

        # signal handler
        signal.signal(signal.SIGHUP, self.restart_logics)
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        # init logging
        _logdate = "%Y-%m-%d %H:%M:%S"
        _logformat = "%(asctime)s %(threadName)-12s %(levelname)-8s %(message)s"
        if LOGLEVEL == 'debug':
            _logdate = None
            _logformat = "%(asctime)s %(threadName)-12s %(levelname)-8s %(message)s -- %(filename)s:%(funcName)s:%(lineno)d"
            _loglevel = logging.DEBUG
        elif LOGLEVEL == 'info':
            _loglevel = logging.INFO
        elif LOGLEVEL == 'warning':
            _loglevel = logging.WARNING
        elif LOGLEVEL == 'error':
            _loglevel = logging.ERROR
        else:
            _loglevel = logging.INFO

        logging.basicConfig(level=_loglevel, format=_logformat, datefmt=_logdate)

        formatter = logging.Formatter(_logformat, _logdate)
        log_file = logging.handlers.TimedRotatingFileHandler(self._logfile, when='midnight', backupCount=7)
        log_file.setLevel(_loglevel)
        log_file.setFormatter(formatter)
        logging.getLogger('').addHandler(log_file)

        self.log = collections.deque(maxlen=self._log_buffer)
        log_mem = LogHandler(self.log)
        log_mem.setLevel(logging.WARNING)
        log_mem.setFormatter(formatter)
        logging.getLogger('').addHandler(log_mem)
        sys.excepthook = self._excepthook

        # write pid file
        try:
            fd = open(PID_FILE, 'w+')
            fd.write("%s\n" % os.getpid())
            fd.close()
        except:
            logger.critical("Could not write to pid file: %s" % PID_FILE)
            logger.critical("Exit")
            os._exit(0)

        # Init Smarthome
        logger.info("Init SmartHome.py v%s" % VERSION)
        # Tools
        self.tools = lib.tools.Tools()
        try:
            config = ConfigObj(smarthome_conf)
            for attr in config:
                if not isinstance(config[attr], dict):  # ignore sub nodes
                    vars(self)['_' + attr] = config[attr]
        except Exception, e:
            pass

        # set tz to local tz
        if hasattr(self, '_tz'):
            os.environ['TZ'] = self._tz
            self.tz = self._tz
            self.tzinfo = gettz(self._tz)
            TZ = self.tzinfo
        else:
            self.tz = 'UTC'
            os.environ['TZ'] = self.tz
            self.tzinfo = self._utctz

        # init sun
        if hasattr(self, '_lon') and hasattr(self, '_lat'):
            if not hasattr(self, '_elev'):
                self.elev = None
            self.sun = lib.sun.Sun(self._lon, self._lat, self._elev)
        else:
            logger.info('No latitude/longitude specified => you could not use the sun object.')

        self.scheduler = lib.scheduler.Scheduler(self)
        self.trigger = self.scheduler.trigger
        self.scheduler.start()
        logger.info("Init plugins")
        self._plugins = lib.plugin.Plugins(self, configfile=self._plugin_conf)
        logger.info("Init nodes")
        for node_file in sorted(os.listdir(self._nodes_dir)):
            if node_file.endswith('.conf'):
                node_conf = ConfigObj(self._nodes_dir + node_file)
                for entry in node_conf:
                    if isinstance(node_conf[entry], dict):
                        path = entry
                        sub_node = lib.node.Node(self, self, path, node_conf[path])
                        vars(self)[path] = sub_node
                        self.add_node(path, sub_node)
                        self._sub_nodes.append(sub_node)
        for node in self.return_nodes():
            node.init_eval_trigger()
        for node in self.return_nodes():
            node.init_eval_run()
        if self._connections != []:
            self._connection_monitor()
            self.scheduler.add('sh.con', self._connection_monitor, cycle=120, offset=60)
        self._plugins.start()
        self.__logics = lib.logic.Logics(self, configfile=self._logic_conf)

        while self.alive:
            if self.socket_map != {}:
                asyncore.loop(timeout=1, count=1, map=self.socket_map)
            else:
                time.sleep(2)

    def __iter__(self):
        for node in self._sub_nodes:
            yield node

    def add_node(self, path, node):
        if path not in self.__nodes:
            self.__nodes.append(path)
        self.__node_dict[path] = node

    def return_node(self, string):
        if string in self.__nodes:
            return self.__node_dict[string]
        else:
            return None

    def return_nodes(self):
        for node in self.__nodes:
            yield self.__node_dict[node]

    def return_logics(self):
        for logic in self.__logics:
            yield logic

    def return_plugins(self):
        for plugin in self._plugins:
            yield plugin

    def stop(self, signum=None, frame=None):
        self.alive = False
        asyncore.close_all(self.socket_map)
        self.scheduler.stop()
        self._plugins.stop()
        time.sleep(0.6)
        if threading.active_count() > 1:
            for thread in threading.enumerate():
                logger.info("Thread: %s, still alive" % thread.name)
        try:
            os.remove(PID_FILE)
        except OSError:
            logger.critical("Could not remove pid file: %s" % PID_FILE)
        logger.info("SmartHome.py stopped")
        logging.shutdown()
        exit()

    def restart_logics(self, signum=None, frame=None):
        pass
        #self.logics.restart()

    def now(self):
        # tz aware 'localtime'
        return datetime.datetime.now(self.tzinfo)

    def utcnow(self):
        # tz aware utc time
        return datetime.datetime.now(self._utctz)

    def string2bool(self, string):
        if string.lower() in ['0', 'false', 'n', 'no', 'off']:
            return False
        elif string.lower() in ['1', 'true', 'y', 'yes', 'on']:
            return True
        else:
            return None

    def _excepthook(self, typ, value, tb):
        mytb = "".join(traceback.format_tb(tb))
        logger.critical("Unhandeld exception: {1}\n{0}\n{2}".format(typ, value, mytb))

    def object_refcount(self):
        objects = {}
        for module in sys.modules.values():
            for sym in dir(module):
                obj = getattr(module, sym)
                if type(obj) is types.ClassType:
                    objects[obj] = sys.getrefcount(obj)
        objects = map(lambda x: (x[1], x[0]), objects.items())
        objects.sort(reverse=True)
        return objects

    def monitor_connection(self, obj):
        if hasattr(obj, 'is_connected') and hasattr(obj, 'connect'):
            self._connections.append(obj)

    def _connection_monitor(self):
        for connection in self._connections:
            if not connection.is_connected:
                connection.connect()

#############################################################################


def read_pid():
    try:
        fd = open(PID_FILE, 'r')
        pid = int(fd.read().strip())
        fd.close()
    except IOError:
        pid = False
    return pid


def stop_sh():
    pid = read_pid()
    if pid:
        for i in range(4):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                os._exit(0)
            time.sleep(0.5)

        # FIXME shutdown doesn't work all the time :-(
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            os._exit(0)
        try:
            os.remove(PID_FILE)
        except OSError:
            print("Could not remove pid file: %s" % PID_FILE)
        print("Hard kill SmartHome.py")


def logic_update():
    pid = read_pid()
    if pid:
        os.kill(pid, signal.SIGHUP)


def usage():
    #print('Usage: smarthome.py [--start] [--no-daemon] [-n] [--stop] [--restart] [-r]')
    print('Usage: smarthome.py [--start] [--no-daemon|-n] [--stop] [--debug|-d]')


if __name__ == '__main__':
    LOGLEVEL = 'info'
    DAEMON = True

    locale.setlocale(locale.LC_ALL, '')

    if '--stop' in sys.argv[1:]:
        stop_sh()
        exit(0)

    for arg in sys.argv[1:]:
        if arg == '--start':
            pass
        #elif arg == '--logic-update' or arg == '-u':
        #    logic_update()
        #    exit(0)
        elif arg == '--no-daemon' or arg == '-n':
            DAEMON = False
            LOGLEVEL = 'debug'
        elif arg == '--debug' or arg == '-d':
            LOGLEVEL = 'debug'
        elif arg == '--restart' or arg == '-r':
            stop_sh()
        elif arg == '--help' or arg == '-h':
            usage()
            exit(0)
        else:
            print("Unkown argument: %s" % arg)
            usage()
            exit(0)

    pid = read_pid()
    try:
        os.getpgid(pid)  # check if the process is running
    except OSError:
        try:
            os.remove(PID_FILE)
        except OSError:
            print("Could not remove pid file: %s" % PID_FILE)

    pid = read_pid()
    if pid:
        print("SmartHome.py already running with pid %s" % pid)
        print("Run 'smarthome.py --stop' to stop it.")
        exit()
    sh = SmartHome()
