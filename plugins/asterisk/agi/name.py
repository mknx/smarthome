#!/usr/bin/env python
#
import sys
import re
import urllib2

while 1:
    line = sys.stdin.readline()
    if not line.startswith('agi_'):
        break
    key,value = line.split(':')
    vars()[key] = value.strip()

if agi_callerid == 'unknown':
    sys.exit()

exp = re.compile('<[^>]*id="name0"[^>]*>([^<]+)<', re.MULTILINE)
lookup = urllib2.urlopen("http://www.dastelefonbuch.de/?kw={0}&cmd=search".format(agi_callerid), data="User-Agent: Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11", timeout=1)
lookup = exp.search(lookup.read())
if lookup != None:
    name = lookup.group(1).strip()
    sys.stdout.write("SET VARIABLE CALLERID(name) \"{0}\"\n".format(name))
    sys.stdout.flush()
    #result = sys.stdin.readline()
    sys.stdout.write("DATABASE PUT cache {0} \"{1}\"\n".format(agi_callerid, name))
    sys.stdout.flush()
    #result = sys.stdin.readline().strip()

lookup.fp._sock.recv=None
lookup.close()
