#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
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
import datetime
import threading
import xml.etree.cElementTree

logger = logging.getLogger('')

class yrno():
    _server = 'http://www.yr.no/place/'
    _content = None
    _xmlData = None

    def updateValues(self, item):
        logger.debug("data: {0}".format(self.weatherData))

        if 'yrno_attr' in item.conf:
            yrno_attr = item.conf['yrno_attr']
            logger.debug("get {0}".format(yrno_attr))
            return self.update_item(item, yrno_attr)


    def importXMLData(self):
        dataURL = self._server + self._weatherStation + '/forecast_hour_by_hour.xml'

        logger.debug("getting actual data from {0}".format(dataURL))
        self._content = self._sh.tools.fetch_url(dataURL)

        if self._content:
            self._xmlData = xml.etree.cElementTree.fromstring(self._content)

    def getAllData(self):
        self.importXMLData()
        self.readXmlNode('all')


    def getActualData(self):
        self.importXMLData()
        self.readXmlNode('one')


    def readXmlNode(self, count='one'):
        retval = {}

        days = self._xmlData.find('./forecast/tabular/time')

        for day in days:

            date, time = day.attrib['from'].split('T')
            year, month, day = date.split('-')
            hour, minute, second = time.split(':')
            d = datetime.datetime(int(year), int(month), int(day), int(hour))

            retval[d] = {   'date' : d,
                            'tempUnit': day.find('temperature').attrib['unit'],
                            'tempValue': day.find('temperature').attrib['value'],
                            'rainfallValue': day.find('precipitation').attrib['value'],
                            'windDirDeg': day.find('windDirection').attrib['deg'],
                            'windDirCode': day.find('windDirection').attrib['code'],
                            'windDirName': day.find('windDirection').attrib['name'],
                            'windSpeedValue': day.find('windSpeed').attrib['mps'],
                            'windSpeedName': day.find('windSpeed').attrib['name'],
                            'pressureUnit': day.find('pressure').attrib['unit'],
                            'pressureValue': day.find('pressure').attrib['value'],
                            'symbolNumber': day.find('symbol').attrib['number'],
                            'symbolName': day.find('symbol').attrib['name'],
                            'symbolVar': day.find('symbol').attrib['var'] }

            rainfall = day.find('precipitation');

            if 'minvalue' in rainfall.attrib:
                retval[d]['rainfallMin'] = day.find('precipitation').attrib['minvalue']
                retval[d]['rainfallMax'] = day.find('precipitation').attrib['maxvalue']

            if count == 'one':
                break;

        if count == 'one':
            self.weatherData = retval[d]
        else:
            self.weatherData = retval
    
    def __init__(self, smarthome, weatherStation):
        self._sh = smarthome
        self._weatherStation = weatherStation
        self.getActualData()
    
    def run(self):
        self.alive = True
    # if you want to create child threads, do not make them daemon = True!
    # They will not shutdown properly. (It's a python bug)
    
    def stop(self):
        self.alive = False
    
    def parse_item(self, item):
        if 'yrno_attr' in item.conf:
            yrno_attr = item.conf['yrno_attr']
            logger.debug("get {0}".format(yrno_attr))
            return self.update_item(item, yrno_attr)
        else:
            return None
    
    def parse_logic(self, logic):
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    def update_item(self, item, yrno_attr, caller=None, source=None, dest=None):
        if caller != 'plugin':
            if yrno_attr == 'tempValue':
                item(float(self.weatherData[yrno_attr]))
            if yrno_attr == 'rainfallValue':
                item(float(self.weatherData[yrno_attr]))
            if yrno_attr == 'windSpeedValue':
                item(float(self.weatherData[yrno_attr]))
            if yrno_attr == 'pressureValue':
                item(float(self.weatherData[yrno_attr]))
            if yrno_attr == 'windDirDeg':
                item(float(self.weatherData[yrno_attr]))
            if yrno_attr == 'rainfallMin' and 'rainfallMin' in self.weatherData:
                item(float(self.weatherData[yrno_attr]))
            if yrno_attr == 'rainfallMax' and 'rainfallMax' in self.weatherData:
                item(float(self.weatherData[yrno_attr]))
            if yrno_attr == 'windSpeedName':
                item(self.weatherData[yrno_attr])
            if yrno_attr == 'windDirName':
                item(self.weatherData[yrno_attr])
            if yrno_attr == 'windDirCode':
                item(self.weatherData[yrno_attr])
            if yrno_attr == 'tempUnit':
                item(self.weatherData[yrno_attr])
            if yrno_attr == 'symbolNumber':
                item(int(self.weatherData[yrno_attr]))
            if yrno_attr == 'symbolVar':
                item(self.weatherData[yrno_attr])
            if yrno_attr == 'pressureUnit':
                item(self.weatherData[yrno_attr])
            if yrno_attr == 'symbolName':
                item(self.weatherData[yrno_attr])

        logger.info("update item: {0} {1} {2} {3}".format(caller, item.id(), yrno_attr, item._value))

    if __name__ == '__main__':
        logging.basicConfig(level=logging.DEBUG)
        myplugin = Plugin('yrno')
        myplugin.run()

