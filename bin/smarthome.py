#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011-2013 KNX-User-Forum e.V.       http://knx-user-forum.de/
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
import sys
import os
import subprocess
import threading
import time
import logging
import logging.handlers
import asyncore
import types
import datetime
import locale
import traceback
import gc

from configobj import ConfigObj
from dateutil.tz import gettz

# os.path.realpath(__file__) # use for BASE evaluation
BASE = '/usr/local/smarthome'
PID_FILE = BASE + '/var/run/smarthome.pid'
sys.path.append(BASE)

import lib.item
import lib.scheduler
import lib.logic
import lib.plugin
import lib.tools
import lib.orb
import lib.log
import lib.scene

VERSION = '0.9-Dev'
try:
    os.chdir(BASE)
    VERSION = subprocess.check_output(['git', 'describe', '--always', '--dirty=+'], stderr=subprocess.STDOUT).strip('\n')
except Exception, e:
    pass

TZ = gettz('UTC')

logger = logging.getLogger('SmartHome.py')


class LogHandler(logging.StreamHandler):
    def __init__(self, log):
        logging.StreamHandler.__init__(self)
        self._log = log

    def emit(self, record):
        timestamp = datetime.datetime.fromtimestamp(record.created, TZ)
        self._log.add([timestamp, record.threadName, record.levelname, record.message])


