# Requirements

pyusb

install by
<pre>
apt-get install python3-setuptools
easy_install3 pyusb
</pre>

## Supported Hardware

* Applied Sensor iAQ Stick
* Voltcraft CO-20 (by Conrad)
* others using the same reference design

# Configuration

## plugin.conf

<pre>
[iaqstick]
    class_name = iAQ_Stick
    class_path = plugins.iaqstick
#    update_cycle = 10
</pre>

Description of the attributes:

* __update_cycle__: interval in seconds how often the data is read from the stick (default 10)

## items.conf

You can use all commands available by the serial interface.

For a explanation of all available commands type 'help' when connected to robot

Attributes:
* __iaqstick_info__: used to get data from the stick
 
Fields:
* __ppm__: get the air quality measured in part-per-million (ppm)

<pre>
[iAQ_Stick]
  [[PPM]]
    type = num
    sqlite = true
    iaqstick_info = ppm
</pre>
