#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011-2013 Marcus Popp                          marcus@popp.mx
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

#####################################################################
# Import Python Core Modules
#####################################################################
import argparse
import asyncore
import datetime
import gc
import locale
import logging
import logging.handlers
import os
import re
import signal
import subprocess
import sys
import threading
import time
import traceback
import types

#####################################################################
# Import 3rd Party Modules
#####################################################################
from configobj import ConfigObj
from dateutil.tz import gettz

#####################################################################
# Base
#####################################################################
logger = logging.getLogger('')
BASE = '/'.join(os.path.realpath(__file__).split('/')[:-2])
sys.path.append(BASE)

#####################################################################
# Import SmartHome.py Modules
#####################################################################
import lib.item
import lib.scheduler
import lib.logic
import lib.plugin
import lib.tools
import lib.orb
import lib.log
import lib.scene

#####################################################################
# Globals
#####################################################################
PID_FILE = BASE + '/var/run/smarthome.pid'
MODE = 'default'
LOGLEVEL = logging.INFO
VERSION = '0.9'
TZ = gettz('UTC')
try:
    os.chdir(BASE)
    VERSION = subprocess.check_output(['git', 'describe', '--always', '--dirty=+'], stderr=subprocess.STDOUT).strip('\n')
except Exception, e:
    pass


#####################################################################
# Classes
#####################################################################

class LogHandler(logging.StreamHandler):
    def __init__(self, log):
        logging.StreamHandler.__init__(self)
        self._log = log

    def emit(self, record):
        timestamp = datetime.datetime.fromtimestamp(record.created, TZ)
        self._log.add([timestamp, record.threadName, record.levelname, record.message])


