---
title: rrdtool Plugin
summary: Plugin to build round robin databases and create graphs
uid: rrdplugin
created: 2011-04-12T21:12:34+0200
changed: 2011-12-29T21:12:34+0200
type: page
category: Plugin
tags:
- Plugin
- rrdtool
- rrd
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
['rrd']
    class_name = RRD
    class_path = plugins.rrd
    # rrd_style = --color, 'ARROW#00000000', --color, 'FRAME#00000000', --color, 'BACK#00000000', --slope-mode
    # rrd_dir = /usr/local/smarthome/var/rrd/
    # rrd_png = /var/www/visu/rrd/
    # rrd_web = /rrd/
</pre>

`rrd_style` is a list of graph style options. See man rrdgraph for creating your own style.
`rrd_dir` specify the rrd storage location. `rrd_png` location for the png graphs. `rrd_web` is used for the relative path name used in the img tag.

smarthome.conf
--------------

### rrd
To active rrd logging (for an item) simply set this attribute to yes.

### rrd_min
Set this item attribute to log the minimum as well.

### rrd_max
Set this item attribute to log the maximum as well.

### rrd_graph
If this attribute ist set to 'yes' a graph for this item would be created.
With `rrd_opt` you could specify item specific graph style options.


<pre>
['outside']
    name = Outside
    [['temperature']]
        name = Temp
        type = num
        rrd = 1
        rrd_min = 1
        rrd_max = 1
        rrd_graph = 1

['office']
    name = 'Büro'
    rrd_graph = office.temperature, office.humidity
    rrd_opt = '--right-axis', '4:-50', '--right-axis-label', '%', '--rigid', '--lower-limit', '20', '--upper-limit', '26', 'CDEF:hum=humidity,4,/,12,+', 'LINE1:temperature#FF0000:Temperatur', 'LINE1:hum#0000FF:Luftfeuchte'
    [['temperature']]
        name = Temperatur
        type = num
        rrd = 1
    [['humidity']]
        name = Luftfeuchtigkeit
        type = num
        rrd = 1
</pre>

Functions
=========

generate_graphs(timeframe)
--------------------------


