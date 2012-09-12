#!/usr/bin/env python
#
import sys
import socket

while 1:
    line = sys.stdin.readline()
    if not line.startswith('agi_'):
        break
    key,value = line.split(':')
    vars()[key] = value.strip()

callerid = "%s|%s|%s" % (agi_callerid, agi_calleridname, sys.argv[1])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(callerid, ('127.0.0.1', 4444))

