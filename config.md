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

 * Basic Configuration: etc/smarthome.conf
 * Logic Configuration: etc/logic.conf
 * Plugin Configuration: etc/plugin.conf
 * Item Configuration: items/*.conf


## etc/smarthome.conf

There are the following attributes for SmartHome.py:

 * `lat`, `lon`, `elev`: specifies the geographic coordinates of your home (latitude, longitude, elevation). The lat and lon are neccesary if you want to reference the sunrise/sunset or the sun position.
 * `tz`: describes the timezone

### Sample Configuration

<pre># /usr/local/smarthome/etc/smarthome.conf

lat = 51.1633
lon = 10.4476
elev = 500

tz = 'Europe/Berlin'
</pre>


## etc/logic.conf

This file is mandatory. For first experiments, it is possible to use a blanc file (touch logic.conf).

Logic items within SmartHome.py are simple python scripts, which are placed in <code>/usr/local/smarthome/logics/</code>. See the [logic introduction](/smarthome/logic) for howto write logics.

A very simple logic.conf would look like this:
<pre># /usr/local/smarthome/etc/logic.conf
[MyLogic]
    filename = logic.py
    crontab = init</pre>
SmartHome.py would look in <code>/usr/local/smarthome/logics/</code> for the file <code>logic.py</code>. The logic would be started - once - when the system starts.

There are several special attributes to controll the behavior of the logics:

### watch_item
Specify items as a single item path or as a comma-separated list to monitor for changes.
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


## etc/plugin.conf
This file is mandatory. For first experiments, it is possible to use a blanc file (touch plugin.conf).

Plugins extend the core functionality of SmartHome.py. You could access these plugins from every logic script.
For example there is a plugin for the prowl notification service to send small push messages to your iPhone/iPad.
Plugins are placed in <code>/usr/local/smarthome/plugins/</code>.

### Configuration
Plugins are configured in the plugin.conf file. A simple one looks like this:

<pre># /usr/local/smarthome/etc/plugin.conf
[notify] # object instance name e.g. sh.notify
    class_name = Prowl # class name of the python class
    class_path = plugins.prowl # path to the plugin
    apikey = abc123abc123 # attribute for the plugin e.g. secret key for prowl
</pre>

The object name, class name and class path must be provided.
The other attributes depend on the individual plugin. See the corrosponding plugin page for more information.

The example above would generate the following statement `sh.notify = plugins.prowl.Prowl(apikey='abc123abc123')`.
From now on there is the object `sh.notify` and you could access the function of this object with `sh.notify.function()`.


## items/*.conf

Items could be specified in one or several conf files placed in the `items` directory of SmartHome.py
Valid characters for the item name are: a-z, A-Z and '_'!

A simple item configuration looks like this:
<pre># /usr/local/smarthome/items/living.conf
[living_room_temp]
    type = num
</pre>

You could nest items to build a tree representing your enviroment.
<pre># /usr/local/smarthome/items/living.conf
[living_room]
    [[temperature]]
        type = num

    [[tv]]
        type = bool

        [[[channel]]]
            type = num
</pre>

### Item Attributes

 * `type`: if you want to use an item for storing values and/or triggering actions you have to specify this attribute. If you do not specify this attribute the item is only usefull for structuring your item tree. You could choose between:
   * bool: you could init this type with on, 1, True or off, 0, False. It will be set to True or False internally. So you could use `if sh.item(): ...`.
   * num: it could be any number (integer or float).
   * str: well a regular string or unicode string.
   * list: a list/array of values. Usefull for some KNX dpts.
   * dict: a python dictionary for generic purposes.
   * foo: this type is for special purposes. No validation is done.
 * `value`: this is the initial value of that item.
 * `name`: you could specify a name which would be the str representation of the item.
 * `cache`: if set to On, the value of the item will be cached in a local file (in /usr/local/smarthome/var/cache/).
 * `enforce_updates`: If set to On, every call of the item will trigger depending logics and item evaluations.
 * `threshold`: specify values to trigger depending logics only if the value transit the threshold. low:high to set a value for the lower and upper threshold, e.g. 21.4:25.0 which triggers the logic if the value exceeds 25.0 or fall below 21.4. Or simply a single value.
 * `offset` (only for num-types): the offset will be evaluated every time you try to update the value of the item. It could be a simple '+2' or a more complex '*3.0/2+3'.
 * `eval` and `eval_trigger`: see the next section for the description of these attributes.

#### eval
The eval attribute is usefull for small evaluations and corrections. The input value is accesible with `value`.
<pre>
# items/level.conf
[level]
    type = num
    eval = value * 2 - 1  # if you call sh.level(3) sh.level will be evaluated and set to 5
</pre>

You could trigger the evaluation of an item with `eval_trigger`:
<pre>
# items/room.conf
[room]
    [[temp]]
        type = num
    [[hum]]
        type = num
    [[dew]]
        type = num
        eval = sh.tools.dewpoint(sh.room.temp(), sh.room.hum())
        eval_trigger = room.temp, room.hum  # every change of temp or hum would trigger the evaluation of dew.
</pre>

There are several eval keywords to use with the eval_trigger:

   * sum: compute the sum of all specified eval_trigger items.
   * avg: compute the average of all specified eval_trigger items.
   * and: set the item to True if all of the specified eval_trigger items are True.
   * or:  set the item to True if one of the specified eval_trigger items is True.

<pre>
# items/rooms.conf
[room_a]
    [[temp]]
        type = num
    [[presence]]
        type = bool
[room_b]
    [[temp]]
        type = num
    [[presence]]
        type = bool
[rooms]
    [[temp]]
        type = num
        name = average temperature
        eval = avg
        eval_trigger = room_a.temp, room_b.temp
    [[presence]]
        type = bool
        name = movement in on the rooms
        eval = or
        eval_trigger = room_a.presence, room_b.presence
</pre>


### Item Functions
There are several item functions which every item provides.

#### id()
Returns the item id (path).

#### return_parent()
Returns the parent item. `sh.item.return_parent()`

#### return_children()
Returns the children of an item. `for child in sh.item.return_children(): ...`

#### last_change()
Returns an datetime object with the latest update time.

#### changed_by()
Return the caller of the latest update.

#### prev_change()
return the age in seconds of the change before the latest update.

#### fade()
This function fades the item to a specified value with the defined stepping (int or float) and timedelta (int or float in seconds).
e.g. <code>sh.living.light.fade(100, 1, 2.5)</code> will in- or decrement the living room light to 100 by a stepping of '1' and a timedelta of '2.5' seconds.