class SmartHome():
    _base_dir = BASE
    _plugin_conf = BASE + '/etc/plugin.conf'
    _items_dir = BASE + '/items/'
    _logic_conf = BASE + '/etc/logic.conf'
    _cache_dir = BASE + '/var/cache/'
    _logfile = BASE + '/var/log/smarthome.log'
    _log_buffer = 50
    socket_map = {}
    connections = {}
    __logs = {}
    __listeners = []
    _plugins = []
    __items = []
    _sub_items = []
    __item_dict = {}
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

        self.log = lib.log.Log(self, 'SmartHome.py', '<li><p style="font-weight:bold;">{1}</p><p>{3}</p><p class="ui-li-aside">{0:%a %H:%M:%S}<br />{2}</p></li>', maxlen=self._log_buffer)
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
        try:
            config = ConfigObj(smarthome_conf)
            for attr in config:
                if not isinstance(config[attr], dict):  # ignore sub items
                    vars(self)['_' + attr] = config[attr]
        except Exception, e:
            logger.warning("Problem reading smarthome.conf: {0}".format(e))

        # set tz to local tz
        if hasattr(self, '_tz'):
            os.environ['TZ'] = self._tz
            self.tz = self._tz
            self._tzinfo = gettz(self._tz)
            TZ = self._tzinfo
        else:
            self.tz = 'UTC'
            os.environ['TZ'] = self.tz
            self._tzinfo = self._utctz

        logger.info("Init SmartHome.py v%s" % VERSION)
        # Tools
        self.tools = lib.tools.Tools()
        # init sun
        if hasattr(self, '_lon') and hasattr(self, '_lat'):
            if not hasattr(self, '_elev'):
                self._elev = None
            self.sun = lib.orb.Orb('sun', self._lon, self._lat, self._elev)
            self.moon = lib.orb.Orb('moon', self._lon, self._lat, self._elev)
        else:
            logger.info('No latitude/longitude specified => you could not use the sun and moon object.')

        self.scheduler = lib.scheduler.Scheduler(self)
        self.trigger = self.scheduler.trigger
        self.scheduler.start()
        logger.info("Init plugins")
        self._plugins = lib.plugin.Plugins(self, configfile=self._plugin_conf)
        logger.info("Init items")
        for item_file in sorted(os.listdir(self._items_dir)):
            if item_file.endswith('.conf'):
                try: 
                    item_conf = ConfigObj(self._items_dir + item_file)
                except Exception, e:
                    logger.warning("Problem reading {0}: {1}".format(item_file,e))
                    continue
                for entry in item_conf:
                    if isinstance(item_conf[entry], dict):
                        path = entry
                        sub_item = lib.item.Item(self, self, path, item_conf[path])
                        vars(self)[path] = sub_item
                        self.add_item(path, sub_item)
                        self._sub_items.append(sub_item)
        for item in self.return_items():
            item.init_prerun()
        for item in self.return_items():
            item.init_run()
        if self._connections != []:
            self.scheduler.add('sh.con', self._connection_monitor, cycle=10, offset=0)
        self._plugins.start()
        self._logics = lib.logic.Logics(self, configfile=self._logic_conf)
        lib.scene.Scenes(self)

        # garbage collection
        self.scheduler.add('sh.gc', self._garbage_collection, prio=8, cron=['init', '4 2 * *'], offset=0)

        while self.alive:
            if self.socket_map != {}:
                asyncore.loop(timeout=1, count=1, map=self.socket_map)
            else:
                time.sleep(2)

    def __iter__(self):
        for item in self._sub_items:
            yield item

    def add_listener(self, method):
        self.__listeners.append(method)

    def return_listeners(self):
        return self.__listeners

    def add_log(self, name, log):
        self.__logs[name] = log

    def return_logs(self):
        return self.__logs

    def add_item(self, path, item):
        if path not in self.__items:
            self.__items.append(path)
        self.__item_dict[path] = item

    def return_item(self, string):
        if string in self.__items:
            return self.__item_dict[string]

    def return_items(self):
        for item in self.__items:
            yield self.__item_dict[item]

    def find_items(self, conf):
        for item in self.__items:
            if conf in self.__item_dict[item].conf:
                yield self.__item_dict[item]

    def find_children(self, parent, conf):
        for item in parent:
            if conf in item.conf:
                yield item
            for child in self.find_children(item, conf):
                yield child

    def return_logic(self, name):
        return self._logics[name]

    def return_logics(self):
        for logic in self._logics:
            yield logic

    def return_plugins(self):
        for plugin in self._plugins:
            yield plugin

    def stop(self, signum=None, frame=None):
        self.alive = False
        asyncore.close_all(self.socket_map)
        self.scheduler.stop()
        self._plugins.stop()
        time.sleep(0.5)
        if threading.active_count() > 1:
            for thread in threading.enumerate():
                logger.info("Thread: %s, still alive" % thread.name)
        try:
            os.remove(PID_FILE)
        except OSError, e:
            logger.critical("Could not remove pid file: {0} - {1}".format(PID_FILE, e))
        logger.info("SmartHome.py stopped")
        logging.shutdown()
        exit()

    def _garbage_collection(self):
        c = gc.collect()
        logger.debug("Garbage collector: collected {0} objects.".format(c))

    def restart_logics(self, signum=None, frame=None):
        pass
        #self.logics.restart()

    def now(self):
        # tz aware 'localtime'
        return datetime.datetime.now(self._tzinfo)

    def tzinfo(self):
        return self._tzinfo

    def utcnow(self):
        # tz aware utc time
        return datetime.datetime.now(self._utctz)

    def utcinfo(self):
        return self._utctz

    def string2bool(self, string):
        if string.lower() in ['0', 'false', 'n', 'no', 'off']:
            return False
        elif string.lower() in ['1', 'true', 'y', 'yes', 'on']:
            return True
        else:
            return None

    def _excepthook(self, typ, value, tb):
        mytb = "".join(traceback.format_tb(tb))
        logger.critical("Unhandled exception: {1}\n{0}\n{2}".format(typ, value, mytb))

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
        with open(PID_FILE, 'r') as fd:
            pid = fd.read().strip()
            if pid == '':
                pid = False
            else:
                pid = int(pid)
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
            time.sleep(0.7)

        # FIXME shutdown doesn't work all the time :-(
        try:
            os.kill(pid, signal.SIGKILL)
            print("Hard kill SmartHome.py")
        except OSError:
            os._exit(0)


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

    locale.setlocale(locale.LC_ALL, 'C')

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

    pid = read_pid() # check if there is a PID_FILE
    if pid:
        try:
            os.getpgid(pid)  # check if the process is running
        except OSError:
            try:
                os.remove(PID_FILE)
            except OSError, e:
                print("Could not remove pid file: {0} - {1}".format(PID_FILE, e))

    pid = read_pid()
    if pid:
        print("SmartHome.py already running with pid {0}".format(pid))
        print("Run 'smarthome.py --stop' to stop it.")
        exit()
    sh = SmartHome()
