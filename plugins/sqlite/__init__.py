#!/usr/bin/env python3
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

    _version = 1
    # (period days, granularity hours)
    periods = [(1900, 168), (400, 24), (32, 1), (7, 0.5), (1, 0.1)]
    # SQL queries
    # time, item, cnt, val, vsum, vmin, vmax, vavg, power
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
        WHERE (time < {})
        GROUP by CAST((time / {}) AS INTEGER), item
        ORDER BY time DESC;"""

    def __init__(self, smarthome, path=None):
        self._sh = smarthome
        self.connected = False
#       sqlite3.register_adapter(datetime.datetime, self._timestamp)
        logger.debug("SQLite {0}".format(sqlite3.sqlite_version))
        self._fdb_lock = threading.Lock()
        self._fdb_lock.acquire()
        if path is None:
            self.path = smarthome.base_dir + '/var/db/smarthome.db'
        else:
            self.path = path + '/smarthome.db'
        try:
            self._fdb = sqlite3.connect(self.path, check_same_thread=False)
        except Exception as e:
            logger.error("SQLite: Could not connect to the database {}: {}".format(self.path, e))
            self._fdb_lock.release()
            return
        self.connected = True
        integrity = self._fdb.execute("PRAGMA integrity_check(10);").fetchone()[0]
        if integrity == 'ok':
            logger.debug("SQLite: database integrity ok")
        else:
            logger.error("SQLite: database corrupt. Seek help.")
            self._fdb_lock.release()
            return
        journal = self._fdb.execute("PRAGMA journal_mode=WAL;").fetchone()[0]
        logger.debug("SQLite: database journal: {}".format(journal))
        common = self._fdb.execute("SELECT * FROM sqlite_master WHERE name='common' and type='table';").fetchone()
        if common is None:
            self._fdb.execute("CREATE TABLE common (version INTEGER);")
            self._fdb.execute("INSERT INTO common VALUES (:version);", {'version': self._version})
            self._fdb.execute(self._create_db)
            self._fdb.execute(self._create_index)
            version = self._version
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
        smarthome.scheduler.add('SQLite pack', self._pack, cron='2 3 * *', prio=5)

    def update_item(self, item, caller=None, source=None, dest=None):
        now = self._timestamp(self._sh.now())
        val = float(item())
        power = int(bool(val))
        if item.conf['sqlite'] == 'sum':
            sum = val
        else:
            sum = 0
        if not self._fdb_lock.acquire(timeout=20):
            return
        if not self.connected:
            self._fdb_lock.release()
            return
        try:
            self._fdb.execute("INSERT INTO history VALUES (:now, :item, 1, :val, :sum, :val, :val, :val, :power)", {'now': now, 'item': item.id(), 'val': val, 'sum': sum, 'power': power})
            self._fdb.commit()
        except Exception as e:
            logger.warning("SQLite: problem updating {}: {}".format(item.id(), e))
        self._fdb_lock.release()

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False
        self._fdb_lock.acquire()
        try:
            self._fdb.close()
        except Exception:
            pass
        finally:
            self.connected = False
            self._fdb_lock.release()

    def parse_item(self, item):
        if 'history' in item.conf:  # XXX legacy history option remove sometime
            item.conf['sqlite'] = item.conf['history']
        if 'sqlite' in item.conf:
            item.series = functools.partial(self._series, item=item.id())
            item.db = functools.partial(self._single, item=item.id())
            if item.conf['sqlite'] == 'init':
                last = self._fetchone("SELECT val from history WHERE item = '{0}' ORDER BY time DESC LIMIT 1".format(item.id()))
                if last is not None:
                    last = last[0]
                    item.set(last, 'SQLite')
            return self.update_item
        else:
            return None

    def parse_logic(self, logic):
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    def _timestamp(self, dt):
        return time.mktime(dt.timetuple()) * 1000 + int(dt.microsecond / 1000)

    def _datetime(self, ts):
        return datetime.datetime.fromtimestamp(ts / 1000, self._sh.tzinfo())

    def _get_timestamp(self, frame='now'):
        try:
            return int(frame)
        except:
            pass
        dt = self._sh.now()
        ts = int(time.mktime(dt.timetuple()) * 1000 + dt.microsecond / 1000)
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

    def _fetchone(self, *query):
        if not self._fdb_lock.acquire(timeout=2):
            return
        if not self.connected:
            self._fdb_lock.release()
            return
        try:
            reply = self._fdb.execute(*query).fetchone()
        except Exception as e:
            logger.warning("SQLite: Problem with '{0}': {1}".format(query, e))
            reply = None
        finally:
            self._fdb_lock.release()
        return reply

    def _fetchall(self, *query):
        if not self._fdb_lock.acquire(timeout=2):
            return
        if not self.connected:
            self._fdb_lock.release()
            return
        try:
            reply = self._fdb.execute(*query).fetchall()
        except Exception as e:
            logger.warning("SQLite: Problem with '{0}': {1}".format(query, e))
            reply = None
        finally:
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

    def _avg_ser(self, tuples, end):
        prev = end
        result = []
        for tpl in tuples:
            if len(tpl) == 2:
                times, vals = tpl
            else:
                continue
            tpls = [(int(float(t)), float(v)) for t in times.split(',') for v in vals.split(',')]
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
        reply = {'cmd': 'series', 'series': None, 'sid': sid}
        _value = ''  # XXX
        try:
            istart = self._get_timestamp(start)
            iend = self._get_timestamp(end)
            prev = self._fetchone("SELECT time from history WHERE item='{0}' AND time <= {1} ORDER BY time DESC LIMIT 1".format(item, istart))
            _value = prev  # XXX
            if prev is None:
                first = istart
            else:
                first = prev[0]
            _value = first  # XXX
            where = " from history WHERE item='{0}' AND time >= {1} AND time <= {2}".format(item, first, iend)
            if step is None:
                if count != 0:
                    step = (iend - istart) / count
                else:
                    step = (iend - istart)
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
                tuples = self._fetchall(query)
            except Exception as e:
                logger.warning("Problem {0} with query: {1}".format(e, query))
                return reply
            if tuples is None:
                return reply
            _value = tuples  # XXX
            if func == 'avg':
                tuples = self._avg_ser(tuples, iend)  # compute avg for concatenation groups
            elif func == 'diff':
                tuples = self._diff_ser(tuples)  # compute diff for concatenation groups
            elif func == 'rate':
                tuples = self._rate_ser(tuples, ratio)  # compute diff for concatenation groups
            _value = tuples  # XXX
            tuples = [(istart, t[1]) if first == t[0] else t for t in tuples]  # replace 'first' time with 'start' time
            _value = tuples  # XXX
            tuples = sorted(tuples)
            lval = tuples[-1][1]
            tuples.append((iend, lval))  # add end entry with last valid entry
            _value = tuples  # XXX
            if update:  # remove first entry
                tuples = tuples[1:]
            _value = tuples  # XXX
            step = int(step / 1000)
            reply['series'] = tuples
            reply['params'] = {'update': True, 'item': item, 'func': func, 'start': iend, 'end': end, 'step': step, 'sid': sid}
            reply['update'] = self._sh.now() + datetime.timedelta(seconds=step)
            return reply
        except Exception as e:
            logger.exception("SQLite: problem generating series value: '{}': {}".format(_value, e))
            return reply

    def _single(self, func, start, end='now', item=None):
        start = self._get_timestamp(start)
        end = self._get_timestamp(end)
        prev = self._fetchone("SELECT time from history WHERE item = '{0}' AND time <= {1} ORDER BY time DESC LIMIT 1".format(item, start))
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
        tuples = self._fetchall(query)
        if tuples is None:
            return
        if func == 'avg':
            tuples = [(start, t[1]) if first == t[0] else t for t in tuples]  # replace 'first' time with 'start' time
            return self._avg(tuples, end)
        else:
                return tuples[0][0]

    def _pack(self):
        now = self._timestamp(self._sh.now())
        insert = []
        delete = []
        if not self._fdb_lock.acquire(timeout=2):
            return
        try:
            logger.debug("SQLite: pack database")
            for entry in self.periods:
                prev = {}
                period, granularity = entry
                period = int(now - period * 24 * 3600 * 1000)
                granularity = int(granularity * 3600 * 1000)
                for row in self._fdb.execute(self._pack_query.format(period, granularity)):
                    gid, gtime, gval, gvavg, gpower, item, cnt, vsum, vmin, vmax = row
                    gtime = [int(float(t)) for t in gtime.split(',')]
                    if len(gtime) == 1:  # ignore
                        prev[item] = gtime[0]
                        continue
                    if item not in prev:
                        upper = now
                    else:
                        upper = prev[item]
                    # pack !!!
                    delete = gid
                    gval = list(map(float, gval.split(',')))
                    gvavg = list(map(float, gvavg.split(',')))
                    gpower = list(map(float, gpower.split(',')))
                    avg = self._avg(list(zip(gtime, gvavg)), upper)
                    power = self._avg(list(zip(gtime, gpower)), upper)
                    prev[item] = gtime[0]
                    # (time, item, cnt, val, vsum, vmin, vmax, vavg, power)
                    insert = (gtime[0], item, cnt, gval[0], vsum, vmin, vmax, avg, power)
                    self._fdb.execute("INSERT INTO history VALUES (?,?,?,?,?,?,?,?,?);", insert)
                    self._fdb.execute("DELETE FROM history WHERE rowid in ({0});".format(delete))
                    self._fdb.commit()
            self._fdb.execute("VACUUM;")
            self._fdb.execute("PRAGMA shrink_memory;")
        except Exception as e:
            logger.exception("problem packing sqlite database: {} period: {} type: {}".format(e, period, type(period)))
            self._fdb.rollback()
        finally:
            self._fdb_lock.release()
