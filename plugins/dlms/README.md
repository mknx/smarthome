# DLMS

# Requirements

* smartmeter using DLMS (Device Language Message Specification) IEC 62056-21
* ir reader e.g. from volkszaehler.org
* serial port/USB-serial adapter

make sure the serial port can be used by the user executing smarthome.py

Example (adapt the vendor- and product-id!):
<pre>
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="6010", MODE="666"' > /etc/udev/rules.d/99-smartmeter.rules
udevadm trigger
</pre>

If you like, you can also give the serial port a descriptive name with this.

## Supported Hardware

* smart meters using using DLMS (Device Language Message Specification) IEC 62056-21
* e.g. Landis & Gyr ZMD120

# Configuration

## plugin.conf

<pre>
[dlms]
    class_name = DLMS
    class_path = plugins.dlms
    serialport = /dev/ttyO1
#    update_cycle = 20
#    baudrate = 300
</pre>

Description of the attributes:

* __update_cycle__: interval in seconds how often the data is read from the meter (default 60)
* __baudrate__: use fixed baudrate after startup (always 300 baud) [300,600,1200,2400,4800,9600,auto] (default 'auto')

## items.conf

You can use all obis codes available by the meter.

To get a list of all available OBIS codes of your reader, start smarthome.py in Debug-mode. All codes which can be obtained from the reader will be printer after the first successful read operation.

Attributes:
* __dlms_obis_code__: obis code such as 'x.y', 'x.y.z' or 'x.y.z*q'
 
<pre>
[Stromzaehler]
  [[Bezug]]
    [[[Energie]]]
      type = num
      dlms_obis_code = 1.8.1
  [[Lieferung]]
    [[[Energie]]]
      type = num
      dlms_obis_code = 2.8.1
</pre>
