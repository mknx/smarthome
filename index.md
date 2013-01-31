---
title: Overview
layout: default
summary:
uid: index
created: 2011-08-08T21:27:24+0200
changed: 2012-06-21T18:27:24+0200
---

SmartHome.py is a modular framework to automate your (smart) home.

See the [install](install) and [config](config) section to start your SmartHome.

# 2013-02-02 Preview: Releasing an Raspberry Pi image with SmartHome.py and smartVISU. *

## 2013-01-31 New Release [0.8](https://github.com/mknx/smarthome/tags)
with contributions from: Niko Will and Alexander Rieger. Thank you.

I am happy to announce a new cooperation with [smartVISU](http://code.google.com/p/smartvisu/) to give you the best user interface experience.

### New Plugins
   * [DWD Plugin](plugins/dwd): fetch weather warnings and forecasts from Deutscher Wetterrdienst (DWD).
   * [Mail Plugin](plugins/mail): sending (SMTP) and receiving (IMAP) mail.
   * [RRD Plugin](plugins/rrd): build round robin databases.
   * [Russound Plugin](plugins/russound): control a Russound audio device with RIO over TCP.
   * [Snom Plugin](plugins/snom): to handle snom VOIP phones.

### Features
   * Base
    * sh.tools.fetch_url()
    * item.conf: new types list, dict
    * sh.moon() with set(), rise(), pos(), light(), phase()
    * sh.find_items('config_string'), sh.find_children(self, parent, 'config_string')
   * Asterisk plugin: Call Log and mailbox count
   * CLI plugin: adding 'rl' to reload and 'rr' to reload and run logic
   * KNX plugin: DPT 16 support
   * Network plugin: adding a simple http interface
   * Visu plugin:
      * [smartVISU](http://code.google.com/p/smartvisu/) support: to generate pages for and communicate with this visualisation framework.
      * plot rrd with flot
      * list view
      * dpt3 push buttons
      * TITLE header template
      * adding 'unit' attribute to item.conf
      * JQuery: 1.8.3, JQuery Mobile 1.2
      * Log view  SmartHome.py, Asterisk

### Bug Fixes
   * KNX plugin: knx_init/knx_cache could not work if first connection attempt failed
     * dpt 10, 11, 16 handling fix
   * Onewire plugin: improve error handling
   * Workaround for urllib2 memory leakage

## 2012-09-27 New Release [0.7](https://github.com/mknx/smarthome/tags)

### Features
   * Items
      * Trees: You could now build unlimited item trees.
      * id(): function to return the item id (path).
      * eval: see the item configuration page for an explanation for 'eval' and 'eval_trigger'.
   * [Asterisk plugin](plugins/asterisk): new function hangup(channel)
   * [iCal plugin](plugins/ical): to parse iCal files
   * [Visu Plugin](plugins/visu):
      * autogenerate visu pages
      * new input type 'time'
   * SmartHome.py:
      * sh.scheduler.change
      * directory structure cleanup: logic => logics
      * items directory: to put multiple item configuration files in
      * sh.tools.dewpoint(): new function to calculate the dewpoint
      * sh.tools.ping(): moved ping to the tools object.
      * sh.tz => sh.tzinfo(): new function tzinfo().

### Bug Fixes

  * CLI Plugin: update attribute negated

## 2012-06-21 New Release [0.6](http://sourceforge.net/projects/smarthome/files/)

### Nonfunctional changes
  * Redesign of the underlying framework to reduce the number of necessary threads and system footprint.

### Features
  * [Network plugin](plugins/network) to receive TCP/UDP and send UDP messages and to trigger logics.
  * [DMX plugin](plugins/dmx) accepts now a channel list to bound several channel to one item (value)
  * [KNX plugin](plugins/knx) changed class options to `host` and `port`. Adding support for more DPTs. Sending the date/time on the bus.
  * [Asterisk plugin](plugins/asterisk) changed class options to `host` and `port`. New functions: db_write, db_read and mailbox_count.
  * [1-Wire plugin](plugins/onewire) changed class options to `host` and `port`. Supporting the current owfs version (2.8p15). New function [ibutton_hook](plugins/onewire/#ibuttonhookibutton-item) to monitor intrusion attempts.
  * [Visu](plugins/visu) three new interactive image elements added: switch, push and set. See the example.html file. JQuery mobile updated to 1.1.0. Websocket default `port` changed to 2121.
  * New [item types](/config#item-attributes) list and foo.
  * New start option `-d` to set the log level to debug.
  * UDP plugin is no longer supported. Please use the generic network plugin instead.

### Bug Fixes
 * Due to the redesign several bugs are fixed. I hope it will not intruduce the same amount of new bugs ;-)


## 2012-04-12 New Release [0.5](http://sourceforge.net/projects/smarthome/files/)

### Features
  * [Visu](plugins/visu) with JQuery mobile
  * ping: sh.ping(host), return True if up, False if down.

### Bug Fixes
  * using the enviroment timezone (TZ) - if provided

## 2011-10-29 New Release [0.4](http://sourceforge.net/projects/smarthome/files/)

### Feature
  * KNX Reply with [KNX plugin](plugins/knx)


## 2011-08-14 New Release [0.3](http://sourceforge.net/projects/smarthome/files/)

### Features
 * [Asterisk plugin](plugins/asterisk) to monitor channels and listen for UserEvents
 * [item.fade()](config#fade): fade the item to a specified value
 + [item.area](config#item-attributes): provides access to the area object
 + [logic.alive](logic/config#logic): safe loop expression for a clean shutdown
 + [logig crontab](logic/config#crontab): new keyword 'init'
 + [CLI plugin](plugins/cli/#usage): new function 'tr' to trigger logics

### Nonfunctional changes

 * New Logic handling. Logics share worker threads and multiple instances of one logic could run at the same time.
 * Two new functions to call/trigger a logic: logic.trigger() and sh.trigger().
 * Every logic provides an 'trigger' object with the reason of the call.

### Bug Fixes

 * sh.sun.set() and rise provides a timezone aware datetime. :-)
   And a small fix in computing the dates.

## 2011-06-21 New Release [0.2](http://sourceforge.net/projects/smarthome/files/) 

### Features
 * Two new [item attributes](config#item-attributes): threshold and offset
 * [CLI plugin](plugins/cli/) for a simple telnet interface
 * [DMX plugin](plugins/dmx/) to interact with the DMX bus

### Bug Fixes
 * sh.sun.set() provided a timezone aware datetime which results in a internal conflict with a third party function.
 * knx_ga is splitted into two attributes: knx_send, knx_listen. See the [KNX plugin](plugins/knx/) for more information.


## 2011-04-09 Initial Release
You could find the initial release 0.1 in the [download](http://sourceforge.net/projects/smarthome/files/) section.
