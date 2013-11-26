# SMA

# Requirements

bluez

install by
<pre>
$ apt-get install bluez
$ hcitool scan
Scanning ...
        <bt-addr>       <name of your inverter, e.g. 'SMA001d SN: 213000xxxx SN213000xxxx'>
$ simple-agent hci0 <bt-addr>
RequestPinCode (/org/bluez/3070/hci0/dev_bt_addr_underscores)
Enter PIN Code: <pin-code>
Release
New device (/org/bluez/3070/hci0/dev_bt_addr_underscores)
$ bluez-test-device trusted <bt-addr> yes
$ bluez-test-device list
</pre>

## Supported Hardware

Tested with:
* SMA SunnyBoy 5000TL-21
* SMA Sunny Tripower 8000TL-10

Should work with other SMA inverters as well - please let me know!

# Configuration

## plugin.conf

<pre>
[sma]
    class_name = SMA
    class_path = plugins.sma
    bt_addr = 00:80:25:21:7F:58
#    password = 0000
#    update_cycle = 60
</pre>

Description of the attributes:

* __bt_addr__: MAC-address of the inverter (find out with 'hcitool scan')
* __password__: password for accessing the inverter in user-mode (default 0000)
* __update_cycle__: interval in seconds how often the data is read from the inverter (default 60)

## items.conf

### AC_POWER

Current power feed to the grid (W)

### DAY_YIELD

Todays yield (Wh)

### TOTAL_YIELD

Total yield of the inverter (Wh)

### INV_SERIAL

Serial number of the inverter

### INV_ADDRESS

MAC-address of the inverter

### LAST_UPDATE

String represensting date/time of last successful read operation

### DC_POWER_STRING<x>

DC power supplied by string <x> (W)

### DC_VOLTAGE_STRING<x>

DC voltage supplied by string <x> (V)

### DC_CURRENT_STRING<x>

DC current supplied by string <x> (A)

<pre>
[Wechselrichter]
  [[Einspeiseleistung]]
    type = num
    sma = "AC_POWER"
  [[Tagesertrag]]
    type = num
    sma = "DAY_YIELD"
  [[Gesamtertrag]]
    type = num
    sma = "TOTAL_YIELD"
  [[Seriennummer]]
    type = num
    sma = "INV_SERIAL"
  [[MAC_Adresse]]
    type = str
    sma = "INV_ADDRESS"
  [[Letzte_Aktualisierung]]
    type = str
    sma = "LAST_UPDATE"
  [[DC_Leistung_String1]]
    type = num
    sma = "DC_POWER_STRING1"
  [[DC_Leistung_String2]]
    type = num
    sma = "DC_POWER_STRING2"
  [[DC_Spannung_String1]]
    type = num
    sma = "DC_VOLTAGE_STRING1"
  [[DC_Spannung_String2]]
    type = num
    sma = "DC_VOLTAGE_STRING2"
  [[DC_Strom_String1]]
    type = num
    sma = "DC_CURRENT_STRING1"
  [[DC_Strom_String2]]
    type = num
    sma = "DC_CURRENT_STRING2"
</pre>
