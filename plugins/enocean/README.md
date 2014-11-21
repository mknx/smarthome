EnOcean - under development !!!

Please do not remove any comments until stable.
  
Configure plugin.conf 
=
  
Add the following lines to your plugin.conf and just change the serialport to the portname of your enocean-adpater.
A udev-rules for the enocean-adapter is recommend. The specification of the enocean tx_id is optional but mandatory for sending control commands from the stick to a device.
  
<pre>
[enocean]
    class_name = EnOcean
    class_path = plugins.enocean
    serialport = /dev/ttyUSB0
    tx_id      = 01A3f480
</pre>


Learning Mode:
For some enocean devices it is important to teach in the enocean stick first. In order to send a special learning message, start smarthome with the interactive console: ./smarthome.py -i
Then use the following command: sh.enocean.send_learn()
That's it!
  
Configure items
=
  
According to the plugin-implementation of the enocean-devices you have to specify at least a enocean-id (enocean serial number in format 01:a2:f3:2d), the correct enocean-rorg-code and an enocean-value. 
   
The following example ist for a rocker/switch with two rocker and 6 available combinations.  
left rocker down = A1  
left rocker up = A0  
right rocker down = B1   
right rocker up = B0  
both rockers down = A1B1   
both rockers up = A0B0   

Mechnical handle example:
handle_status = STATUS


<pre>
[A1]
type = bool
enforce_updates = true
enocean_id = 00:22:60:37
enocean_rorg = F6_02_02
enocean_value = A1
</pre>
  
Add new enocean devices
=
  
You have to know about the EnOcean RORG of your device, so pleas ask Mr.Google or the vendor. Further the RORG must be declared in the plugin. The following EEPs are supported:

F6_02_02	2-Button-Rocker
F6_02_03	2-Button-Rocker
F6_10_00	Mechanical Handle  

A5_11_04	Dimmer status feedback
A5_3F_7F
