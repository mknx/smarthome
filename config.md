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


## etc/smarthome.conf [optional]

Following attributes are supportet in smarthome.conf:

 * `lat`, `lon`, `elev`: geographic coordinates of your home (latitude, longitude, elevation). lat and lon are neccesary for sunrise/sunset calculation, dealing with the position of the sun.
 * `tz`: used timezone

### Sample Configuration

<pre># /usr/local/smarthome/etc/smarthome.conf

lat = 51.1633
lon = 10.4476
elev = 500

tz = 'Europe/Berlin'
</pre>


## etc/logic.conf [mandatory]

It is possible to use a blank file (touch logic.conf) for the first steps.

Logic items within SmartHome.py are simple python scripts, which are placed in <code>/usr/local/smarthome/logics/</code>. See the [logic introduction](/smarthome/logic) for howto write logics.

An example of a very simple logic.conf:
<pre># /usr/local/smarthome/etc/logic.conf
[MyLogic]
    filename = logic.py
    crontab = init</pre>

SmartHome.py would look in <code>/usr/local/smarthome/logics/</code> for the file <code>logic.py</code>. The logic would be started - once - when the system starts.

Following attributes are supportet controll the behavior of the logics:

### watch_item
The comma-separated list of items will be monitored for changes. 
<pre>watch_item = house.door, terrace.door</pre>
Every change of these two items triggers (run) the logic.

### cycle
Defines the time interval for repeating the logic (in seconds).
<pre>cycle = 60</pre>
Special use:
<pre>cycle = 15 = 42</pre>
Calls the logic with <code>trigger['value'] # == '42'</code>


### crontab
like unix crontab with following options:

<code>crontab = init</code>
Run the logic during the start of SmartHome.py.

<code>crontab = minute hour day wday</code>

 *  minute: single value from 0 to 59, or comma separated list, or * (every minute)
 *  hour: single value from 0 to 23, or comma separated list, or * (every hour)
 *  day: single value from 0 to 28, or comma separated list, or * (every day)
    Please note: dont use days greater than 28 in the moment.
 *  wday: weekday, single value from 0 to 6 (0 = Monday), or comma separated list, or * (every day)

<code>crontab = sunrise</code>
Runs the logic at every sunrise. Use `sunset` to run at sunset. 
For sunset / sonrise You could provide:

   * an horizon offset in degrees e.g. <code>crontab = sunset-6</code> You have to specify your latitude/longitued in smarthome.conf.
   * an offset in minutes specified by a 'm' e.g. <code>crontab = sunset-10m</code>
   * a boundry for the execution <pre>crontab = 17:00&lt;sunset  # sunset, but not bevor 17:00 (locale time)
crontab = sunset&lt;20:00  # sunset, but not after 20:00 (locale time)
crontab = 17:00&lt;sunset&lt;20:00  # sunset, beetween 17:00 and 20:00</pre>

<code>crontab = 15 * * * = 50</code>
Calls the logic with <code>trigger['value'] # == 50</code>

Combine several options with '\|':
<pre>crontab = init = 'start' | sunrise-2 | 0 5 * *</pre>

### prio
Priority of the logic used by the internal scheduling table. By default every logic has the the priority of '3'. You could assign [0-10] as a value.
You could change it to '1' to prefer or to '4' to penalise the logic in comparison to other logics. 

### Other attributes
Other attributes could be accessed from the the logic with <code>self.attribute_name</code>.

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


## etc/plugin.conf (mandatory)
It is possible to use a blank file (touch plugin.conf) for the first steps.

Plugins extend the core functionality of SmartHome.py. You could access these plugins from every logic script.
For example there is a plugin for the prowl notification service to send small push messages to your iPhone/iPad.
Plugins are placed in <code>/usr/local/smarthome/plugins/</code>.

### Configuration
Plugins are configured in the plugin.conf file. A simple plugin.conf:

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


## items/*.conf (optional)

Items could be specified in one or several conf files placed in the `items` directory of SmartHome.py
Valid characters for the item name are: a-z, A-Z and '_'!

A simple item configuration:
<pre># /usr/local/smarthome/items/living.conf
[living_room_temp]
    type = num
</pre>

Use nested items to build a tree representing your enviroment.
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

 * `type`: for storing values and/or triggering actions you have to specify this attribute. (If you do not specify this attribute the item is only usefull for structuring your item tree). Supported types:
   * bool: boolean type (on, 1, True or off, 0, False). True or False are internally used. Use e.g.  `if sh.item(): ...`.
   * num: any number (integer or float).
   * str: regular string or unicode string.
   * list: list/array of values. Usefull e.g. for some KNX dpts.
   * dict: python dictionary for generic purposes.
   * foo: pecial purposes. No validation is done.
   * scene: special keyword to support scenes
 * `value`: initial value of that item.
 * `name`: name which would be the str representation of the item (optional).
 * `cache`: if set to On, the value of the item will be cached in a local file (in /usr/local/smarthome/var/cache/).
 * `enforce_updates`: If set to On, every call of the item will trigger depending logics and item evaluations.
 * `threshold`: specify values to trigger depending logics only if the value transit the threshold. low:high to set a value for the lower and upper threshold, e.g. 21.4:25.0 which triggers the logic if the value exceeds 25.0 or fall below 21.4. Or simply a single value.
 * `eval` and `eval_trigger`: see next section for a description of these attributes.
 * `crontab` and `cycle`: see logic.conf for possible options to set the value of an item at the specified times / cycles.

#### Scenes
For using scenes a config file into the scenes directory for every 'scene item' is neccessary. The scene config file consists of space separated lines with the <code>ItemValue ItemPath|LogicName Value</code>.

<pre># items/example.conf
[example]
    type = scene
[otheritem]
    type = num
</pre>

<pre># scenes/example.conf
0 otheritem 2
1 otheritem 20
1 LogicName run
2 otheritem 55
3 LogicName stop
</pre>


#### eval
This attribute is usefull for small evaluations and corrections. The input value is accesible with `value`.
<pre>
# items/level.conf
[level]
    type = num
    eval = value * 2 - 1  # if you call sh.level(3) sh.level will be evaluated and set to 5
</pre>

Trigger the evaluation of an item with `eval_trigger`:
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

Eval keywords to use with the eval_trigger:

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
Every item provides provides item functions.

#### id()
Returns the item id (path).

#### return_parent()
Returns the parent item. `sh.item.return_parent()`

#### return_children()
Returns the children of an item. `for child in sh.item.return_children(): ...`

#### age()
Returns the age of the current item value.

#### last_change()
Returns an datetime object with the latest update time.

#### changed_by()
Returns the caller of the latest update.

#### prev_change()
Returns the age in seconds of the change before the latest update.

#### fade()
Fades the item to a specified value with the defined stepping (int or float) and timedelta (int or float in seconds).
e.g. <code>sh.living.light.fade(100, 1, 2.5)</code> will in- or decrement the living room light to 100 by a stepping of '1' and a timedelta of '2.5' seconds.

