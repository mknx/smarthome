---
title: KNX Plugin
layout: default
summary: Plugin to communicate with the KNX bus.
---

Requirements
============
This plugin needs a running eibd.

Installing eibd
---------------
I'm using the vanilla eibd from Martins repository.
<pre>$ sudo add-apt-repository ppa:mkoegler/bcusdk
$ sudo apt-get install eibd-clients eibd-server libeibclient-dev</pre>

Configuration
=============

plugin.conf
-----------
<pre>
[knx]
   class_name = KNX
   class_path = plugins.knx
#   host = 127.0.0.1
#   port = 6720
   send_time = 600 # update date/time every 600 seconds, default none
   time_ga = 1/1/1 # default none
   date_ga = 1/1/2 # default none
#   busmonitor = False
</pre>

This plugins is looking by default for the eibd on 127.0.0.1 port 6720. You could change this in your plugin.conf.
If you specify a `send_time` intervall and a `time_ga` and/or `date_ga` the plugin sends the time/date every cycle seconds on the bus.

If you set `busmonitor` to True, every KNX packet will be logged.

items.conf
--------------

### knx_dpt
This attribute is mandatory. If you don't provide one the item will be ignored.
Right know the following datapoint types are supported:

* 1 = 1.x: type must be bool
* 2 = 2.x: type must be foo
* 3 = 3.x: type must be foo
* 4002 = 4.002: type must be str
* 5 = 5.x: type must be num
* 5001 = 5.001: type must be num
* 6 = 6.x: type must be num
* 7 = 7.x: type must be num
* 8 = 8.x: type must be num
* 9 = 9.x: type must be num
* 10 = 10.x: type must be foo # datetime.time
* 11 = 11.x: type must be foo # datetime.date
* 12 = 12.x: type must be num
* 13 = 13.x: type must be num
* 14 = 14.x: type must be num
* 16000 = 16.000: type must be str
* 16001 = 16.001: type must be str
* 17 = 17.x: type must be num
* 20 = 20.x: type must be num
* 24 = 24.x: type must be str

If you are missing one, open a bug report or drop me a message in the knx user forum.

### knx_send
You could specify one or more group addresses to send updates to. Item update will only be sent if the item is not changed via KNX.

### knx_status
Similar to knx_send but will send updates even for changes vie KNX if the knx_status GA differs from the destination GA.

### knx_listen
You could specify one or more group addresses to monitor for changes.

### knx_init
If you set this attribute, SmartHome.py sends a read request to specified group address at startup and set the value of the item to the response.
It implies 'knx_listen'.

### knx_cache
If you set this attribute, SmartHome.py tries to read the cached value for the group address. If it fails it sends a read request to specified group address at startup and set the value of the item to the response.
It implies 'knx_listen'.

### knx_reply
Specify one or more group addresses to allow reading the item value.

# Example
<pre>
['living_room']
    [['light']]
        type = bool
        knx_dpt = 1
        knx_send = 1/1/3
        knx_listen = 1/1/4, 1/1/5
        knx_init = 1/1/4

    [['temperature']]
        type = num
        knx_dpt = 9
        knx_send = 1/1/6
        knx_reply = 1/1/6
        ow_id = 28.BBBBB20000 # see 1-Wire plugin
        ow_sensor = temperature # see 1-Wire plugin
</pre>

logic.conf
----------
You could specify the `knx_listen` and `knx_reply` attribute to every logic in your logic.conf. The argument could be a single group address and dpt or a list of them.
<pre>
['logic1']
    knx_dpt = 9
    knx_listen = 1/1/7

['logic2']
    knx_dpt = 9
    knx_reply = 1/1/8, 1/1/8
</pre>
If there is a packet directed to the according group address, SmartHome.py would trigger the logic and will pass the payload (via the trigger object) to the logic.

In the context of the KNX plugin the trigger dictionary consists of the following elements:

* trigger['by']     protocol ('KNX')
* trigger['source']     PA (physical adress of the KNX packet source) 
* trigger['value']     payload

Functions
=========

encode(data, dpt)
-----------------
This function encodes your data according to the specified datapoint.
<pre>data = sh.knx.encode(data, 9)</pre>

groupwrite(ga, data, dpt)
-------------------------
With this function you could send the data to the specified group address.
<pre>sh.knx.groupwrite('1/1/10', 10.3, '9')</pre>

groupread(ga, cache=False)
--------------------------
This function triggers a read request on the specified group address. It doesn't return the received value!

send_time(time_ga, date_ga)
-----------------------------
This funcion send the current time and or date to the specified group address.
<pre>sh.knx.send_time('1/1/1', '1/1/2') # send the time to 1/1/1 and the date to 1/1/2
sh.knx.send_time('1/1/1') # only send the time to 1/1/1
sh.knx.send_time(data_ga='1/1/2') # only send the date to 1/1/2
</pre>
Hint: instead of this function you could use the plugin attribute 'send_time' as described above.
