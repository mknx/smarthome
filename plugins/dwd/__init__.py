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
        filepath = "{0}/{1}/*_{2}_*".format(directory, region, location)
        files = self._retr_list(filepath)
        for filename in files:
            fb = self._retr_file(filename)
            fb = fb.decode('iso-8859-1')
            dates = re.findall(r"\d\d\.\d\d\.\d\d\d\d \d\d:\d\d", fb)
            tz = dateutil.tz.gettz('Europe/Berlin')
            now = datetime.datetime.now(tz)
            if len(dates) > 1:  # Entwarnungen haben nur ein Datum
                start = dateutil.parser.parse(dates[0])
                start = start.replace(tzinfo=tz)
                end = dateutil.parser.parse(dates[1])
                end = end.replace(tzinfo=tz)
                notice = dateutil.parser.parse(dates[2])
                notice = notice.replace(tzinfo=tz)
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

    def _forecast(self, filename, location):
            fb = self._retr_file(filename)
            fb = fb.decode('iso-8859-1')
            header = fb.splitlines()[0]
            for line in fb.splitlines():
                if line.count('Termin ist nicht mehr'):
                    # already past
                    return [None, None, None, None]
                elif line.count(location):
                    header = re.sub(r"/\d\d?", '', header)
                    date = re.findall(r"\d\d\.\d\d\.\d\d\d\d", header)[0].split('.')
                    date = "%s-%s-%s" % (date[2], date[1], date[0])
                    space = re.compile(r'  +')
                    line = space.split(line)
                    line[1] = float(line[1])
                    return [date] + line[1:]

    def forecast(self, region, location):
        directory = 'gds/specials/forecasts/tables/germany/Daten_'
        forecast = {}
        filename = "{0}{1}_".format(directory, region)
        d0f = self._forecast(filename + 'frueh', location)
        d0m = self._forecast(filename + 'mittag', location)
        d0s = self._forecast(filename + 'spaet', location)
        d0n = self._forecast(filename + 'nacht', location)
        d1f = self._forecast(filename + 'morgen_frueh', location)
        d1s = self._forecast(filename + 'morgen_spaet', location)
        d2f = self._forecast(filename + 'uebermorgen_frueh', location)
        d2s = self._forecast(filename + 'uebermorgen_spaet', location)
        d3f = self._forecast(filename + 'Tag4_frueh', location)
        d3s = self._forecast(filename + 'Tag4_spaet', location)
        forecast[d0n[0]] = {'temp-f': d0f[1], 'sky-f': d0f[2], 'gust-f': d0f[3],
                            'temp-m': d0m[1], 'sky-m': d0m[2], 'gust-m': d0m[3],
                            'temp-s': d0s[1], 'sky-s': d0s[2], 'gust-s': d0s[3],
                            'temp-n': d0n[1], 'sky-n': d0n[2], 'gust-n': d0n[3]
                        }
        forecast[d1s[0]] = {'temp-min': d1f[1], 'temp-max': d1s[1], 'sky-f': d1f[2], 'sky-s': d1s[2], 'gust-f': d1f[3], 'gust-s': d1s[3]}
        forecast[d2s[0]] = {'temp-min': d2f[1], 'temp-max': d2s[1], 'sky-f': d2f[2], 'sky-s': d2s[2], 'gust-f': d2f[3], 'gust-s': d2s[3]}
        forecast[d3s[0]] = {'temp-min': d3f[1], 'temp-max': d3s[1], 'sky-f': d3f[2], 'sky-s': d3s[2], 'gust-f': d3f[3], 'gust-s': d3s[3]}
        return forecast

    def uvi(self, location):
        directory = 'gds/specials/warnings/FG'
        forecast = {}
        for frame in ['12', '36', '60']:
            filename = "{0}/u_vindex{1}.xml".format(directory, frame)
            fb = self._retr_file(filename)
            date = re.findall(r"\d\d\d\d\-\d\d\-\d\d", fb)[0]
            uv = re.findall(r"%s<\/tns:Ort>\n *<tns:Wert>([^<]+)" % location, fb)
            forecast[date] = int(uv[0])
        return forecast

    def pollen(self, region):
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
