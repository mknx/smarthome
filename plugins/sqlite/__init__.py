#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 Marcus Popp                               marcus@popp.mx
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
import sqlite3
import datetime
import functools
import time
import threading

logger = logging.getLogger('')


class SQL():

    # (period days, granularity hours)
    periods = [(1900, 168), (400, 24), (32, 1), (7, 0.5), (1, 0.1)]
    # SQL queries
    _create_db = "CREATE TABLE IF NOT EXISTS history (time INTEGER, item TEXT, cnt INTEGER, val REAL, vsum REAL, vmin REAL, vmax REAL, vavg REAL, power REAL);"
    _create_index = "CREATE INDEX IF NOT EXISTS idx ON history (time, item)"
    _pack_query = """
        SELECT
        group_concat(rowid),
        group_concat(time),
        group_concat(val),
        group_concat(vavg),
        group_concat(power),
        item,
        SUM(cnt),
        SUM(vsum),
        MIN(vmin),
        MAX(vmax)
        FROM history
        WHERE time <= :period
        GROUP by CAST((time / :granularity) AS INTEGER), item
        ORDER BY time DESC """

    def __init__(self, smarthome):
        self._sh = smarthome
        self._version = 1
        sqlite3.register_adapter(datetime.datetime, self.timestamp)
        logger.debug("SQLite {0}".format(sqlite3.sqlite_version))
        self.connected = True
        self._fdb = sqlite3.connect(smarthome.base_dir + '/var/db/smarthome.db', check_same_thread=False)
        self._fdb_lock = threading.Lock()
        self._fdb_lock.acquire()
        common = self._fdb.execute("SELECT * FROM sqlite_master WHERE name='common' and type='table';").fetchone()
        if common is None:
            self._fdb.execute("CREATE TABLE common (version INTEGER);")
            self._fdb.execute("INSERT INTO common VALUES (:version);", {'version': self._version})
            self._fdb.execute(self._create_db)
            self._fdb.execute(self._create_index)
        else:
            version = int(self._fdb.execute("SELECT version FROM common;").fetchone()[0])
        if version < self._version:
            logger.debug("update database")
            self._fdb.execute("UPDATE common SET version=:version;", {'version': self._version})
        self._fdb.commit()
        self._fdb_lock.release()
        minute = 60 * 1000
        hour = 60 * minute
        day = 24 * hour
        week = 7 * day
        month = 30 * day
        year = 365 * day
        self._frames = {'i': minute, 'h': hour, 'd': day, 'w': week, 'm': month, 'y': year}
        self._times = {'i': minute, 'h': hour, 'd': day, 'w': week, 'm': month, 'y': year}
        # self.query("alter table history add column power INTEGER;")
        smarthome.scheduler.add('sqlite', self._pack, cron='2 3 * *', prio=5)

    def update_item(self, item, caller=None, source=None, dest=None):
        if not self.connected:
            return
        now = self.timestamp(self._sh.now())
        val = float(item())
        power = int(bool(val))
        self._fdb_lock.acquire()
        self._fdb.execute("INSERT INTO history VALUES (:now, :item, 1, :val, :val, :val, :val, :val, :power)", {'now': now, 'item': item.id(), 'val': val, 'power': power})
        self._fdb.commit()
        self._fdb_lock.release()
        #self.dump()

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        if 'sqlite' in item.conf or 'history' in item.conf:  # XXX legacy history option remove sometime
            item.series = functools.partial(self._series, item=item.id())
            item.db = functools.partial(self._single, item=item.id())
            return self.update_item
        else:
            return None

    def parse_logic(self, logic):
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    def timestamp(self, dt):
        return int(time.mktime(dt.timetuple())) * 1000 + dt.microsecond / 1000

    def datetime(self, ts):
        return datetime.datetime.fromtimestamp(ts / 1000, self._sh.tzinfo())

    def get_timestamp(self, frame='now'):
        try:
            return int(frame)
        except:
            pass
        dt = self._sh.now()
        ts = int(time.mktime(dt.timetuple())) * 1000 + dt.microsecond / 1000
        if frame == 'now':
            fac = 0
            frame = 0
        elif frame[-1] in self._frames:
            fac = self._frames[frame[-1]]
            frame = frame[:-1]
        else:
            return frame
        try:
            ts = ts - int(float(frame) * fac)
        except:
            logger.warning("DB select: unkown time frame '{0}'".format(frame))
        return ts

    def query(self, *query):
        if not self.connected:
            return
        self._fdb_lock.acquire()
        #logger.info(*query)
        reply = self._fdb.execute(*query)
        self._fdb_lock.release()
        return reply

    def _avg(self, tuples, end):
        sum = 0.0
        span = 1
        prev = end
        for time, val in sorted(tuples, reverse=True):
            sum += (prev - time) * val
            prev = time
            span = end - time
        if span != 0:
            return sum / span
        else:
            return val

    def _cast_tuples(self, time, val):
        return (int(time), float(val))

    def _avg_ser(self, tuples, end):
        prev = end
        result = []
        for tpl in tuples:
            if len(tpl) == 2:
                times, vals = tpl
            else:
                continue
            tpls = map(self._cast_tuples, times.split(','), vals.split(','))
            avg = self._avg(tpls, prev)
            first = sorted(tpls)[0][0]
            prev = first
            result.append((first, round(avg, 4)))
        return result

    def _diff_ser(self, tuples):
        result = []
        prev = None
        for tpl in tuples:
            if len(tpl) == 2:
                times, vals = tpl
            else:
                continue
            if prev is not None:
                result.append((int(times.split(',')[0]), prev - float(vals.split(',')[0])))  # fetch only the first entry, ingore the rest
            prev = float(vals.split(',')[0])
        return result

    def _rate_ser(self, tuples, ratio):
        result = []
        prev_val = None
        prev_time = None
        ratio *= 1000
        for tpl in tuples:
            if len(tpl) == 2:
                times, vals = tpl
            else:
                continue
            if prev_val is not None:
                time = int(times.split(',')[0])
                val = float(vals.split(',')[0])
                rate = ratio * (prev_val - val) / (prev_time - time)
                result.append((time, rate))
            prev_time = int(times.split(',')[0])
            prev_val = float(vals.split(',')[0])
        return result

    def _series(self, func, start, end='now', count=100, ratio=1, update=False, step=None, sid=None, item=None):
        if sid is None:
            sid = item + '|' + func + '|' + start + '|' + end
        istart = self.get_timestamp(start)
        iend = self.get_timestamp(end)
        prev = self.query("SELECT time from history WHERE item='{0}' AND time <= {1} ORDER BY time DESC LIMIT 1".format(item, istart)).fetchone()
        if prev is None:
            first = istart
        else:
            first = prev[0]
        where = " from history WHERE item='{0}' AND time >= {1} AND time <= {2}".format(item, first, iend)
        if step is None:
            if count != 0:
                step = (iend - istart) / count
            else:
                step = (iend - istart)
        reply = {'cmd': 'series', 'series': None, 'sid': sid}
        where += " GROUP by CAST((time / {0}) AS INTEGER)".format(step)
        if func == 'avg':
            query = "SELECT group_concat(time), group_concat(vavg)" + where + " ORDER BY time DESC"
        elif func in ('diff-ser', 'rate-ser'):
            query = "SELECT group_concat(time), group_concat(val)" + where + " ORDER BY time ASC"
        elif func == 'rate':
            query = "SELECT group_concat(time), group_concat(val)" + where + " ORDER BY time ASC"
        elif func == 'min':
            query = "SELECT MIN(time), MIN(vmin)" + where
        elif func == 'max':
            query = "SELECT MIN(time), MAX(vmax)" + where
        elif func == 'sum':
            query = "SELECT MIN(time), SUM(vsum)" + where
        else:
            logger.warning("Unknown export function: {0}".format(func))
            return reply
        try:
            tuples = self.query(query).fetchall()
        except Exception, e:
            logger.warning("Problem {0} with query: {1}".format(e, query))
            return reply
        if tuples == []:
            return reply
        if func == 'avg':
            tuples = self._avg_ser(tuples, iend)  # compute avg for concatenation groups
        elif func == 'diff':
            tuples = self._diff_ser(tuples)  # compute diff for concatenation groups
        elif func == 'rate':
            tuples = self._rate_ser(tuples, ratio)  # compute diff for concatenation groups
        tuples = [(istart, t[1]) if first == t[0] else t for t in tuples]  # replace 'first' time with 'start' time
        tuples = sorted(tuples)
        lval = tuples[-1][1]
        tuples.append((iend, lval))  # add end entry with last valid entry
        if update:  # remove first entry
            tuples = tuples[1:]
        reply['series'] = tuples
        reply['params'] = {'update': True, 'item': item, 'func': func, 'start': iend, 'end': end, 'step': step, 'sid': sid}
        reply['update'] = self.datetime(iend + step)
        return reply

    def _single(self, func, start, end='now', item=None):
        start = self.get_timestamp(start)
        end = self.get_timestamp(end)
        prev = self.query("SELECT time from history WHERE item='{0}' AND time =< {1} ORDER BY time DESC LIMIT 1".format(item, start)).fetchone()
        if prev is None:
            first = start
        else:
            first = prev[0]
        where = " from history WHERE item='{0}' AND time >= {1} AND time < {2}".format(item, first, end)
        if func == 'avg':
            query = "SELECT time, vavg" + where
        elif func == 'min':
            query = "SELECT MIN(vmin)" + where
        elif func == 'max':
            query = "SELECT MAX(vmax)" + where
        elif func == 'sum':
            query = "SELECT SUM(vsum)" + where
        else:
            logger.warning("Unknown export function: {0}".format(func))
            return
        tuples = self.query(query).fetchall()
        if tuples is None:
            return
        if func == 'avg':
            tuples = [(start, t[1]) if first == t[0] else t for t in tuples]  # replace 'first' time with 'start' time
            return self._avg(tuples, end)
        else:
                return tuples[0][0]

    def _pack(self):
        now = self.timestamp(datetime.datetime.now())
        insert = []
        delete = []
        self._fdb_lock.acquire()
        try:
            for entry in self.periods:
                prev = now
                period, granularity = entry
                period = now - period * 24 * 3600 * 1000
                granularity = int(granularity * 3600 * 1000)
                for row in self._fdb.execute(self._pack_query, {'period': period, 'granularity': granularity}).fetchall():
                    gid, gtime, gval, gvavg, gpower, item, cnt, vsum, vmin, vmax = row
                    gtime = map(int, gtime.split(','))
                    if len(gtime) == 1:  # ignore
                        continue
                    # pack !!!
                    delete.append(gid)
                    gval = map(float, gval.split(','))
                    gvavg = map(float, gvavg.split(','))
                    gpower = map(float, gpower.split(','))
                    avg = self._avg(zip(gtime, gvavg), prev)
                    power = self._avg(zip(gtime, gpower), prev)
                    prev = gtime[0]
                    # (time, item, cnt, val, vsum, vmin, vmax, vavg, power)
                    insert.append((gtime[0], item, cnt, gval[0], vsum, vmin, vmax, avg, power))
            self._fdb.executemany("INSERT INTO history VALUES (?,?,?,?,?,?,?,?,?)", insert)
            self._fdb.execute("DELETE FROM history WHERE rowid in ({0})".format(','.join(delete)))
            self._fdb.commit()
            self._fdb.execute("VACUUM")
        except Exception, e:
            logger.warning("problem packing sqlite database: {0}".format(e))
            self._fdb.rollback()
        self._fdb_lock.release()

    def dump(self):
        for row in self.query('SELECT rowid, * FROM history ORDER BY time ASC').fetchall():
            print row