class SmartHome():
    base_dir = BASE
    _plugin_conf = BASE + '/etc/plugin.conf'
    _items_dir = BASE + '/items/'
    _logic_conf = BASE + '/etc/logic.conf'
    _cache_dir = BASE + '/var/cache/'
    _logfile = BASE + '/var/log/smarthome.log'
    _log_buffer = 50
    socket_map = {}
    __logs = {}
    __event_listeners = {}
    __all_listeners = []
    _plugins = []
    __items = []
    _sub_items = []
    __item_dict = {}
    _utctz = TZ

    def __init__(self, smarthome_conf=BASE + '/etc/smarthome.conf'):
        global TZ
        threading.currentThread().name = 'Main'
        self.alive = True
        self.version = VERSION
        self._connections = []

        #############################################################
        # logfile write test
        #############################################################
        try:
            with open(self._logfile, 'a') as f:
                f.write("Init SmartHome.py {0}\n".format(VERSION))
        except IOError, e:
            print("Error creating logfile {}: {}".format(self._logfile, e))

        #############################################################
        # Fork
        #############################################################
        if MODE == 'default':
            pid = os.fork()  # fork first child
            if pid == 0:
                os.setsid()
                pid = os.fork()  # fork second child
                if pid == 0:
                    os.chdir('/')
                    os.umask(022)
                    print("Starting SmartHome.py in the background with pid: {}".format(os.getpid()))
                else:
                    time.sleep(0.1)
                    os._exit(0)  # exit parent
            else:
                time.sleep(0.1)
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

        #############################################################
        # Signal Handling
        #############################################################
        signal.signal(signal.SIGHUP, self.reload_logics)
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        #############################################################
        # Logging
        #############################################################
        _logdate = "%Y-%m-%d %H:%M:%S"
        _logformat = "%(asctime)s %(threadName)-12s %(levelname)-8s %(message)s"
        if LOGLEVEL == logging.DEBUG:
            _logdate = None
            _logformat = "%(asctime)s %(threadName)-12s %(levelname)-8s %(message)s -- %(filename)s:%(funcName)s:%(lineno)d"
        logging.basicConfig(level=LOGLEVEL, format=_logformat, datefmt=_logdate)
        if MODE == 'interactive':  # remove default stream handler
            logger.removeHandler(logger.handlers[0])
        # adding logfile
        try:
            formatter = logging.Formatter(_logformat, _logdate)
            log_file = logging.handlers.TimedRotatingFileHandler(self._logfile, when='midnight', backupCount=7)
            log_file.setLevel(LOGLEVEL)
            log_file.setFormatter(formatter)
            logging.getLogger('').addHandler(log_file)
        except IOError, e:
            print("Error creating logfile {}: {}".format(self._logfile, e))
        # adding SH.py log
        self.log = lib.log.Log(self, 'SmartHome.py', '<li><p style="font-weight:bold;">{1}</p><p>{3}</p><p class="ui-li-aside">{0:%a %H:%M:%S}<br />{2}</p></li>', maxlen=self._log_buffer)
        log_mem = LogHandler(self.log)
        log_mem.setLevel(logging.WARNING)
        log_mem.setFormatter(formatter)
        logging.getLogger('').addHandler(log_mem)

        #############################################################
        # Catching Exceptions
        #############################################################
        sys.excepthook = self._excepthook

        #############################################################
        # Write PID File
        #############################################################
        try:
            with open(PID_FILE, 'w+') as fd:
                fd.write("{}\n".format(os.getpid()))
        except:
            logger.critical("Could not write to pid file: {}".format(PID_FILE))
            logger.critical("Exit")
            os._exit(0)

        #############################################################
        # Reading smarthome.conf
        #############################################################
        try:
            config = ConfigObj(smarthome_conf)
            for attr in config:
                if not isinstance(config[attr], dict):  # ignore sub items
                    vars(self)['_' + attr] = config[attr]
            del(config)  # clean up
        except Exception, e:
            logger.warning("Problem reading smarthome.conf: {0}".format(e))

        #############################################################
        # Setting (local) tz
        #############################################################
        if hasattr(self, '_tz'):
            os.environ['TZ'] = self._tz
            self.tz = self._tz
            self._tzinfo = gettz(self._tz)
            TZ = self._tzinfo
        else:
            self.tz = 'UTC'
            os.environ['TZ'] = self.tz
            self._tzinfo = self._utc

        logger.info("Start SmartHome.py {0}".format(VERSION))
        logger.debug("Python {0}".format(sys.version.split()[0]))

        #############################################################
        # Link Tools
        #############################################################
        self.tools = lib.tools.Tools()

        #############################################################
        # Link Sun and Moon
        #############################################################
        if hasattr(self, '_lon') and hasattr(self, '_lat'):
            if not hasattr(self, '_elev'):
                self._elev = None
            self.sun = lib.orb.Orb('sun', self._lon, self._lat, self._elev)
            self.moon = lib.orb.Orb('moon', self._lon, self._lat, self._elev)
        else:
            logger.warning('No latitude/longitude specified => you could not use the sun and moon object.')

    #################################################################
    # Process Methods
    #################################################################

    def start(self):
        threading.currentThread().name = 'Main'

        #############################################################
        # Start Scheduler
        #############################################################
        self.scheduler = lib.scheduler.Scheduler(self)
        self.trigger = self.scheduler.trigger
        self.scheduler.start()

        #############################################################
        # Init Plugins
        #############################################################
        logger.info("Init Plugins")
        self._plugins = lib.plugin.Plugins(self, configfile=self._plugin_conf)

        #############################################################
        # Init Items
        #############################################################
        logger.info("Init Items")
        for item_file in sorted(os.listdir(self._items_dir)):
            if item_file.endswith('.conf'):
                try:
                    item_conf = ConfigObj(self._items_dir + item_file)
                except Exception, e:
                    logger.warning("Problem reading {0}: {1}".format(item_file, e))
                    continue
                for entry in item_conf:
                    if isinstance(item_conf[entry], dict):
                        path = entry
                        sub_item = self.return_item(path)
                        if sub_item is None:  # new item
                            sub_item = lib.item.Item(self, self, path, item_conf[path])
                            vars(self)[path] = sub_item
                            self.add_item(path, sub_item)
                            self._sub_items.append(sub_item)
                        else:  # existing item
                            sub_item.parse(self, self, path, item_conf[path])
                del(item_conf)  # clean up
        for item in self.return_items():
            item.init_prerun()
        for item in self.return_items():
            item.init_run()

        #############################################################
        # Add connection monitor
        #############################################################
        if self._connections != []:
            self.scheduler.add('sh.con', self._connection_monitor, cycle=10, offset=0)

        #############################################################
        # Start Plugins
        #############################################################
        self._plugins.start()

        #############################################################
        # Init Logics
        #############################################################
        self._logics = lib.logic.Logics(self, configfile=self._logic_conf)

        #############################################################
        # Init Scenes
        #############################################################
        lib.scene.Scenes(self)

        #############################################################
        # Adding Garbage Collection
        #############################################################
        self.scheduler.add('sh.gc', self._garbage_collection, prio=8, cron="init | 4 2 * *", offset=0)

        #############################################################
        # Main Loop
        #############################################################
        while self.alive:
            if self.socket_map != {}:
                asyncore.loop(timeout=1, use_poll=True, count=1, map=self.socket_map)
            else:
                time.sleep(2)

    def stop(self, signum=None, frame=None):
        self.alive = False
        logger.info("Number of Threads: {0}".format(threading.activeCount()))
        try:
            asyncore.close_all(self.socket_map)
        except:
            pass
        try:
            self.scheduler.stop()
        except:
            pass
        try:
            self._plugins.stop()
        except:
            pass
        time.sleep(0.5)
        if threading.active_count() > 1:
            for thread in threading.enumerate():
                logger.info("Thread: {}, still alive".format(thread.name))
        try:
            os.remove(PID_FILE)
        except OSError, e:
            logger.critical("Could not remove pid file: {0} - {1}".format(PID_FILE, e))
        logger.info("SmartHome.py stopped")
        logging.shutdown()
        exit()

    #################################################################
    # Item Methods
    #################################################################
    def __iter__(self):
        for item in self._sub_items:
            yield item

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

    def match_items(self, regex):
        regex = regex.replace('.', '\.').replace('*', '.*') + '$'
        regex = re.compile(regex)
        return [self.__item_dict[item] for item in self.__items if regex.match(item)]

    def find_items(self, conf):
        for item in self.__items:
            if conf in self.__item_dict[item].conf:
                yield self.__item_dict[item]

    def find_children(self, parent, conf):
        children = []
        for item in parent:
            if conf in item.conf:
                children.append(item)
            children += self.find_children(item, conf)
        return children

    #################################################################
    # Plugin Methods
    #################################################################
    def return_plugins(self):
        for plugin in self._plugins:
            yield plugin

    #################################################################
    # Logic Methods
    #################################################################
    def reload_logics(self, signum=None, frame=None):
        for logic in self._logics:
            self._logics[logic].generate_bytecode()

    def return_logic(self, name):
        return self._logics[name]

    def return_logics(self):
        for logic in self._logics:
            yield logic

    #################################################################
    # Connection Monitor
    #################################################################
    def monitor_connection(self, obj):
        if hasattr(obj, 'is_connected') and hasattr(obj, 'connect'):
            self._connections.append(obj)

    def _connection_monitor(self):
        for connection in self._connections:
            if not connection.is_connected:
                connection.connect()

    #################################################################
    # Log Methods
    #################################################################
    def add_log(self, name, log):
        self.__logs[name] = log

    def return_logs(self):
        return self.__logs

    #################################################################
    # Event Methods
    #################################################################
    def add_event_listener(self, events, method):
        for event in events:
            if event in self.__event_listeners:
                self.__event_listeners[event].append(method)
            else:
                self.__event_listeners[event] = [method]
        self.__all_listeners.append(method)

    def return_event_listeners(self, event='all'):
        if event == 'all':
            return self.__all_listeners
        elif event in self.__event_listeners:
            return self.__event_listeners[event]
        else:
            return []

    #################################################################
    # Time Methods
    #################################################################
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

    #################################################################
    # Helper Methods
    #################################################################
    def _excepthook(self, typ, value, tb):
        mytb = "".join(traceback.format_tb(tb))
        logger.critical("Unhandled exception: {1}\n{0}\n{2}".format(typ, value, mytb))

    def _garbage_collection(self):
        c = gc.collect()
        logger.debug("Garbage collector: collected {0} objects.".format(c))

    def string2bool(self, string):
        if isinstance(string, bool):
            return string
        if string.lower() in ['0', 'false', 'n', 'no', 'off']:
            return False
        if string.lower() in ['1', 'true', 'y', 'yes', 'on']:
            return True
        else:
            return None

    def object_refcount(self):
        objects = {}
        for module in sys.modules.values():
            for sym in dir(module):
                obj = getattr(module, sym)
                if isinstance(obj, types.ClassType):
                    objects[obj] = sys.getrefcount(obj)
        objects = map(lambda x: (x[1], x[0]), objects.items())
        objects.sort(reverse=True)
        return objects


