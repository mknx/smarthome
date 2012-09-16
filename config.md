---
title: Configuration
summary: Basic configuration of SmartHome.py
uid: config
created: 2011-04-07T21:36:23+0200
changed: 2011-04-07T21:36:23+0200
type: page
category: Configuration
---


smarthome.conf
==============
A very simple smarthome.conf looks like this:
<pre># /usr/local/smarthome/etc/smarthome.conf

['living_room'] # Area
    [['temperature']] # Item
        type = num # Attribute

    [['light']] # Item
        type = bool # Attribute
</pre>

Areas and Items
===============
The basic structure of the configuration is based on two elements: areas and items.
An area could group serveral items to build a tree structure of your smarthome.
Wheras items could have several attributes which specifies the characteristics of the item.
Valid characters for the name of the area or item are: a-z, A-Z and '_'!

Item Attributes
---------------
 * `type`: this is the only mandatory attribute for an item. You could choose between:
   * bool: you could init this type with on, 1, True or off, 0, False. It will be set to True or False internally. So you could use `if sh.area.item: ...`.
   * num: it could be any number (integer or float).
   * str: well a string or unicode string.
   * list: a list/array of values. Usefull for some KNX dpts.
   * foo: this type is for generic purposes. No validation is done.
 * `value`: this is the initial value of that item.
 * `name`: you could specify a name wich would be the str reprensentation of the item.
 * `cache`: if set to On, the value of the item will be cached in a local file (in /usr/local/smarthome/var/cache/).
 * `enforce_updates`: If set to On, every call of the item will trigger depending logics.
 * `threshold`: specify values to trigger depending logics only if the value transit the threshold. low:high to set a value for the lower and upper threshold, e.g. 21.4:25.0 which triggers the logic if the value exceeds 25.0 or fall below 21.4. Or simply a single value.
 * `offset` (only for num-types): the offset will be evaluated every time you try to update the value of the item. It could be a simple '+2' or a more complex '*3.0/2+3'.
 * `area`: Area object of the item. e.g. sh.living.light.area == sh.living

The following attributes are constantly updated by SmartHome.py:

 * `last_change`: a datetime object with the latest update time
 * `changed_by`: caller of the latest update
 * `prev_change`: age in seconds of the change before the latest update

### fade()
This function fades the item to a specified value with the defined stepping (int or float) and timedelta (int or float in seconds).
e.g. <code>sh.living.light.fade(100, 1, 2.5)</code> will in- or decrement the living room light to 100 by a stepping of '1' and a timedelta of '2.5' seconds.


SmartHome.py Attributes
=======================
There are the following attributes for SmartHome.py:

 * `lat`, `lon`, `elev`: specifies the geographic coordinates of your home (latitude, longitude, elevation). The lat and lon are neccesary if you want to reference the sunrise/sunset or the sun position. See the description at the [Logic](/logic/config/) page.
 * `tz`: describes the timezone

Sample Configuration
====================
<pre># /usr/local/smarthome/etc/smarthome.conf

lat = 51.1633
lon = 10.4476
elev = 500

tz = 'Europe/Berlin'

['living_room']
    [['temperature']]
        type = num
        name = Living room temperature

    [['target-temperature']]
        type = num
        cache = On

    [['light']]
        type = bool
        cache = On

['entrance']
    [['camera']]
        type = str
        value = http://camera.locale/
    [['door']]
        type = bool

</pre>

Plugin and Logic Configuration
==============================
There are dedicated configuration pages for [plugins](/plugins/config/) and [logics](/logic/config/).

