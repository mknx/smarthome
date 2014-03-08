# Drexel & Weiss

This plugin uses the D&W USB service interface for connection, so you don't need the additional modbusadapter. Be careful not to configure wrong parameters, otherwise the function of your device may be damaged. The D&W warranty is not including this case of damage!

Requirements
============
This plugin needs one of the supported Drexel&Weiss devices:

   * aerosilent stratos


Configuration
=============

plugin.conf
-----------
<pre>
[DuW]
   class_name = DuW
   class_path = plugins.drexelundweiss
   tty = /dev/ttyUSB0
#   LU_ID = 130
#   WP_ID = 140
</pre>

You have to adapt the tty to your local enviroment and change LU_ID and WP_ID if not D&W default is used.

items.conf
--------------

### DuW_register
With this attribute you could specify the D&W register ID found in the modbus documentation of D&W (900.6666_00_TI_Modbus_Parameter_DE.pdf)

# Example
<pre>
[KWL]
    [[MODE]]
        name = Betriebsart
        visu_acl = rw
        type = num
        DuW_register = 5002
        sv_widget = {{ basic.slider('item', 'item', 0, 5, 1) }}
</pre>


Functions
=========

......
