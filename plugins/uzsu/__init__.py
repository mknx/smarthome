#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2011-2013 Niko Will
#########################################################################
#  This file is part of SmartHome.py.    http://mknx.github.io/smarthome/
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

import logging
import datetime
from datetime import datetime, date, time
import sqlite3
import functools
import time
import threading

import dateutil.relativedelta
from dateutil.relativedelta import MO, TU, WE, TH, FR, SA, SU
from dateutil.tz import tzutc
from dateutil.rrule import *
from dateutil import parser

logger = logging.getLogger('')

class UZSU():

    _version = 1        # database version
    _items = {}         # item buffer for all uzsu enabled items

    # SQL table definition
    # id        row id to identify the entry
    # item      item for which an entry is for
    # dt        the date when to set the value or the start of a recurring action
    # active    False disables a entry temporarily
    # time      time when to set the value. A %H:%M string or in combination with sunrise/set eg. "17:00" or "17:00<sunset<20:00"
    # value     the value which will be set to the item
    # rrule     the recurring rule according RFC 2445 (ftp://ftp.rfc-editor.org/in-notes/rfc2445.txt)
    _create_db = "CREATE TABLE IF NOT EXISTS uzsu (id INTEGER PRIMARY KEY ASC, item TEXT, dt TIMESTAMP, active BOOLEAN, time TEXT, value TEXT, rrule TEXT);"

    def __init__(self, smarthome, path=None):
        logger.info('Init UZSU')
        logger.debug("UZSU uses SQLite {0}".format(sqlite3.sqlite_version))
        self._sh = smarthome
        self.connected = False
        # Connect to the database.
        self._fdb_lock = threading.Lock()
        self._fdb_lock.acquire()
        if path is None:
            self.path = smarthome.base_dir + '/var/db/uzsu.db'
        else:
            self.path = path + '/uzsu.db'
        try:
            self._fdb = sqlite3.connect(self.path, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
        except Exception as e:
            logger.error("UZSU: Could not connect to the database {}: {}".format(self.path, e))
            self._fdb_lock.release()
            return
        self.connected = True
        # Check the database integrity
        integrity = self._fdb.execute("PRAGMA integrity_check(10);").fetchone()[0]
        if integrity == 'ok':
            logger.debug("UZSU: database integrity ok")
        else:
            logger.error("UZSU: database corrupt. Seek help.")
            self._fdb_lock.release()
            return
        # Add the factory for the results.
        # With this, every row result is stored as a dictionary with the column name as key
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d
        self._fdb.row_factory = dict_factory
        # Check the version
        common = self._fdb.execute("SELECT * FROM sqlite_master WHERE name='common' and type='table';").fetchone()
        if common is None:
            self._fdb.execute("CREATE TABLE common (version INTEGER);")
            self._fdb.execute("INSERT INTO common VALUES (:version);", {'version': self._version})
            version = self._version
        else:
            version = int(self._fdb.execute("SELECT version FROM common;").fetchone()['version'])
        if version < self._version:
            self._fdb.execute("UPDATE common SET version=:version;", {'version': self._version})
        # Create the database
        self._fdb.execute(self._create_db)
        self._fdb.commit()
        self._fdb_lock.release()

    def parse_item(self, item):
        if 'uzsu' in item.conf:
            result = self._db_fetchall(item)
            self._items[item] = result if result else []

    def run(self):
        self.alive = True
        for item in self._items:
            for entry in self._items[item]:
                self._schedule(item, entry['id'])

    def stop(self):
        self.alive = False
        self._dump()
        self._fdb_lock.acquire()
        try:
            self._fdb.close()
        except Exception:
            pass
        finally:
            self.connected = False
            self._fdb_lock.release()

    def get(self, item):
        return self._items[item]

    def add(self, item, dt, value, active=True, time=None, rrule=None):
        self._items[item].append({'id': None, 'item': item.__str__(), 'dt': dt, 'active': active, 'rrule': rrule, 'time': time, 'value': value})
        if self._db_update(item, self._items[item][-1]):
            self._schedule(item, self._items[item][-1]['id'])

    def update(self, item, id, dt=None, value=None, active=True, time=None, rrule=None):
        entry = self._get_entry(item, id)
        if entry:
            entry['active'] = active
            if dt:
                entry['dt'] = dt
            if time:
                entry['time'] = time
            if value:
                entry['value'] = value
            if rrule:
                entry['rrule'] = rrule
            if self._db_update(item, entry):
                self._schedule(item, id)

    def remove(self, item, id):
        if self._db_remove(item, id):
            self._sh.scheduler.remove('uzsu_{}_{}'.format(item, id))
            self._items[item].remove(self._get_entry(item, id))

    def _schedule(self, item, id):
        next = self._next_time(item, id)
        if next: # and next > datetime.now(self._sh.tzinfo()):
            self._sh.scheduler.remove('uzsu_{}_{}'.format(item, id))
            if self._get_entry(item, id)['active']:
                self._sh.scheduler.add('uzsu_{}_{}'.format(item, id), self._set, value={'item': item, 'id': id}, next=next)
        else:
            self.remove(item, id)

    def _set(self, **kwargs):
        item = kwargs['item']
        id = kwargs['id']
        item(value=self._get_entry(item, id)['value'], caller='UZSU')
        self._schedule(item, id)

    def _get_entry(self, item, id):
        return next(x for x in self._items[item] if x['id'] == id)

    def _next_time(self, item, id):
        entry = self._get_entry(item, id)
        now = datetime.now()
        dt = entry['dt']
        timestr = entry['time']
        rrule = rrulestr(entry['rrule'], dtstart=dt) if entry['rrule'] else None
        try:
            if timestr and rrule:
                dt = now
                while self.alive:
                    dt = rrule.after(dt)
                    if dt is None:
                        return
                    if 'sun' in timestr:
                        next = self._sun(datetime.combine(dt.date(), datetime.min.time()).replace(tzinfo=self._sh.tzinfo()), timestr)
                    else:
                        next = datetime.combine(dt.date(), parser.parse(timestr.strip()).time()).replace(tzinfo=self._sh.tzinfo())
                    if next and next.date() == dt.date() and next > datetime.now(self._sh.tzinfo()):
                        return next
            elif rrule:
                next = rrule.after(now)
                return next.replace(tzinfo=self._sh.tzinfo()) if next else None
            elif timestr:
                if 'sun' in timestr:
                    next = self.sun(datetime.combine(dt.date(), datetime.min.time()).replace(tzinfo=self._sh.tzinfo()), timestr)
                else:
                    next = datetime.combine(dt.date(), parser.parse(timestr.strip()).time()).replace(tzinfo=self._sh.tzinfo())
                if next and next.date() == dt.date() and next > datetime.now(self._sh.tzinfo()):
                    return next
            elif dt > now:
                return dt.replace(tzinfo=self._sh.tzinfo())
        except Exception as e:
            logger.error("Error parsing time {}: {}".format(timestr, e))

    def _sun(self, dt, tstr):
        if not self._sh.sun:  # no sun object created
            logger.warning('No latitude/longitude specified. You could not use sunrise/sunset as UZSU entry.')
            return
        # find min/max times
        tabs = tstr.split('<')
        if len(tabs) == 1:
            smin = None
            cron = tabs[0].strip()
            smax = None
        elif len(tabs) == 2:
            if tabs[0].startswith('sun'):
                smin = None
                cron = tabs[0].strip()
                smax = tabs[1].strip()
            else:
                smin = tabs[0].strip()
                cron = tabs[1].strip()
                smax = None
        elif len(tabs) == 3:
            smin = tabs[0].strip()
            cron = tabs[1].strip()
            smax = tabs[2].strip()
        else:
            logger.error('Wrong syntax: {0}. Should be [H:M<](sunrise|sunset)[+|-][offset][<H:M]'.format(tstr))
            return

        doff = 0  # degree offset
        moff = 0  # minute offset
        tmp, op, offs = cron.rpartition('+')
        if op:
            if offs.endswith('m'):
                moff = int(offs.strip('m'))
            else:
                doff = float(offs)
        else:
            tmp, op, offs = cron.rpartition('-')
            if op:
                if offs.endswith('m'):
                    moff = -int(offs.strip('m'))
                else:
                    doff = -float(offs)

        if cron.startswith('sunrise'):
            next_time = self._sh.sun.rise(doff, moff, dt=dt)
        elif cron.startswith('sunset'):
            next_time = self._sh.sun.set(doff, moff, dt=dt)
        else:
            logger.error('Wrong syntax: {0}. Should be [H:M<](sunrise|sunset)[+|-][offset][<H:M]'.format(tstr))
            return

        if smin is not None:
            h, sep, m = smin.partition(':')
            try:
                dmin = next_time.replace(hour=int(h), minute=int(m), second=0, tzinfo=self._sh.tzinfo())
            except Exception:
                logger.error('Wrong syntax: {0}. Should be [H:M<](sunrise|sunset)[+|-][offset][<H:M]'.format(tstr))
                return
            if dmin > next_time:
                next_time = dmin
        if smax is not None:
            h, sep, m = smax.partition(':')
            try:
                dmax = next_time.replace(hour=int(h), minute=int(m), second=0, tzinfo=self._sh.tzinfo())
            except Exception:
                logger.error('Wrong syntax: {0}. Should be [H:M<](sunrise|sunset)[+|-][offset][<H:M]'.format(tstr))
                return
            if dmax < next_time:
                next_time = dmax
        return next_time

    def _db_fetchall(self, item):
        if not self._fdb_lock.acquire(timeout=2):
            logger.error("UZSU: init item {} failed - db is locked".format(item))
            return
        if not self.connected:
            logger.error("UZSU: init item {} failed - db is disconnected".format(item))
            self._fdb_lock.release()
            return
        try:
            return self._fdb.execute("SELECT * FROM uzsu WHERE item='{0}' ORDER BY id".format(item)).fetchall()
        except Exception as e:
            logger.error("UZSU: init item {} failed - db query failed".format(item))
        finally:
            self._fdb_lock.release()

    def _db_update(self, item, entry):
        if not self._fdb_lock.acquire(timeout=10):
            logger.error("UZSU: insert or replace item {} failed - lock timeout".format(entry['item']))
            return
        try:
            columns = ', '.join(entry.keys())
            placeholders = ', '.join('?' * len(entry))
            sql = 'INSERT OR REPLACE INTO uzsu ({}) VALUES ({})'.format(columns, placeholders)
            entry['id'] = self._fdb.execute(sql, tuple(entry.values())).lastrowid
            self._fdb.commit()
            logger.debug("UZSU: dumped item {} success - values: {}".format(item, entry))
            return True
        except Exception as e:
            logger.warning("UZSU: insert or replace item {} failed: {}".format(item, e))
        finally:
            self._fdb_lock.release()

    def _db_remove(self, item, id):
        if not self._fdb_lock.acquire(timeout=10):
            logger.error("UZSU: remove item {} failed - lock timeout".format(item))
            return
        try:
            self._fdb.execute("DELETE FROM uzsu WHERE id = ?;", (id,))
            self._fdb.commit()
            logger.debug("UZSU: removed id {} from item".format(id))
            return True
        except Exception as e:
            logger.warning("UZSU: problem removing {}: {}".format(id, e))
        finally:
            self._fdb_lock.release()