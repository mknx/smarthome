---
title: Russound Plugin
layout: default
summary: Plugin to control a Russound audio device with RIO over TCP.
created: 2012-10-15T21:18:27+0200
changed: 2012-10-15T21:18:27+0200
---

Requirements
============
This plugin needs a Russound audio device in the network to communicate with. The communication protocol for the ethernet port has to be set to RIO.

Configuration
=============

plugin.conf
-----------
<pre>
[russound]
   class_name = Russound
   class_path = plugins.russound
   host = 192.168.1.123
#   port = 9621
</pre>

This plugin talks by default with the Russound audio device with the given host ip on the default port 9621. If you have changed the default port you have to change it here as well.

items.conf
--------------

### rus_path
This attribute is mandatory. If you don't provide one the item will be ignored.
The value must be given with the following format c.z.p where c is the number of the controller, z is the number of the zone and p is the system parameter of the Russound audio device like volume or treble.
Right know the following russound parameter types are supported:

* status = zone On/Off: type must be bool
* volume = volume of the zone: type must be num [0..255]
* bass = bass of the zone: type must be num [-128..127]
* treble = treble of the zone: type must be num [-128..127]
* balance = balance of the zone: type must be num [-128..127]
* turnonvolume = volume on zone on: type must be num [0..255]
* source = number of the source: type must be num
* mute = mute the zone volume: type must be bool
* loudness = loudness of the zone: type must be bool
* partymode = party mode setting of the zone: type must be string [ON/OFF/MASTER]
* donotdisturb = do not disturb setting of the zone: type must be string

# Example
<pre>
['dg']
        [['bedroom']]
                [[['audio']]]
                        type=bool
                        rus_path=1.1.status

                        [[[['volume']]]]
                                type=num
                                rus_path=1.1.volume
                        [[[['bass']]]]
                                type=num
                                rus_path=1.1.bass
                        [[[['treble']]]]
                                type=num
                                rus_path=1.1.treble
                        [[[['balance']]]]
                                type=num
                                rus_path=1.1.balance
                        [[[['turnonvolume']]]]
                                type=num
                                rus_path=1.1.turnonvolume
                        [[[['source']]]]
                                type=num
                                rus_path=1.1.currentsource
                        [[[['mute']]]]
                                type=bool
                                rus_path=1.1.mute
                        [[[['loudness']]]]
                                type=bool
                                rus_path=1.1.loudness
                        [[[['partymode']]]]
                                type=str
                                rus_path=1.1.partymode
                        [[[['donotdisturb']]]]
                                type=str
                                rus_path=1.1.donotdisturb
</pre>

