---
title: CLI
summary: Simple Command Line Interface to access SmartHome.py with telnet
uid: cli
created: 2011-04-12T21:12:34+0200
changed: 2011-04-12T21:12:34+0200
type: page
category: Plugin
tags:
- Telnet
- CLI
---


Configuration
=============

plugin.conf
-----------
<pre>
['cli']
   class_name = CLI
   class_path = plugins.cli
#   ip = 127.0.0.1
#   port = 2323
#   update = False
</pre>

This plugin listen by default on 127.0.0.1 port 2323 for a telnet connection.
You could change the IP to a local address or to <code>0.0.0.0</code> to get access it over the network.
By default you could only list the values of your items. If you want to change them you have to allow updates by <code>update = True</code>.


Usage
=====

Just telnet the port: <code>telnet 127.0.0.1 2323</code> and enter <code>help</code> for a list of commands.

It would return:
<pre>ls: list all areas
ls area: list every item (with values) of the specified area
ls area.item: list the specified item and value
la: list all items (with values)
update area.item = value: update the specified item with the specified value
up: alias for update
lo: list all logics
tr logic: trigger logic
quit: quit the session
q: alias for quit</pre>

You could list <code>ls</code> items and areas or update items <code>up office.light = On</code>.
