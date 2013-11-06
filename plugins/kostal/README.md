---
title: KOSTAL plugin
layout: default
summary: Retrieve data from a KOSTAL inverter module
---

# Requirements

This plugin is designed to retrieve data from a KOSTAL inverter module (e.g. PICO inverters).

## Supported Hardware

Is currently working with the following KOSTA inverter modules:

  * KOSTAL PIKO 7.0

# Configuration

## plugin.conf

Please provide a plugin.conf snippet for your plugin with ever option your plugin supports. Optional attributes should be commented out.

<pre>
[KOSTAL]
   class_name = Kostal
   class_path = plugins.kostal
   ip = 10.10.10.10
#   user = pvserver
#   passwd = pvwr
#   cycle = 300
</pre>

This plugin retrieves data from a KOSTAL inverter module of a solar energy
plant.

The data retrieval is done by establishing a network connection to the 
inverter module and retrieving the status via a HTTP request.

You need to configure the host (or IP) address of the inverter module. Also
the user and password attributes (user, passwd) can be overwritten, but
defaults to the standard credentials.

The cycle parameter defines the update interval and defaults to 300 seconds.

## items.conf

### kostal

This attribute references the information to retrieve by the plugin. The
following list of information can be specified:

  * power_current: The current power of the solar installation
  * power_total: The total amount of generated energy
  * power_day: The amount of generated energy for the current day
  * status: The textual status of the module (off, feeding, ...)
  * string1_volt ... string3_volt: The current voltage of string 1, 2, 3
  * string1_ampere ... string3_ampere: The current ampere of string 1, 2, 3
  * l1_volt ... l3_volt: The current voltage of L 1, 2, 3
  * l1_watt ... l3_watt: The current watt of L 1, 2, 3

### Example

Please provide an item configuration with every attribute and usefull settings.

<pre>
# items/my.conf

[solar]
    [[current]]
        type = num
        kostal = 1
</pre>

## logic.conf
If your plugin support item triggers as well, please describe the attributes like the item attributes.


# Methodes
If your plugin provides methods for logics. List and describe them here...

## method1(param1, param2)
This method enables the logic to send param1 and param2 to the device. You could call it with `sh.my.method1('String', 2)`.

## method2()
This method does nothing.
