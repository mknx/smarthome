---
title: FritzBox Plugin
summary: A plugin to send commands to a FritzBox.
uid: index
layout: default
created: 2013-05-15T20:58:06+0200
changed: 2013-05-15T20:58:06+0200
---

# Requirements
This plugin has no requirements or dependencies.
At the moment only firmware versions before 5.50 are supported.

# Configuration

## plugin.conf
<pre>
[fritzbox]
    class_name = FritzBox
    class_path = plugins.fritzbox
    host = fritz.box
    password = blub
</pre>

### Attributes
  * `host`: specifies the hostname or ip address of your FritzBox.
  * `password`: the password for the web interface.

## items.conf

### fritzbox
With this attribute you can define supported functions of the plugin which are executed when the item is set to some value which can be interpreted as `true`.
  * `call <<from>> <<to>>`: with this, every time the item is set to `true` the FritzBox will initiate a call from the number defined with `from` to a number defined with `to`.

### fritzbox:<<telcfg>>
This is a special kind of attribute. Each attribute which starts with `fritzbox:` is taken to create a dictionary, which is sent to the FritzBox whenever the corresponding sh.py item can be interpreted as `true`. Here you can use every command which is available for the telcfg interface (just replace the `telcfg:` with `fritzbox:`). A list of known commands is described here: http://www.wehavemorefun.de/fritzbox/Telcfg
Please have a look at the following example which may explain this attribute a bit better:

<pre>
[fb]
    [[call1]]
        type=bool
        fritzbox=call **610 **611
    [[call2]]
        type=bool
        fritzbox:settings/UseClickToDial = '1'
        fritzbox:command/Dial = '**610'
        fritzbox:settings/DialPort = '**611'
</pre>

Both `call1` and `call2` will have the same effect. The first uses the implemented call function. The later uses the telcfg commands which are used internally in the call function. With the second option you can control almost anything which can be controlled via the web interface of your FritzBox.

## logic.conf

Currently there is no logic configuration for this plugin.

# Functions

## call(from, to)
This function calls a specified number with the specified caller.
<pre>
sh.fritzbox.call('**610', '**611')
</pre>
