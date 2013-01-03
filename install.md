---
title: Installation
layout: default
summary: Describes the installation of SmartHome.py
uid: installation
created: 2011-04-07T21:24:51+0200
changed: 2011-04-07T21:24:51+0200
type: page
category: Installation
---

Requirements
============

System
------

* OS: Any Linux or Unix System should be fine. We are running SmartHome.py on Ubuntu 12.04 (amd64) and on an appliance with an outdated debian. So your installation commands may differ from this guide.
* NTP: You should really run a NTP daemon. <code>apt-get install openntpd</code>

Python
------
Python 2.6 and 2.7 is tested. 3.x could have problems.

The base system needs two modules:
<code>apt-get install python-configobj python-dateutil</code>

If you want to use sunset/sunrise triggers, you have to install pyephem as well.
<pre># apt-get install python-setuptools python-dev
# easy_install pyephem</pre>

### User
You may want to create an separate user to run SmartHome.py. <code>adduser smarthome</code>

# Installation

## Stable Release

### Download
At [https://github.com/mknx/smarthome/downloads](https://github.com/mknx/smarthome/downloads) you could download the latest stable version.

### Install
<pre>$ cd /
$ sudo tar --owner=smarthome xvzf path-to-tgz/smarthome-X.X.tgz
</pre>
Now everything is extracted to <code>/usr/local/smarthome/</code>.

# Structure
Within <code>/usr/local/smarthome/</code> is the following structure:

 * bin/: contains <code>smarthome.py</code>
 * dev/ developer files
 * etc/: should contain the basic configuration files (smarthome.conf, plugin.conf, logic.conf)
 * examples/: contain some example files for the configaration and the visu plugin
 * items/: should contain one or more item configuration files.
 * lib/: contains the core libraries of SmartHome.py
 * logics/: should contain your logic scripts
 * plugins/: contains the available plugins
 * tools/: contains little programms helping to maintain SmartHome.py
 * var/log/ contains the logfiles

Confguration
============
[There is a dedicated page for the configuration.](/smarthome/config)

Plugins
=======
Every [plugin](/smarthome/plugins/) has it's own installation section.

Running SmartHome.py
====================
You could run SmartHome.py (`/usr/local/smarthome/bin/smarthome.py`) with different arguments.

* `--start` or 'None'
* `--stop`
* `--debug` or `-d`: set the log level to debug
* `--no-daemon` or `-n`: run as foreground process, setting the loglevel to debug
* `--help` or `-h`: to show the options
