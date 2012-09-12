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

lookup = urllib2.urlopen("http://www.dasoertliche.de/Controller?form_name=search_inv&js=no&ph=%s" % agi_callerid, timeout=1)
lookup = lookup.read()
exp = re.compile('na: "([a-zA-Z0-9_ ]+)",', re.MULTILINE)
lookup = exp.search(lookup)
if lookup != None:
    sys.stdout.write("SET VARIABLE CALLERID(name) \"%s\"\n" % lookup.group(1))
    sys.stdout.flush()
    #result = sys.stdin.readline()
    sys.stdout.write("DATABASE PUT cache %s \"%s\"\n" % (agi_callerid, lookup.group(1)))
    sys.stdout.flush()
    #result = sys.stdin.readline().strip()

