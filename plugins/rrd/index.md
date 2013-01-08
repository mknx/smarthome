---
title: rrdtool Plugin
summary: Plugin to build round robin databases and create graphs
uid: rrdplugin
layout: default
created: 2011-04-12T21:12:34+0200
changed: 2011-12-29T21:12:34+0200
---

Requirements
============
You have to install the python bindings for rrdtool:
<pre>$ sudo apt-get install python-rrdtool</pre>

Configuration
=============

plugin.conf
-----------
<pre>
[rrd]
    class_name = RRD
    class_path = plugins.rrd
    # step = 300
    # rrd_dir = /usr/local/smarthome/var/rrd/
</pre>

`step` sets the cycle time how often entries will be updated.
`rrd_dir` specify the rrd storage location.

items.conf
--------------

### rrd
To active rrd logging (for an item) simply set this attribute to yes.

### rrd_min
Set this item attribute to log the minimum as well. Default is no.

### rrd_max
Set this item attribute to log the maximum as well. Default is no.

<pre>
[outside]
    name = Outside
    [[temperature]]
        name = Temperatur
        type = num
        rrd = 1
        rrd_min = 1
        rrd_max = 1

[office]
    name = Büro
    [[temperature]]
        name = Temperatur
        type = num
        rrd = 1
</pre>

# Functions
This plugin adds two item! functions to every item which has rrd enabled.

## sh.item.average(frame)
Return the average for the specified time frame. See the rrdtool documentation for supported time frames.
e.g. `sh.office.temperature.average('1h')` return the average of the last hour

## sh.item.export(frame)
Export/dumps the rrd database for the time frame.
