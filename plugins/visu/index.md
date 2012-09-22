---
title: Visu Plugin
summary: WebSocket interface for an jQuery mobile user interface.
layout: default
created: 2011-04-12T19:41:03+0200
changed: 2012-04-12T19:41:03+0200
---

This plugin provides an javascript interface for the JQuery mobile framework (shipping with 1.1.1 and jQuery 1.7.1). It has been tested with Chrome (18.0.1025.151), Firefox (11.0), Safari (5.1.5) and mobile Safari (iOS 5.1).
Right now the WebSocket interface of SmartHome.py only supports nonencrypted connections. Please use a internal network or VPN to connect to the service.

# Requirements
This plugin needs just a webserver to serve the HTML and JavaScript files for the GUI.

# Configuration

## plugin.conf
<pre>
[visu]
    class_name = WebSocket
    class_path = plugins.visu
#   ip='0.0.0.0'
#   port=2121
</pre>

This plugins listens by default on every IP address of the host on the TCP port 2121.

## items.conf

If you want to use the value of an item in you user interface you have to set it.
Right now it doesn't matter which value you set. But I'm planning to implement some basic access controll list function.

<pre>
[example]
    [[toggle]]
        value = True
        type = bool
        visu = rw
</pre>


## logic.conf
You could specify the `visu` attribute to every logic in your logic.conf. This way you could trigger the logic via the interface.
<pre>
[dialog]
    filename = 'dialog.py'
    visu = true
</pre>

Functions
=========

dialog(header, content)
-----------------------
This function opens a jQuery mobile dialog.
<pre>sh.visu.dialog('Easy', 'going')</pre> would create the following dialog on every client.
![dialog](/media/img/dialog.png)

User Interface
==============
See the [JQuery mobile](http://jquerymobile.com/) website for instructions how to build the interface. On the website is a interactive designer to get you started in no time.
There are several other graphical tools to build a website with JQuery mobile.

You could find an example in the `/usr/local/smarthome/plugins/visu/example/` or have a look at the [noninteractive version](example.html) on this website.

See the `example.html` source for the structure of the header and the file. You have to load the minified `smarthome.min.js` or `smarthome.js` for debug output on the javascript console.

my.smarthome.js
---------------
You have to initialise the javascript to connect to the backbone. You could do this with `shInit("ws://"+ location.host + ":2121/");` which tries to open a WebSocket connection to the host (webserver) on port 2121.

HTML and data-sh
----------------
You could update the value or content of several HTML elements. Every element could be associated with an SmartHome.py item by adding the attribute `data-sh="area.item"` to the element.

The following elements are supported:

  * a: anchor for creating buttons to trigger logics. The `data-sh` has to set to the logic name as specified in the logic.conf.
  * div/span: update the content of the div/span
  * img: to update the `src` attribute of the element
  * input/textarea/select: to create forms

You could find every supported element and usage in the `example.html`.