#####################################################################
# Private Methods
#####################################################################

def _read_pid():
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


def _stop():
    pid = _read_pid()
    if pid:
        for i in range(4):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                os._exit(0)
            time.sleep(0.7)
        try:
            os.kill(pid, signal.SIGKILL)
            print("Hard kill SmartHome.py")
        except OSError:
            os._exit(0)


def reload_logics():
    pid = _read_pid()
    if pid:
        os.kill(pid, signal.SIGHUP)


#####################################################################
# Main
#####################################################################

if __name__ == '__main__':
    if locale.getdefaultlocale() == (None, None):
        locale.setlocale(locale.LC_ALL, 'C')
    else:
        locale.setlocale(locale.LC_ALL, '')

    # argument handling
    argparser = argparse.ArgumentParser()
    arggroup = argparser.add_mutually_exclusive_group()
    arggroup.add_argument('-v', '--verbose', help='verbose logging to the logfile', action='store_true')
    arggroup.add_argument('-d', '--debug', help='stay in the foreground with verbose output', action='store_true')
    arggroup.add_argument('-i', '--interactive', help='open an interactive shell with tab completion and with verbose logging to the logfile', action='store_true')
    arggroup.add_argument('-l', '--logics', help='reload all logics', action='store_true')
    arggroup.add_argument('-s', '--stop', help='stop SmartHome.py', action='store_true')
    arggroup.add_argument('-q', '--quiet', help='reduce logging to the logfile', action='store_true')
    arggroup.add_argument('--start', help='start SmartHome.py and detach from console (default)', default=True, action='store_true')
    args = argparser.parse_args()

    if args.interactive:
        LOGLEVEL = logging.DEBUG
        MODE = 'interactive'
        import code
        import rlcompleter  # noqa
        import readline
        import atexit
        # history file
        histfile = os.path.join(os.environ['HOME'], '.history.python')
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        atexit.register(readline.write_history_file, histfile)
        readline.parse_and_bind("tab: complete")
        sh = SmartHome()
        _sh_thread = threading.Thread(target=sh.start)
        _sh_thread.start()
        shell = code.InteractiveConsole(locals())
        shell.interact()
        exit(0)
    elif args.logics:
        reload_logics()
        exit(0)
    elif args.stop:
        _stop()
        exit(0)
    elif args.debug:
        LOGLEVEL = logging.DEBUG
        MODE = 'debug'
    elif args.quiet:
        LOGLEVEL = logging.WARNING
    elif args.verbose:
        LOGLEVEL = logging.DEBUG

    # check for pid file
    pid = _read_pid()
    if pid:
        try:
            os.getpgid(pid)  # check if the process is running
        except OSError:
            try:
                os.remove(PID_FILE)
            except OSError, e:
                print("Could not remove pid file: {0} - {1}".format(PID_FILE, e))
    pid = _read_pid()
    if pid:
        print("SmartHome.py already running with pid {}".format(pid))
        print("Run 'smarthome.py -s' to stop it.")
        exit()

    # Starting SmartHome.py
    sh = SmartHome()
    sh.start()
