
See http://mknx.github.io/smarthome/ for more information and documentation.

## Directory and File Overview
This should give you an overview of the most important files and directories.

### etc/smarthome.conf
This is a global configuration file where you could specify the location and timezone of your smart home.

### etc/plugin.conf
In this configuration file you configure the plugins and their attributes.

### etc/logic.conf
In the logic.conf you specify your logics and when they will be run.
<pre>
# etc/logic.conf
[AtSunset]
    filename = sunset.py
    crontab = sunset
</pre>

### items/
This directory contains one or more item configuration files. The filename does not matter, except it has to end with '.conf'.
<pre>
# items/global.conf
[global]
    [[sun]]
        type = bool
        attribute = foo
</pre>

### logics/
This directory contains your logic files. Simple or sophisitcated python scripts. You could address your smarthome item by `sh.item.path`.
If you want to read an item call `sh.item.path()` or to set an item `sh.item.path(Value)`.

<pre>
# logics/sunset.py
if sh.global.sun():  # if sh.global.sun() == True:
    sh.gloabl.sun(False)  # set it to False
</pre>

