---
title: UDP Plugin
summary: A UDP Plugin to send and receive UDP Messages and trigger logics.
layout: default
created: 2011-04-08T20:58:06+0200
changed: 2011-04-08T20:58:06+0200
---


END OF LIFE
===========

This plugin is no longer supported. Use the generic [network plugin](../network/) for in and outgoing data.


Requirements
============

Configuration
=============
plugin.conf
-----------
This plugin has no additional arguments in the plugin.conf.
<pre>
['udp']
   class_name = UDP
   class_path = plugins.udp
</pre>

smarthome.conf
--------------

### udp_listen
You could specify the `udp_listen` attribute to every item in your smarthome.conf. The argument could be a port or ip:port and a list of both.
<pre>
['test']
    [['item1']]
        type = string
        # bind to 0.0.0.0:7777 (every IP address)
        udp_listen = 7777

    [['item2']]
        type = string
        # bind to 0.0.0.0:7777 and 127.0.0.1:8888
        udp_listen = 7777, 127.0.0.1:8888
</pre>
If you send a UDP packet to the port, the corrosponding item will be set to the UDP payload.
<code>$ echo teststring | nc -u 127.0.0.1 7777</code> would set the value of item1 and item2 to 'teststring'.

### udp_send
If you specify `udp_send` as an attribute every change of an item will send the new value to the specified IP and port.
<pre>
    [['item3']]
        type = string
        udp_send = 192.168.0.4:7777

    [['item4']]
        type = string
        udp_send = 192.168.0.4:7777, 192.168.0.8:8888
</pre>

<code>sh.test.item3('yeah')</code> will send 'yeah' to 192.168.0.4 port 7777.
<code>sh.test.item4('baby')</code> will send 'baby' to 192.168.0.4 port 7777 and 192.168.0.8 port 8888.

logic.conf
----------
You could specify the `udp_listen` attribute to every logic in your logic.conf. The argument could be a port or ip:port and a list of both.
<pre>
['logic1']
    # bind to 0.0.0.0:7777 (every IP address)
    udp_listen = 7777

['logic2']
    # bind to 0.0.0.0:7777 and 127.0.0.1:8888
    udp_listen = 7777,127.0.0.1:8888
</pre>
If you send a UDP packet to the port, the corrosponding item will be triggerd and the payload will be passed (via the triggered object) to the logic.
<code>$ echo teststring | nc -u 127.0.0.1 7777</code> would trigger the logics 'logic1' and 'logic2'.

Functions
=========

send(host, port, data)
----------------------
<code>sh.udp.send('192.168.0.5', 9999, 'turn it on')</code> would send 'turn it on' to 192.168.0.5 port 9999. Simple, isn't it?

