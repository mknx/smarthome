#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.
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
##########################################################################

import sys
import logging
import threading
import configobj

logger = logging.getLogger('')

class Plugins():
    _plugins = []
    _threads = []

    def __init__(self, smarthome, configfile):
        try:
            _conf = configobj.ConfigObj(configfile, file_error=True)
        except IOError, e:
            logger.critical(e)
            sys.exit(1)

        for plugin in _conf:
            args = ''
            logger.debug("Plugin: %s" % plugin)
            for arg in _conf[plugin]:
                if arg != 'class_name' and arg != 'class_path':
                    value = _conf[plugin][arg]
                    if isinstance(value, str):
                        value = "'%s'" % value
                    args = args + ", %s=%s" % ( arg, value )
            classname = _conf[plugin]['class_name']
            classpath = _conf[plugin]['class_path']
            try:
                plugin_thread = Plugin(smarthome, plugin, classname, classpath, args)
                self._threads.append(plugin_thread)
                self._plugins.append(plugin_thread.plugin)
            except Exception, e:
                logger.warning("Plugin {0} exception: {1}".format(plugin, e))

    def __iter__(self):
        for plugin in self._plugins:
            yield plugin

    def start(self):
        logger.info('Start Plugins')
        for plugin in self._threads:
            plugin.start()

    def stop(self):
        logger.info('Stop Plugins')
        for plugin in self._threads:
            plugin.stop()


class Plugin(threading.Thread):

    def __init__(self, smarthome, name, classname, classpath, args):
        threading.Thread.__init__(self, name=name)
        exec "import %s" % classpath
        exec "self.plugin = %s.%s(smarthome%s)" % (classpath, classname, args)
        setattr(smarthome, self.name, self.plugin)

    def run(self):
        self.plugin.run()

    def stop(self):
        self.plugin.stop()

