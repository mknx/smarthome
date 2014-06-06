# logo

# Requirements
Siemens LOGO PLC

libnodave - a free library to communicate to Siemens S7 PLCs
used version: 0.8.4.6

raspberry.pi: copy the file 'libnodave.so' to '/lib/libnodave.so'

other machines: download the library  and run 'make'
http://libnodave.sourceforge.net/

## Supported Hardware

Siemens LOGO version 0BA7

# Configuration

## plugin.conf

Please provide a plugin.conf snippet for your plugin with ever option your plugin supports. Optional attributes should be commented out.

<pre>
[logo]
    class_name = LOGO
    class_path = plugins.logo
    host = 10.10.10.99
    #port = 102 
	#io_wait=5 
</pre>

This plugin needs an host attribute and you could specify a port attribute

* 'io_wait' = timeperiod between two read requests. Default 5 seconds.

items.conf
--------------

### logo_read
Input, Output, Mark to read from Siemens Logo

### logo_write
Input, Output, Mark to write to Siemens Logo

* 'I' Input bit to read I1, I2 I3,.. I24
* 'Q' Output bit to read/write Q1, Q2, Q3,.. Q16
* 'M' Mark bit to read/write M1, M2 M3, .. M27
* 'AI' Analog Input(word) to read AI1, AI2, AI3,..I8
* 'AQ' Analog Output(word) to read/write AQ1, AQ2
* 'AM' Analog Mark(word) to read/write AM1, AM2, AM3,..AM16
* 'VM' VM-Byte to read/write VM0, VM1, VM3,.. VM850
* 'VMx.x' VM-Bit to read/write VM0.0, VM0.7, VM3.4,.. VM850.7
* 'VMW' VM-Word to read/write VMW0, VM2, VMW4,.. VM849

<pre>
# items/my.conf
[myroom]
    [[status_I1]]
        typ = bool
        logo_read = I1
    [[lightM1]]
        typ = bool
        knx_dpt = 1
        knx_listen = 1/1/3
        knx_init = 1/1/3
        logo_write = M4
     [[temp_measure]]
        typ = num
        eval = value/10
        visu = yes
        sqlite = yes
        logo_read = AI1
    [[temp_set]]
        typ = num
        visu = yes
        logo_write = VMW4
</pre>
