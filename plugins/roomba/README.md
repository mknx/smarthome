Roomba
====

plugin.conf:
=
<pre>
[roomba]
     class_name = Roomba
     class_path = plugins.roomba
     tty = /dev/rfcomm1
     baudrate = 57600
     cycle = 0 #0=deactivate reading sensors
</pre>


item.conf:
=
There are 3 attributes wich can be used with the Roomba-Plugin:

* <code>roomba_cmd = xxx</code>
Here you can use one of the following commands (clean, dock, power_off, spot, max) and the Roomba will do it.
You can also define a "driving scene": <code>roomba_cmd = backward | 2 | stop | 2 | clean</code>
Integers are sleep times in this moment. The above example drives 2 seconds backward, stops for 2 seconds and begins to clean.
There are the following commands available:
forward (100mm/s)
backward (100mm/s)
spin_left
spin_right
stop

* <code>roomba_get = xxx</code>
Use the following item.conf to see how to configure the item for your wanted sensor. 
I think the names are self explaining.

* <code>roomba_raw = [123]</code>
To send integers to Roomba following the documentation of Roomba SCI as List!

<pre>[roomba]
    [[command]]
        [[[clean]]]
			enforce_updates = true
            name = clean
            type = bool
            roomba_cmd = clean
        [[[dock]]]
			enforce_updates = true
            name = dock
            type = bool
            roomba_cmd = dock
        [[[power_off]]]
			enforce_updates = true
            name = power_off
            type = bool
            roomba_cmd = power_off
        [[[spot]]]
			enforce_updates = true
            name = spot
            type = bool
            roomba_cmd = spot
        [[[max]]]
			enforce_updates = true
            name = max
            type = bool
            roomba_cmd = max
        [[[test_scene]]]
			enforce_updates = true
            #drives backward for 2 seconds, then spins left for 2 seconds, then drives forward for 3 seconds, then spins right for 3 seconds, then stops and starts to clean after 2 seconds
            name = test-drive
            type = bool
            roomba_cmd = backward | 2 | spin_left | 2 | forward | 3 | spin_right | 3 | stop | 2 | clean
			
	[[raw]]
		[stop]
			type = bool
			enforce_updates = true
			roomba_raw = 137 | 0 | 0 | 0
		
    [[sensor]]
        [[[current]]]
            #current in mA
			enforce_updates = true
            type = num
            roomba_get = current
        [[[temperature]]]
            #temperature in degrees celsius
			enforce_updates = true
            type = num
            roomba_get = temperature
        [[[voltage]]]
            #voltage in mV
			enforce_updates = true
            type = num
            roomba_get = voltage
        [[[button_clean]]]
            #clean button pressed
			enforce_updates = true
            type = bool
            roomba_get = buttons_clean
        [[[capacity]]]
            #capacity in mA
			enforce_updates = true
            type = num
            roomba_get = capacity
        [[[charge]]]
            #charge in mA
			enforce_updates = true
            type = num
            roomba_get = charge
        [[[angle]]]
            #angle since last request
			enforce_updates = true
            type = num
            roomba_get = angle
        [[[distance]]]
            #distance since last request
			enforce_updates = true
            type = num
            roomba_get = distance
        [[[buttons_max]]]
			enforce_updates = true
            type = bool
            roomba_get = buttons_max
        [[[buttons_clean]]]
			enforce_updates = true
            type = bool
            roomba_get = buttons_clean
        [[[buttons_spot]]]
			enforce_updates = true
            type = bool
            roomba_get = buttons_spot
        [[[buttons_power]]]
			enforce_updates = true
            type = bool
            roomba_get = buttons_power
        [[[remote_opcode]]]
			enforce_updates = true
            type = num
            roomba_get = remote_opcode
        [[[dirt_detect_right]]]
			enforce_updates = true
            type = bool
            roomba_get = dirt_detect_right
        [[[dirt_detect_left]]]
			enforce_updates = true
            type = bool
            roomba_get = dirt_detect_left
        [[[motor_overcurrent_side_brush]]]
			enforce_updates = true
            type = bool
            roomba_get = motor_overcurrent_side_brush
        [[[motor_overcurrent_vacuum]]]
			enforce_updates = true
            type = bool
            roomba_get = motor_overcurrent_vacuum
        [[[motor_overcurrent_main_brush]]]
			enforce_updates = true
            type = bool
            roomba_get = motor_overcurrent_main_brush
        [[[motor_overcurrent_drive_left]]]
			enforce_updates = true
            type = bool
            roomba_get = motor_overcurrent_drive_left
        [[[virtual_wall]]]
			enforce_updates = true
            type = bool
            roomba_get = virtual_wall
        [[[cliff_right]]]
			enforce_updates = true
            type = bool
            roomba_get = cliff_right
        [[[cliff_front_right]]]
			enforce_updates = true
            type = bool
            roomba_get = cliff_front_right
        [[[cliff_front_left]]]
     	enforce_updates = true
            type = bool
            roomba_get = cliff_front_left
        [[[cliff_left]]]
			enforce_updates = true
            type = bool
            roomba_get = cliff_left
        [[[wall]]]
            enforce_updates = true
            type = bool
            roomba_get = wall
        [[[bumps_wheeldrops_bump_right]]]
			enforce_updates = true
            type = bool
            roomba_get = bumps_wheeldrops_bump_right
        [[[bumps_wheeldrops_bump_left]]]
			enforce_updates = true
            type = bool
            roomba_get = bumps_wheeldrops_bump_left
        [[[bumps_wheeldrops_wheeldrop_right]]]
			enforce_updates = true
            type = bool
            roomba_get = bumps_wheeldrops_wheeldrop_right
        [[[bumps_wheeldrops_wheeldrop_left]]]
			enforce_updates = true
            type = bool
            roomba_get = bumps_wheeldrops_wheeldrop_left
        [[[bumps_wheeldrops_wheeldrop_caster]]]
			enforce_updates = true
            type = bool
            roomba_cmd = bumps_wheeldrops_wheeldrop_caster
</pre>

Serial-Port:
=
There are several availabilitys to connect to Roomba Serial Port. This was tested with a bluetooth-modul wich creates a virtual serial port.
This can be done in do-it-yourself your you can buy it i.e. "FT41 BlueRoom" from Fussel Elektronik.
Not tested is a connection trough a wifi-rs232 adapter. 

#Bluetooth:
#install Bluetooth
<pre>apt-get install bluez bluez-utils</pre>

#scan for modules
<code>hcitool scan</code>
output:
<pre>
Scanning ...
	00:13:04:11:14:77	bluetooth-adapter
</pre>
#pair module
<code>bluez-simple-agent hci0 00:13:04:11:14:77</code>
Enter your PIN (0000/1234 for default) in following output:
<pre>RequestPinCode (/org/bluez/1975/hci0/dev_A8_26_D9_F3_55_59)
Enter PIN Code: 1234
Release
New device (/org/bluez/1975/hci0/dev_A8_26_D9_F3_55_59)
</pre>
#bind module to tty
<code>nano /etc/bluetooth/rfcomm.conf</code>
configure your rfcomm.conf:
<pre>rfcomm1 {
bind yes;
device 00:13:04:11:14:77;
channel 1;
comment "Roomba";
}
</pre>

Finally unplug and plug your bt-dongle an in /dev must be a /dev/rfcomm1 now.
Good doocumentation to Roombas SCI: http://www.robotiklubi.ee/_media/kursused/roomba_sumo/failid/hacking_roomba.pdf
