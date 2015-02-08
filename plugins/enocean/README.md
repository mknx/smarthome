EnOcean - Still under development.


Configure plugin.conf
=

Add the following lines to your plugin.conf and just adapt the serial port to your port name of your enocean-adpater.
A udev-rules for the enocean-adapter is recommend. The specification of the enocean tx_id is optional but mandatory for sending control commands from the stick to a device. When controlling multiple devices, it is recommended to use the stick's BaseID (not ChipID) as transmitting ID.
For further information regarding the difference between BaseID and ChipID, see https://www.enocean.com/en/knowledge-base-doku/enoceansystemspecification:issue:what_is_a_base_id/
With the specification of the BaseID, 128 different transmit IDs are available, ranging between BaseID and BaseID + 127.

<pre>
[enocean]
    class_name = EnOcean
    class_path = plugins.enocean
    serialport = /dev/ttyUSB0
    tx_id      = FFFF_4680
</pre>


Learning Mode:
For some enocean devices it is important to teach in the enocean stick first. In order to send a special learning message, start smarthome with the interactive console: ./smarthome.py -i
Then use the following command:
<pre>
    sh.enocean.send_learn(ID_Offset)
</pre>
, where ID_Offset, range (0-127), specifies the sending ID offset with respect to the BaseID. Later, the ID offset is specified in the item.conf for every outgoing send command, see example below.
Use different ID offsets for different groups of actors.
That's it!

Configure items
=

 The following example is for a rocker/switch with two rocker and 6 available combinations (EEP F6_02_02).
left rocker down = A1
left rocker up = A0
right rocker down = B1
right rocker up = B0
both rockers up = A1B1
both rockers down = A0B0


The following example is for a rocker/switch with two rocker and 6 available combinations (EEP F6_02_03).
left rocker down = A1
left rocker up = A0
right rocker down = B1
right rocker up = B0
last state of left rocker = A
last state of right rocker = B

Mechanical handle example:
handle_status = STATUS

Example item.conf
=
<pre>
[Enocean]
    [[Door]]
        enocean_rx_id = 01234567
        enocean_rx_eep = D5_00_01
        [[[status]]]
            type = bool
            enocean_rx_key = STATUS
    [[FT55switch]]
        enocean_rx_id = 012345AA
        enocean_rx_eep = F6_02_03
            [[[up]]]
                type = bool
                enocean_rx_key = B0
            [[[down]]]
                type = bool
                enocean_rx_key = B1
    [[dimmer1]]
        enocean_rx_id = 00112233
        enocean_rx_eep = A5_11_04
        [[[light]]]
            type = bool
            enocean_rx_key = STAT
            enocean_tx_eep = A5_38_08_02
            enocean_tx_id_offset = 1
            [[[[level]]]]
                type = num
                enocean_rx_key = D
                enocean_tx_eep = A5_38_08_03
                enocean_tx_id_offset = 1
    [[handle]]
        enocean_rx_id = 01234567
        enocean_rx_eep = F6_10_00
        [[[status]]]
            type = num
            enocean_rx_key = STATUS
    [[actor1]]
            enocean_rx_id = FFAABBCC
            enocean_rx_eep = A5_12_01
            [[[power]]]
                type = num
                enocean_rx_key = VALUE
    [[actor1B]]
            enocean_rx_id = FFAABBCD
            enocean_rx_eep = F6_02_03
            [[[light]]]
                type = bool
                enocean_rx_key = B
                enocean_tx_eep = A5_38_08_01
                enocean_tx_id_offset = 2

</pre>

Add new listening enocean devices
=

You have to know about the EnOcean RORG of your device, so pleas ask Mr.Google or the vendor. Further the RORG must be declared in the plugin. The following EEPs are supported:

F6_02_02    2-Button-Rocker

F6_02_03    2-Button-Rocker, Status feedback from manual buttons on different actors, e.g. Eltako FT55, FSUD-230, FSVA-230V or Gira switches.

F6_10_00    Mechanical Handle

A5_11_04    Dimmer status feedback

A5_12_01    Power Measurement

D5_00_01    Door/Window Contact, e.g. Eltako FTK, FTKB

Send commands: Tx EEPs
=

A5_38_08_01 Regular switch actor command (on/off)

A5_38_08_02 Dimmer command with fix on off command (on: 100, off:0)

A5_38_08_03 Dimmer command with specified dim level (0-100)
