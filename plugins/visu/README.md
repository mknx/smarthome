# Visualisation

This plugin provides an javascript interface for the JQuery mobile framework (shipping with 1.1.1 and jQuery 1.7.1). It has been tested with Chrome (18.0.1025.151), Firefox (11.0), Safari (5.1.5) and mobile Safari (iOS 5.1).
Right now the WebSocket interface of SmartHome.py only supports nonencrypted connections. Please use a internal network or VPN to connect to the service.

# Requirements
This plugin needs just a webserver to serve the HTML and JavaScript files for the GUI.
The example files in 'examples/visu' have to be placed in the _root directory_ of the webserver!

# Configuration

## plugin.conf
<pre>
[visu]
    class_name = WebSocket
    class_path = plugins.visu
#   ip='0.0.0.0'
#   port=2121
#   visu_dir = False
#   smartvisu_dir = False
</pre>

This plugins listens by default on every IP address of the host on the TCP port 2121.
The attribute `visu_dir` and `smartvisu_dir` are described in the subsection autogeneration.

## items.conf

Simply set the visu attribute to something to allow read/write access to the item. There are special keywords described in the subsection autogeneration.

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

## Quickstart

   * set the the visu_dir in the plugin.conf to the root directory of you webserver e.g. `/var/www/visu`
   * copy the basic structure to the root directory `cp -r /usr/local/smarthome/examples/visu/* /var/www/visu/`
   * copy the example item configuration in your items directory `cp /usr/local/smarthome/examples/items/visu.conf /usr/local/smarthome/items/`
   * start SmartHome.py
   * goto http://yourserver/example.html


Functions
=========

## dialog(header, content)

This function opens a jQuery mobile dialog.
<pre>sh.visu.dialog('Easy', 'going')</pre> would create the following dialog on every client.
![dialog](/smarthome/img/dialog.png)

## url(url)

Change the current visu page to the specified url. e.g. `sh.visu.url('http://smarthome.local/door.html')`


User Interface
==============
## smartVISU

You could generate pages for the [smartVISU](http://code.google.com/p/smartvisu/) visualisation if you specify the `smartvisu_dir` which should be set to the root directory of your smartVISU installation.
In the examples directory you could find a configuration with every supported element. `examples/items/smartvisu.conf`  

The attribute keywords are:

   * sv_page: to generate a page for this item. You have to specify `sv_page = room` to activate it. Every widget beneath this item will be included in the page.
   * sv_img: with this attribute you could assign an icon or picture for a page or widget.
   * sv_widget: This has to be a double quoted encapsulated string with the smartVISU widget. You could define multiple widgets by separating them by a comma. See the example below:

<pre>
[second]
    [[sleeping]]
        name = Sleeping Room
        sv_page = room
        sv_img = scene_sleeping.png
        [[[light]]]
            name = Light
            type = bool
            visu = yes
            sv_widget = "&#123;&#123; device.dimmer('second.sleeping.light', 'Light', 'second.sleeping.light', 'second.sleeping.light.level') &#125;&#125;"
            knx_dpt = 1
            knx_listen = 3/2/12
            knx_send = 3/2/12
            [[[[level]]]]
                type = num
                visu = yes
                knx_dpt = 5
                knx_listen = 3/2/14
                knx_send = 3/2/14
</pre>

But instead of giving the widget distinct options you could use `item` as a keyword.
The page generator will replace it with the current path. This way you could easily copy widget calls and don't type the item path every time.
<pre>
[second]
    [[sleeping]]
        name = Sleeping Room
        sv_page = room
        sv_img = scene_sleeping.png
        [[[light]]]
            name = Light
            type = bool
            visu = yes
            sv_widget = "&#123;&#123; device.dimmer('item', 'item.name', 'item', 'item.level') &#125;&#125;"
            knx_dpt = 1
            knx_listen = 3/2/12
            knx_send = 3/2/12
            [[[[level]]]]
                type = num
                visu = yes
                knx_dpt = 5
                knx_listen = 3/2/14
                knx_send = 3/2/14
</pre>

