---
title: Key Hanger
summary: This logic monitors the key_hanger.
uid: key_hanger
created: 2011-04-08T22:03:01+0200
changed: 2011-04-08T22:03:01+0200
type: page
category: Logic
tags:
- iButton
- Logic
---

Configuration
=============

I assume the following configuration:

<pre># /usr/local/smarthome/etc/smarthome.conf
['home']

    [['key_hanger']]
        type = bool
        ow_id = 81.FFFFFFF0000
        ow_sensor = ibutton_master # busmaster for the key hanger

    [['lights']]
        type = bool
        knx_ga = 1/1/3
        knx_dpt = 1


['residents']

    [['John']]
        type = bool
        ow_id = 01.AAAAAA30000
        ow_sensor = ibutton

    [['Jane']]
        type = bool
        ow_id = 01.BBBBA30000
        ow_sensor = ibutton
</pre>

<pre># /usr/local/smarthome/etc/logic.conf
['Key Hanger']
    filename = 'key_hanger.py'
    watch_item = residents.John, residents.Jane
</pre>

Logic
=====
<pre># /usr/local/smarthome/logic/key_hanger.py

presence = False

for resident in sh.residents:
    if resident:
        presence = True

sh.home.key_hanger(presence)

if not presence:
    sh.home.lights('off')
</pre>
