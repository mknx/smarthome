---
title: CLI
layout: default
summary: Simple Command Line Interface to access SmartHome.py with telnet
created: 2011-04-12T21:12:34+0200
changed: 2011-04-12T21:12:34+0200
---

Configuration
=============

plugin.conf
-----------
<pre>
[cli]
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

Just telnet to the port: <code>telnet 127.0.0.1 2323</code> and enter <code>help</code> for a list of commands.

It would return:
<pre>ls: list the first level items
cl: clear smarthome in memory log
ls item: list item and every child item (with values)
la: list all items (with values)
lo: list all logics and next execution time
update item = value: update the specified item with the specified value
up: alias for update
tr logic: trigger logic
rl logic: reload logic
rr logic: reload and run logic
quit: quit the session
q: alias for quit
exit: alias for quit
x: alias for quit</pre>

You could list <code>ls</code> items and areas or update items <code>up office.light = On</code>.
