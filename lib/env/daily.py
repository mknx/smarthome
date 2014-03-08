#!/usr/bin/env python3
#

if trigger['value'] == 'init':
    h = random.randrange(2, 5)
    m = random.randrange(0, 59)
    sh.scheduler.change(logic.name, cron="{} {} * *".format(m, h))
    exit()

import hashlib
import urllib.parse

import lib.www

## check version
data = {}
try:
    data['u'] = int((sh.now() - sh.env.core.start()).total_seconds() / 86400)
    data['i'] = sh.item_count
    data['p'] = len(sh._plugins._plugins)
    __ = sh.version.split('.')
    data['v'] = float('.'.join([__[0], __[1]]))
    data['c'] = int(__[2])
    if len(__) == 4:
        data['b'] = __[3]
except:
    pass
try:
    with open('/sys/class/net/eth0/address', 'r') as f:
        __ = f.readline().strip()
        data['m'] = hashlib.md5(__.encode()).hexdigest()
except:
    pass
try:
    body = urllib.parse.urlencode(data)
    content = lib.www.Client().fetch_url("http://get.smarthomepy.de/version", method='POST', body=body, timeout=5)
    if content:
        major, minor, change = content.decode().split('.')
        if float('.'.join([major, minor])) > data['v']:
            sh.env.core.upgrade(True)
        elif int(change) > data['c']:
            sh.env.core.update(True)
except:
    pass
