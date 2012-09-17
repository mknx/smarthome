---
title: Configuration
layout: default
summary: Configuration of SmartHome.py
created: 2011-04-07T21:36:23+0200
changed: 2011-04-07T21:36:23+0200
category: Configuration
---

# Configuration

The configuration of SmartHome.py is split up in four areas:
 * Basic Configuration: smarthome.conf
 * Logic Configuration: logic.conf
 * Plugin Configuration: plugin.conf
 * Nodes Configuration: nodes


## smarthome.conf

There are the following attributes for SmartHome.py:

 * `lat`, `lon`, `elev`: specifies the geographic coordinates of your home (latitude, longitude, elevation). The lat and lon are neccesary if you want to reference the sunrise/sunset or the sun position. See the description at the [Logic](/logic/config/) page.
 * `tz`: describes the timezone

### Sample Configuration

<pre># /usr/local/smarthome/etc/smarthome.conf

lat = 51.1633
lon = 10.4476
elev = 500

tz = 'Europe/Berlin'
</pre>


## logic.conf

Logic items within SmartHome.py are simple python scripts, which are placed in <code>/usr/local/smarthome/logics/</code>. See XXX for howto write logics.

A very simple logic.conf would look like this:
<pre># /usr/local/smarthome/etc/logic.conf
[MyLogic]
    filename = logic.py
    crontab = init</pre>
SmartHome.py would look in <code>/usr/local/smarthome/logics/</code> for the file <code>logic.py</code>. The logic would be started - once - when the system starts.

There are several special attributes to controll the behavior of the logics:

### watch_node
Specify nodes as a single node path or as a comma-separated list to monitor for changes.
<pre>watch_item = house.door, terrace.door</pre>
Every change of these two items would trigger (run) the logic.

### cycle
The logic will be repeated every specified seconds.
<pre>cycle = 60</pre>

### crontab
A crontab like attribute, with the following options:

<pre>crontab = init</pre>
Run the logic during the start of SmartHome.py.

<pre>crontab = minute hour day wday</pre>
 *  minute: single value from 0 to 59, or comma separated list, or * (every minute)
 *  hour: single value from 0 to 23, or comma separated list, or * (every hour)
 *  day: single value from 0 to 28!, or comma separated list, or * (every day)
    Please note: you cannot use days greater than 28. Sorry
 *  wday: single value from 0 to 6 (0 = Monday), or comma separated list, or * (every day)

<pre>crontab = sunrise</pre>
Runs the logic at every sunrise. Or specify `sunset` to run at sunset. Furthermore you could provide an horizon offset in degrees e.g. <code>crontab = sunset-6</code>.
For this option you have to specify your latitude/longitued in smarthome.conf.

You could combine several options with '\|':
<pre>crontab = init | sunrise-2 | 0 5 * *</pre>

### prio
This attribute provides access the internal scheduling table. By default every logic has the the prio of '3'. You could assign [0-10] as a value.
You could change it to '1' to prefer or to '4' to penalise the logic in comparison to other logics. 

### Other attributes
Every other attribute could be accessed from the the logic with <code>self.attribute_name</code>.

### Sample logic.conf
<pre># /usr/local/smarthome/etc/logic.conf
[Time]
    filename = time.py
    cyle = 60

[DoorBell]
    filename = bell.py
    watch_item = dorr.bell # monitor for changes

[Blind Living]
    filename = blind.py
    crontab = 10,25,40,55 * * * # run every 15 minutes
    # cycle = 900 # could be used instead
    sunshine = no # accessed by self.sunshine

[BlindKitchen]
    filename = blind.py  # you could run the same logic file several times
    crontab = 10,25,40,55 * * * # run every 15 minutes
    sunshine = yes
</pre>


## Plugins
XXX
