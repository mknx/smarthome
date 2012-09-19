---
title: Logic Configuration
layout: default
summary: HowTo write and integrate logics for Smarthome.py
uid: logicconf
created: 2011-04-07T21:30:13+0200
changed: 2011-04-07T21:30:13+0200
type: page
---

# Introduction

Logic items within SmartHome.py are simple python scripts, which should be placed in <code>/usr/local/smarthome/logics/</code>.

# Basic Structure

The most important object to use is 'sh' for smarthome. It contains every detail about your smarthome. You could access your items, plugins and basic functions of SmartHome.py.
It is very important that you always access these objects with parantheses ()! Otherwise errors could accure.
To get the value of an item just call the name of it: <code>sh.area.item()</code>. And to set a new value: <code>sh.area.item(new_value)</code>.
<pre>#!/usr/bin/env python
# put on the light in the living room, if it is not on
if not sh.living_room.light():
    sh.living_room.light('on')
</pre>

You could iterate over `sh` and the item objects.
<pre>
for item in sh:
    print item
    for child_item in item:
        print child_item
</pre>

# Available Objects
Besides the 'sh' object are other important objects.

## sh.trigger()
This global function could trigger any specified logic by its name. `sh.trigger(name [, by] [, source] [, value] [, dt])`
The mandatory `name` defines which logic to trigger. With `by` you could specify a name for the calling logic. By default its set to 'Logic'.
The `source` you could name the reason for triggering and with `value` a variable.
The `dt` option is for a timezone aware datetime object which specifies the triggering time.
But watch out, if something else triggers that logic before the given datetime, it will not be triggered at the specified time! E.g. if you have set the `cycle` attribute to 60 seconds and you cant trigger after the next scheduled execution.

## logic
This object provides access to the current logic object. You could change logic attributes (crontab, cycle, ...) during runtime. They will be lost after restarting SmartHome.py.
If you want to create a endless loop please use `while logic.alive:`. This way SmartHome.py could stop the loop at shutdown.
See the next section (trigger) for a description of the special function `logic.trigger()`.
There are some predifined attributs of the logic object:

* logic.name: with the name of the logic as specified in the logic.conf
* logic.last_time(): this function provides the last run of this logic (before the actual one)
* logic.prio: read and set the current prio of this logic.

### logic.trigger()
It is equal to `sh.trigger()` except that you cannot specify name, because it will trigger the current logic. The main reason to use this function is to run the logic (again) at a specified time.

## trigger
`trigger` is a runtime enviroment for the logic which provides some information why the logic is triggerd.

It is a dictonary which could be accessed with: `trigger['by']`, `trigger['source']` and `trigger['value']`.

## logger and sh.log
You could use this object to generate log messages. It provides five different log levels: debug, info, warning, error, critical.
<code>logger.level(str) e.g. logger.info('42')</code>. The log messages are stored in the log file and the latest 50 entries in 'sh.log'.
This way you could access the messages by plugins (visu) and logics. Attention: the datetime in every log entry is the timezone aware localtime.
<pre># a simple loop over the log messages
for entry in sh.log:
    print(entry) # remark: if SmartHome.py is run in daemon mode output by 'print' is not visible.
</pre>

## sh.now and sh.utcnow
These two functions return a timezone-aware datetime object. This way you could compute with different timezones.
You could use <code>self.tz</code> and <code>self.utctz</code> to address a local and the utc timezone.

## sh.sun
This module provides access to some parameters of the sun. In order to use this module you have to specify the latitude (e.g. lat = 51.1633) and longitude (e.g. lon = 10.4476) in the smarthome.conf!
<pre># sh.sun.pos([offset]) You could specify an minute offset.
azimut, altitude = sh.sun.pos() # return the current sun position
azimut, altitude = sh.sun.pos(30) # return the sun position 30 minutes
                                  # in the future.

### sh.sun.set([offset]) You could specify an degree offset.
sunset = sh.sun.set() # Returns a utc! based datetime object with the next
                      # sunset.
sunset_tw = sh.sun.set(-6) # Would return the end of the twilight.

### sh.sun.rise([offset]) You could specify an degree offset.
sunrise = sh.sun.rise() # Returns a utc! based datetime object with the next
                        # sunrise.
sunrise_tw = sh.sun.rise(-6) # Would return the start of the twilight.
</pre>

# Loaded modules
In the logic enviroment are several python modules already loaded:

 * sys
 * os
 * time
 * datetime
 * ephem
 * random
 * Queue
 * subprocess

