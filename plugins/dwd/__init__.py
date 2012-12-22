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
#  along with SmartHome.py.  If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import csv
import ftplib
import socket
import re
import datetime
import dateutil.parser
import dateutil.tz
import dateutil.relativedelta
import StringIO
import xml.etree.ElementTree
import threading

logger = logging.getLogger('')


class DWD():
    _dwd_host = 'ftp-outgoing2.dwd.de'
    _warning_cat = {}
    _warnings_csv = '/usr/local/smarthome/plugins/dwd/warnings.csv'

    def __init__(self, smarthome, dwd_user, dwd_password=True):
        self._sh = smarthome
        self._dwd_user = dwd_user
        self._dwd_password = dwd_password
        self.lock = threading.Lock()
        self.tz = dateutil.tz.gettz('Europe/Berlin')
        try:
            warnings = csv.reader(open(self._warnings_csv, "rb"), delimiter=';')
        except IOError, e:
            logger.error('Could not open warning catalog %s: %s' % (self._warnings_csv, e))
        for row in warnings:
            self._warning_cat[int(row[0])] = {'summary': unicode(row[1], 'utf-8'), 'kind': unicode(row[2], 'utf-8')}

    def _connect(self):
        # open ftp connection to dwd
        if not hasattr(self, '_ftp'):
            try:
                self._ftp = ftplib.FTP(self._dwd_host, self._dwd_user, self._dwd_password, timeout=3)
            except (socket.error, socket.gaierror), e:
                logger.error('Could not connect to %s: %s' % (self._dwd_host, e))
                self.ftp_quit()
            except ftplib.error_perm, e:
                logger.error('Could not login: %s' % e)
                self.ftp_quit()

    def run(self):
        self.alive = True

    def stop(self):
        self.ftp_quit()
        self.alive = False

    def ftp_quit(self):
        try:
            self._ftp.close()
        except Exception, e:
            pass
        if hasattr(self, '_ftp'):
            del self._ftp

    def parse_item(self, item):
        return None

    def parse_logic(self, logic):
        return None

    def _buffer_file(self, data):
        self._buffer += data

    def _retr_file(self, filename):
        self.lock.acquire()
        self._connect()
        self._buffer = ''
        try:
            self._ftp.retrbinary("RETR %s" % filename, self._buffer_file)
        except Exception, e:
            pass
        self.lock.release()
        return self._buffer

    def _retr_list(self, dirname):
        self.lock.acquire()
        self._connect()
        try:
            filelist = self._ftp.nlst(dirname)
        except Exception, e:
            filelist = []
        self.lock.release()
        return filelist

    def warnings(self, region, location):
        directory = 'gds/specials/warnings'
        warnings = []
        filepath = "{0}/{1}/W*_{2}_*".format(directory, region, location)
        files = self._retr_list(filepath)
        for filename in files:
            fb = self._retr_file(filename)
            fb = fb.decode('iso-8859-1')
            dates = re.findall(r"\d\d\.\d\d\.\d\d\d\d \d\d:\d\d", fb)
            now = datetime.datetime.now(self.tz)
            if len(dates) > 1:  # Entwarnungen haben nur ein Datum
                start = dateutil.parser.parse(dates[0])
                start = start.replace(tzinfo=self.tz)
                end = dateutil.parser.parse(dates[1])
                end = end.replace(tzinfo=self.tz)
                notice = dateutil.parser.parse(dates[2])
                notice = notice.replace(tzinfo=self.tz)
                if end > now:
                    area_splitter = re.compile(r'^\r\r\n', re.M)
                    area = area_splitter.split(fb)
                    code = int(re.findall(r"\d\d", area[0])[0])
                    desc = area[5].replace('\r\r\n', '').strip()
                    kind = self._warning_cat[code]['kind']
                    warnings.append({'start': start, 'end': end, 'kind': kind, 'notice': notice, 'desc': desc})
        return warnings

    def current(self, location):
        directory = 'gds/specials/observations/tables/germany'
        last = sorted(self._retr_list(directory)).pop()
        fb = self._retr_file(last)
        fb = fb.decode('iso-8859-1')
        fb = fb.splitlines()
        header = fb[4]
        legend = fb[8].split()
        date = re.findall(r"\d\d\.\d\d\.\d\d\d\d", header)[0].split('.')
        date = "%s-%s-%s" % (date[2], date[1], date[0])
        for line in fb:
            if line.count(location):
                space = re.compile(r'  +')
                line = space.split(line)
                return dict(zip(legend, line))
        return {}

    def forecast(self, region, location):
        path = 'gds/specials/forecasts/tables/germany/Daten_'
        frames = ['frueh', 'mittag', 'spaet', 'nacht', 'morgen_frueh', 'morgen_spaet', 'uebermorgen_frueh', 'uebermorgen_spaet', 'Tag4_frueh', 'Tag4_spaet']
        forecast = {}
        for frame in frames:
            filepath = "{0}{1}_{2}".format(path, region, frame)
            fb = self._retr_file(filepath)
            fb = fb.decode('iso-8859-1')
            minute = 0
            if frame.count('frueh'):
                hour = 6
            elif frame == 'mittag':
                hour = 12
            elif frame == 'nacht':
                hour = 23
                minute = 59
            else:
                hour = 18
            for line in fb.splitlines():
                if line.count('Termin ist nicht mehr'):  # already past
                    date = self._sh.now().replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=self.tz)
                    forecast[date] = ['', '', '']
                    continue
                elif line.startswith('Vorhersage'):
                    header = line
                elif line.count(location):
                    header = re.sub(r"/\d\d?", '', header)
                    day, month, year = re.findall(r"\d\d\.\d\d\.\d\d\d\d", header)[0].split('.')
                    date = datetime.datetime(int(year), int(month), int(day), hour, tzinfo=self.tz)
                    space = re.compile(r'  +')
                    #line = unicode(line, 'utf-8')
                    fc = space.split(line)
                    forecast[date] = fc[1:]
        return forecast

    def uvi(self, location):
        directory = 'gds/specials/warnings/FG'
        forecast = {}
        for frame in ['12', '36', '60']:
            filename = "{0}/u_vindex{1}.xml".format(directory, frame)
            fb = self._retr_file(filename)
            year, month, day = re.findall(r"\d\d\d\d\-\d\d\-\d\d", fb)[0].split('-')
            date = datetime.datetime(int(year), int(month), int(day), tzinfo=self.tz)
            uv = re.findall(r"%s<\/tns:Ort>\n *<tns:Wert>([^<]+)" % location, fb)[0]
            forecast[date] = int(uv)
        return forecast

    def pollen(self, region):
        return
        # XXX ftp path broken
        filename = 'gds/specials/warnings/FG/sb31fg.xml'
        filexml = self._retr_file(filename)
        fxp = xml.etree.ElementTree.fromstring(filexml)
        date = fxp.attrib['last_update'].split()[0].split('-')
        day0 = datetime.date(int(date[0]), int(date[1]), int(date[2]))
        day1 = day0 + dateutil.relativedelta.relativedelta(days=1)
        day2 = day0 + dateutil.relativedelta.relativedelta(days=2)
        day0 = day0.isoformat()
        day1 = day1.isoformat()
        day2 = day2.isoformat()
        forecast = {day0: {}, day1: {}, day2: {}}
        for reg in fxp.findall('region'):
            for preg in reg.findall('partregion'):
                if preg.attrib['name'] == region:
                    for kind in preg:
                        kindflag = False
                        kindforc = []
                        for day in kind:
                            value = day.text.replace('/', '')
                            if value != '':
                                kindflag = True
                            kindforc.append(value)
                        if kindflag:
                            forecast[day0][kind.tag] = kindforc[0]
                            forecast[day1][kind.tag] = kindforc[1]
                            forecast[day2][kind.tag] = kindforc[2]
        return forecast
