Roadmap
=======
   * Denon Plugin
   * MPD Plugin

# 0.9
## Features
   * Scene support
   * Item: setting values by crontab and cycle
   * Logic: calling with values by crontab and cycle

# 0.8
## Contributions from:
   * Niko Will
   * Alexander Rieger

## New Plugins
   * DWD Plugin: new plugin to fetch weather warnings and forecasts from Deutscher Wetterrdienst (DWD)
   * Mail Plugin: IMAP, SMTP
   * RRD Plugin: build round robin databases and create graphs with flot.
   * Russound Plugin: RIO
   * Snom Plugin: to handle snom VOIP phones.

## Features
   * Base
    * sh.tools.fetch_url()
    * item.conf: new types list, dict
    * sh.moon() with set(), rise(), pos(), light(), phase()
    * sh.find_items('config_string'), sh.find_children(self, parent, 'config_string')
   * Asterisk plugin: Call Log, mailbox count
   * CLI plugin: adding 'rl' to reload logic, and 'rr' to reload and run logic
   * KNX plugin: DPT 16 support
   * Network plugin: adding simple http interface
   * Visu plugin: plot rrd with flot,
      * push buttond sends now cyclic,
      * list view
      * dpt3 push buttons,
      * TITLE header template,
      * adding 'unit' attribute to item.conf
      * JQuery: 1.8.3, JQuery Mobile 1.2
      * Log view  SmartHome.py, Asterisk

## Bug Fixes
   * KNX plugin: knx_init/knx_cache could not work if first connection attempt failed
        dpt 10, 11 encoding
   * Onewire plugin: improve error handling
   * Workaround for urllib2 memory leakage


# 0.7

## Features
   * Items
      * Trees: You could now build unlimited item trees.
      * id(): function to return the item id (path).
      * eval: see the item configuration page for an explanation for 'eval' and 'eval_trigger'.
   * Asterisk Plugin: hangup(channel)
   * iCal Plugin: to parse iCal files
   * Visu Plugin:
      * autogenerate visu pages
      * new input type 'time'
    * SmartHome.py:
       * sh.scheduler.change
       * directory structure cleanup: logic => logics
       * sh.tools.dewpoint(): new function to calculate the dewpoint
       * sh.tools.ping(): moved ping to the tools object.
       * sh.tz => sh.tzinfo(): new function tzinfo().

## Bug Fixes
    * CLI Plugin: update attribute negated

0.6
===
Nonfunctional changes
---------------------
+ Heavy redesign of the underlying framework to reduce the number of necessary threads and system footprint.

Features
--------
+ Network plugin: new plugin to send and receive TCP/UDP messages.
+ DMX accepts a channel list as item attribute to change multiple channels with one item
+ sh.string2bool()
+ KNX plugin: changed class options.
+ Visu plugin: added three interactive image elements.
+ 1-Wire plugin: changed class options. new function ibutton_hook.
+ -d start option to use the debug log level
+ new item types: list, foo

Bug Fixes
---------
+ Visu Plugin: Improve error handling if connection is lost or could not connect the socket

0.5
===
Features
--------
+ WebSocket/JQuery mobile Visu
+ ping: sh.ping(host), return True if up, False if down.
+ sh.return_item(path)
+ sh.return_items()
+ sh.return_areas()

Bug Fixes
---------
+ Asterisk plugin: update_db() now log errors
+ set enviroment TZ

0.4
===
Features
--------
+ KNX plugin: reply to read requests


0.3
===
Features
--------
+ item.fade(): fade the item to a specified value
+ item.area: provides access to the area object
+ logic.alive: safe loop expression for a clean shutdown
+ crontab: new keyword 'init'
+ CLI plugin: new function 'tr' to trigger logics
+ Asterisk plugin: to monitor channels and listen for UserEvents

Nonfunctional changes
---------------------
+ New Logic handling. Now logics share some worker threads. Multiple logic instances could run at the same time.
+ Two new functions to call/trigger a logic: logic.trigger() and sh.trigger().
+ Every logic provides an 'trigger' object with the reason of the call.

Bug Fixes
---------
+ sh.sun.set() and rise provides a timezone aware datetime. :-)
  And a small fix in computing the dates.


0.2
===
Features
--------
+ item attribute threshold: set low:high
                            or only low which is equal to low:low
+ item attribute offset: You could specify offsets for numeric item types.
+ cli plugin
+ dmx plugin

Bug Fixes
---------
+ knx_ga => knx_send, knx_listen
+ sh.sun.set() provided a timezone aware datetime.

