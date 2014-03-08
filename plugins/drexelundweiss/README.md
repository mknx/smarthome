# Drexel & Weiss

Requirements
============
This plugin needs one of the supported Drexel&Weiss devices connected through the USB service interface (not Modbusadapter):

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
With this attribute you could specify the D&W register ID

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
