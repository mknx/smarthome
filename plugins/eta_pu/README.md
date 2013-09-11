# Requirements
## Supported Hardware

* ETA Pellet Unit PU (http://www.eta.at) with remote access enabled

# Configuration
## plugin.conf

<pre>

[eta_pu]
    class_name = ETA_PU
    class_path = plugins.eta_pu
    address = 192.168.179.15
    port = 8080
    setpath = '/user/vars'
    setname = 'smarthome'

</pre>

Description of the attributes:

* __address__: ip address of the ETA pellet unit
* __port__: port of the ETA webserver (usally 8080)
* __setpath__: path to the presaved sets of CAN-bus-uri
* __setname__: the name of the set, used by this plugin

## items.conf

There ist one item type in this plugin. Every item has subitems for particular information of the requested uri.
The uri represents the CAN-bus-id in the pellet unit. Every CAN-bus-id request replies the following data:
E.g.:
<pre>
<value uri="/user/var/112/10021/0/0/12162" strValue="26" unit="°C" decPlaces="0" scaleFactor="10" advTextOffset="0">262</value>
</pre>

The subitem represents one field of the data line. A number ("26") plus unit ("°C") consists of two subitems for the same CAN-Bus-id (uri).

* __eta_pu_uri__: Contains the CAN-bus-id. The pellet unit shows all ids with discription by requesting http://ip/user/menu

* __eta_pu_type__: Represents the field of the data line. Must be one of: strValue, unit, decPlaces, scaleFactor, advTextOffset

### Example

<pre>
# items/eta_pu.conf
[eta_unit]
    [[boiler_state]]
       eta_pu_uri = 112/10021/0/0/12000
       type = str
       [[[strValue]]]
           eta_pu_type = strValue
           type = str
    [[emission_temperature]]
       eta_pu_uri = 112/10021/0/0/12162
       type = str
       [[[Value]]]
           eta_pu_type = strValue
           type = num
       [[[unit]]]
           eta_pu_type = unit
           type = str

</pre>

## logic.conf

t.b.d.

## ToDo
* reading errors (number of errors and text)
* setting of parameters
* reading the raw file of an uri

