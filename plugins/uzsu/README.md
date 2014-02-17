# UZSU
Provides universial time switches for items.

# Requirements
Calculating of sunset/sunrise in triggers, requires installation of ephem.

# Configuration

## plugin.conf
Please provide a plugin.conf snippet for your plugin with ever option your plugin supports. Optional attributes should be commented out.

<pre>
[uzsu]
   class_name = UZSU
   class_path = plugins.uzsu
</pre>

## items.conf

### uzsu
You can enable the univerial time switching capabilities for each item by setting the uzsu attribute to True.

<pre>
# items/my.conf

[someroom]
    [[someitem]]
        type = int
        uzsu = True
</pre>

# Methodes

## get(item)
Retrieve all switching entries for the specified item as a list of dictionaries.

## add(item, dt, value, active=True, time=None, rrule=None)
Add a new switching entry for the given item.
Parameter description:

* __item__: the item object.

* __dt__: a datetime object. With time = None and rrule = None this is the exact date and time when the item will be set to the specified value once.

* __value__: the value which will be set to the item.

* __active__: `True` if the entry is activated, `False` if not. A deactivated entry is stored to the database but doesn't trigger the setting of the value. It can be enabled later with the `update` method.

* __time__: optional time as string to use sunrise/sunset arithmetics like in the crontab eg. `17:00<sunset`, `sunrise>8:00`, `17:00<sunset`. You also can set the time with `17:00`. This string, if given, will overwrite the time from the `dt` parameter.

* __rrule__: You can use the recurrence rules documented in the [iCalendar RFC](http://www.ietf.org/rfc/rfc2445.txt) for recurrence use of a switching entry.

`sh.uzsu.add(sh.item1, datetime.datetime.now() + datetime.timedelta(minutes=2), '1')` would set the item1 to 1 in 2 minutes.
`sh.uzsu.add(sh.item1, datetime.datetime.now() + datetime.timedelta(minutes=2), '1', True, rrule='FREQ=MINUTELY;INTERVAL=2;COUNT=5')` would set item1 to 1 every to minutes, starting in 2 minutes and exactly 5 times.
`sh.uzsu.add(sh.item1, datetime.datetime.now() + datetime.timedelta(minutes=2), '0', True, '17:00<sunset<18:30', rrule='FREQ=DAILY;INTERVAL=2;COUNT=5')` would set the item1 to 0 every other day at sunset between 17:00 and 18:00 o'clock for 5 times.

## update(item, id, dt=None, value=None, active=None, time=None, rrule=None)
This method updates every given parameter for an existing entry. See the `add` method for a description of each parameter.

`sh.uzsu.update(sh.item1, 1, active=False)` would deactive the entry with ID 1 for item1.

## remove(item, id)
This method removes an entry from an item.

`sh.uzsu.remove(sh.item1, 1)` would remove the entry with ID 1 from item1.

