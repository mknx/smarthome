#!/usr/bin/env python3
#
# history: time, item, avg, vmin, vmax, power
# num: _end, _start, _item, _avg, _min, _max, _on


def db2to3(db):
    db.execute("DROP INDEX IF EXISTS idy;")
    for item in db.execute("SELECT item FROM history GROUP BY item;").fetchall():
        end = 0
        for row in db.execute("SELECT * FROM history WHERE item='{}' ORDER BY time DESC;".format(item[0])).fetchall():
            time, item, avg, vmin, vmax, power = row
            if end:
                insert = (end, time, item, avg, vmin, vmax, power)
                db.execute("INSERT INTO num VALUES (?,?,?,?,?,?,?);", insert)
            end = time
    db.execute("DROP TABLE history;")
    db.execute("VACUUM;")
    db.commit()
