#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012-2013 KNX-User-Forum e.V.       http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.
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

import struct
import datetime


def en1(value):
    return [int(value) & 0x01]


def de1(payload):
    if len(payload) != 1:
        return None
    return bool(ord(payload) & 0x01)


def en2(vlist):
    # control, value
    return [(int(vlist[0]) << 1) & 0x02 | int(vlist[1]) & 0x01]


def de2(payload):
    if len(payload) != 1:
        return None
    payload = ord(payload)
    return [int(payload) >> 1 & 0x01, int(payload) & 0x01]


def en3(vlist):
    # direction, value
    return [(int(vlist[0]) << 3) & 0x08 | int(vlist[1]) & 0x07]


def de3(payload):
    if len(payload) != 1:
        return None
    payload = ord(payload)
    # up/down, stepping
    return [int(payload) >> 3 & 0x01, int(payload) & 0x07]


def en4002(value):
    if isinstance(value, unicode):
        value = value.encode('iso-8859-1')
    else:
        value = str(value)
    return [0, ord(value) & 0xff]


def de4002(payload):
    if len(payload) != 1:
        return None
    return payload.decode('iso-8859-1')


def en5(value):
    return [0, int(value) & 0xff]


def de5(payload):
    if len(payload) != 1:
        return None
    return struct.unpack('>B', payload)[0]


def en5001(value):
    return [0, int(int(value) * 255 / 100) & 0xff]


def de5001(payload):
    if len(payload) != 1:
        return None
    return struct.unpack('>B', payload)[0] * 100 / 255


def en6(value):
    if value < -128:
        value = -128
    elif value > 127:
        value = 127
    return [0, ord(struct.pack('b', value)[0])]


def de6(payload):
    if len(payload) != 1:
        return None
    return struct.unpack('b', payload)[0]


def en7(value):
    yield 0
    for c in struct.pack('>H', value):
        yield ord(c)


def de7(payload):
    if len(payload) != 2:
        return None
    return struct.unpack('>H', payload)[0]


def en8(value):
    if value < -32768:
        value = -32768
    elif value > 32767:
        value = 32767
    yield 0
    for c in struct.pack('>h', value):
        yield ord(c)


def de8(payload):
    if len(payload) != 2:
        return None
    return struct.unpack('>h', payload)[0]


def en9(value):
    s = 0
    e = 0
    if value < 0:
        s = 0x8000
    m = int(value * 100)
    while (m > 2047) or (m < -2048):
        e = e + 1
        m = m >> 1
    num = s | (e << 11) | (int(m) & 0x07ff)
    return en7(num)


def de9(payload):
    if len(payload) != 2:
        return None
    i1 = ord(payload[0])
    i2 = ord(payload[1])
    s = (i1 & 0x80) >> 7
    e = (i1 & 0x78) >> 3
    m = (i1 & 0x07) << 8 | i2
    if s == 1:
        s = -1 << 11
    return (m | s) * 0.01 * pow(2, e)


def en10(time):
    return [0, time.hour, time.minute, time.second]


def de10(payload):
    ba = bytearray(payload)
    h = ba[0] & 0x1f
    m = ba[1] & 0x3f
    s = ba[2] & 0x3f
    return datetime.time(h, m, s)


def en11(date):
    return [0, date.day, date.month, date.year - 2000]


def de11(payload):
    ba = bytearray(payload)
    d = ba[0] & 0x1f
    m = ba[1] & 0x0f
    y = (ba[2] & 0x7f) + 2000  # sorry no 20th century...
    return datetime.date(y, m, d)


def en12(value):
    if value < 0:
        value = 0
    elif value > 4294967295:
        value = 4294967295
    yield 0
    for c in struct.pack('>I', value):
        yield ord(c)


def de12(payload):
    if len(payload) != 4:
        return None
    return struct.unpack('>I', payload)[0]


def en13(value):
    if value < -2147483648:
        value = -2147483648
    elif value > 2147483647:
        value = 2147483647
    yield 0
    for c in struct.pack('>i', value):
        yield ord(c)


def de13(payload):
    if len(payload) != 4:
        return None
    return struct.unpack('>i', payload)[0]


def en14(value):
    yield 0
    for c in struct.pack('>f', value):
        yield ord(c)


def de14(payload):
    if len(payload) != 4:
        return None
    return struct.unpack('>f', payload)[0]


def en16000(value):
    if isinstance(value, unicode):
        value = value.encode('ascii')
    else:
        value = str(value)
    value = value[:14]
    a = [0]
    for c in value:
        a.append(ord(c))
    a = a + [0] * (15 - len(a))
    return a


def en16001(value):
    if isinstance(value, unicode):
        value = value.encode('iso-8859-1')
    else:
        value = str(value)
    value = value[:14]
    a = [0]
    for c in value:
        a.append(ord(c))
    a = a + [0] * (15 - len(a))
    return a


def de16(payload):
    return str(payload).rstrip('\0')


def en24(value):
    if isinstance(value, unicode):
        value = value.encode('iso-8859-1')
    else:
        value = str(value)
    yield 0
    for c in value:
        yield ord(c)
    yield 0x00


def de24(payload):
    return str(payload).rstrip('\0')


def depa(string):
    if len(string) != 2:
        return None
    pa = struct.unpack(">H", string)[0]
    return "{0}.{1}.{2}".format((pa >> 12) & 0x0f, (pa >> 8) & 0x0f, (pa) & 0xff)


def enga(ga):
    ga = ga.split('/')
    return [int(ga[0]) << 3 | int(ga[1]), int(ga[2])]


def dega(string):
    if len(string) != 2:
        return None
    ga = struct.unpack(">H", string)[0]
    return "{0}/{1}/{2}".format((ga >> 11) & 0x1f, (ga >> 8) & 0x07, (ga) & 0xff)


def dehex(payload):
    #xlist = ["{0:02x}".format(ord(char)) for char in payload]
    xlist = ["{0:x}".format(ord(char)) for char in payload]
    return ' '.join(xlist)


decode = {
    '1': de1,
    '2': de2,
    '3': de3,
    '4002': de4002,
    '5': de5,
    '5001': de5001,
    '6': de6,
    '7': de7,
    '8': de8,
    '9': de9,
    '10': de10,
    '11': de11,
    '12': de12,
    '13': de13,
    '14': de14,
    '16000': de16,
    '16001': de16,
    '24': de24,
    'pa': depa,
    'ga': dega,
    'hex': dehex
}

encode = {
    '1': en1,
    '2': en2,
    '3': en3,
    '4002': en4002,
    '5': en5,
    '5001': en5001,
    '6': en6,
    '7': en7,
    '8': en8,
    '9': en9,
    '10': en10,
    '11': en11,
    '12': en12,
    '13': en13,
    '14': en14,
    '16000': en16000,
    '16001': en16001,
    '24': en24,
    'ga': enga
}
# DPT: 19, 28
