---
title: 1-Wire Plugin
summary: Plugin to monitor sensor information on a 1-Wire bus
uid: onewire
created: 2011-04-08T20:59:34+0200
changed: 2011-04-08T20:59:34+0200
type: page
category: Plugin
tags:
- Plugin
- 1-Wire
---

Requirements
============
This plugin needs an running owserver from owfs. I've tested owfs-2.7p34 and owfs-2.8p15.

Hint: to run the owserver as non root. You have to add a udev rule for the usb busmasters.
<pre># /etc/udev/rules.d/80-smarthome.rules
SUBSYSTEM=="usb",ENV{DEVTYPE}=="usb_device",ATTR{idVendor}=="04fa", ATTR{idProduct}=="2490",GROUP="smarthome",MODE="0660"
</pre>

Configuration
=============

plugin.conf
-----------
<pre>
['ow']
    class_name = OneWire
    class_path = plugins.onewire
#    host = 127.0.0.1
#    port = 4304
</pre>

This plugins is looking by default for the owserver on 127.0.0.1 port 4304. You could change this in your plugin.conf.

smarthome.conf
--------------

### ow_id
If you specify an 'ow_id' attribute to an item the 1-Wire plugin will monitor this sensor.

### ow_sensor
'ow_sensor' defines which sensor information do you want to read from the sensor. The most common is 'temperature' and 'humidity'.

#### ibutton and ibutton_master
The 'ibutton' and the 'ibutton_master' are special keywords for 'ow_sensor'.
If you specify an 'ibutton_master' the 1-Wire plugin will monitor this bus with a high frequency (2/s) for changes.
They 'ibutton' sensor returns 'True' if the ibutton is present or 'False' if not.

<pre>['office']
    [['temperature']]
        type = num
        ow_id = 28.BBBBB20000
        ow_sensor = temperature

    [['humidity']]
        type = num
        ow_id = 26.CCCCCC00000
        ow_sensor = humidity

['home']
    [['key_hanger']]
        type = bool
        ow_id = 81.FFFFFFF0000
        ow_sensor = ibutton_master # busmaster for the key hanger

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

See the [logic key hanger](/logic/key_hanger) for an example.

Functions
=========

ibutton_hook(ibutton, item)
--------------------------------

This is a special function which is called if an unknown ibutton is attached to the bus.
If the unknown ibutton is already seen, the id will be cached and the function is not called again. The cache will be reset every ten minutes.
The function must take two arguments. The first will be the id of the ibutton and the second is the item of the ibutton busmaster (e.g. `sh.home.key_hanger`).

To use it you have to assign a (useful) function. For this you could do something like this:

<pre># my startup.py logic which is called at startup with crontab = init
def intruder_alert(ibutton_id, item):
    sh.notify("iButton-Alert","Someone uses an unknown iButton ({0}) at {1}".format(ibutton_id, item))
    # sh.take_picuture()
    # ...

sh.ow.ibutton_hook = intruder_alert</pre>

