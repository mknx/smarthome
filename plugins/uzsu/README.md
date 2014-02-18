# UZSU
Provides universial time switches for items.

# Requirements
Calculating of sunset/sunrise in triggers, requires installation of ephem.

# Configuration

## plugin.conf

<pre>
[uzsu]
   class_name = UZSU
   class_path = plugins.uzsu
</pre>

## items.conf

### uzsu
You have to specify a item with `type = list` and with the `uzsu_item` attribute set to the path of the item which will be set by this item.

<pre>
# items/my.conf

[someroom]
    [[someitem]]
        type = int
        [[[anotheritem]]]
            type = list
            uzsu_item = someroom.someitem
            cache = True
</pre>

If you specify the `cache = True` as well, then you're switching entries will be there even if you restart smarthome.py.

# Item Data Format

Each UZSU item is of type list. Each list entry has to be a dict with specific key and value pairs. Here are the possible keys and what their for:

* __dt__: a datetime object. With time = None and rrule = None this is the exact date and time when the item will be set to the specified value once.

* __value__: the value which will be set to the item.

* __active__: `True` if the entry is activated, `False` if not. A deactivated entry is stored to the database but doesn't trigger the setting of the value. It can be enabled later with the `update` method.

* __time__: optional time as string to use sunrise/sunset arithmetics like in the crontab eg. `17:00<sunset`, `sunrise>8:00`, `17:00<sunset`. You also can set the time with `17:00`. This string, if given, will overwrite the time from the `dt` parameter.

* __rrule__: You can use the recurrence rules documented in the [iCalendar RFC](http://www.ietf.org/rfc/rfc2445.txt) for recurrence use of a switching entry.

## Example

The following example will set the UZSU with two entries. The first will switch the item ON every two minutes, starting in two minutes and this five times. The second entry switches the corresponding item OFF every two minutes, starting in three minutes and this five times.

`sh.eg.wohnen.kugellampe.uzsu([{'dt':datetime.datetime.now() + datetime.timedelta(minutes=2), 'value':1, 'active':True, 'rrule':'FREQ=MINUTELY;INTERVAL=2;COUNT=5'},{'dt':datetime.datetime.now() + datetime.timedelta(minutes=3), 'value':0, 'active':True, 'rrule':'FREQ=MINUTELY;INTERVAL=2;COUNT=5'}])`

