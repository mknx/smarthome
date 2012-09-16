---
title: Plugin Configuration
summary: Setup your SmartHome.py plugins
uid: pluginconfig
created: 2011-04-08T20:45:46+0200
changed: 2011-04-08T20:45:46+0200
type: page
---

Introduction
============
Plugins extend the core functionality of SmartHome.py. You could access these plugins from every logic script.
For example there is a plugin for the prowl notification service to send small push messages to your iPhone/iPad.
Plugins are placed in <code>/usr/local/smarthome/plugins/</code>.

Configuration
=============
Plugins are configured in the plugin.conf file. A simple one looks like this:

<pre># /usr/local/smarthome/etc/plugin.conf
['notify'] # object name
    class_name = Prowl # class name of the python class
    class_path = plugins.prowl # path to the plugin
    apikey = asdf1234asdf1234 # secret key for prowl
</pre>

The object name, class name and class path must be provided.
The other attributes depend on the individual plugin. See the corrosponding plugin page for more information.

The example above would generate the following statement `sh.notify = plugins.prowl.Prowl(apikey='asdf1234asdf1234')`.
From now on there is the object `sh.notify` and you could access the function of this object with `sh.notify.function()`.

