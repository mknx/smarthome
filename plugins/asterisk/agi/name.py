#!/usr/bin/env python
#
# cp name.py /usr/share/asterisk/agi-bin/name.py
#

import sys
import re
import urllib
import urllib2

while 1:
    line = sys.stdin.readline()
    if not line.startswith('agi_'):
        break
    key,value = line.split(':')
    vars()[key] = value.strip()

if agi_callerid == 'unknown':
    sys.exit()

number = urllib.quote(agi_callerid)
exp = re.compile('<[^>]*id="name0"[^>]*>([^<]+)<', re.MULTILINE)
lookup = urllib2.urlopen("http://www3.dastelefonbuch.de/?kw={0}&cmd=search".format(number), data="User-Agent: Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11", timeout=1)
name = exp.search(lookup.read())
if name != None:
    name = name.group(1).strip()
    sys.stdout.write("SET VARIABLE CALLERID(name) \"{0}\"\n".format(name))
    sys.stdout.flush()
    line = sys.stdin.readline()
    sys.stdout.write("DATABASE PUT cache {0} \"{1}\"\n".format(agi_callerid, name))
    sys.stdout.flush()
    line = sys.stdin.readline()

lookup.fp._sock.recv=None
lookup.close()
