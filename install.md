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

* OS: Any Linux or Unix System should be fine. SmartHome.py is tested on Ubuntu 12.04 (amd64) and on an appliance with an outdated debian. So the specific installation commands may differ from this guide.
* NTP: A running NTP daemon is recommended:
```
# apt-get install openntpd</code>
```

Python
------
Python 2.6 and 2.7 is recommended. 3.x could have problems.

The base system needs two modules:
```
# apt-get install python-configobj python-dateutil</code>
```

Calculating of sunset/sunrise in triggers,requires installation of **pyephem** as well.
```
# apt-get install python-pip python-dev
# pip install pyephem</pre>
```

### User
A dedicated user for smarthome.py can be created: 
```
# adduser smarthome</code>
```
# Installation

## Stable Release

### Download
At [https://github.com/mknx/smarthome/tags](https://github.com/mknx/smarthome/tags) the latest stable version is availabe.

### Installation of the latest release
```
$ cd /usr/local
$ sudo tar --owner=smarthome xvzf path-to-tgz/smarthome-X.X.tgz
```
Everything is extracted to <code>/usr/local/smarthome/</code>. It is possible to use another path.

### Developement
For using the recent developer version of smarthome.py:

as root:
```
# mkdir -p /usr/local/smarthome/
# chown USER /usr/local/smarthome/
```

as USER:
```
$ cd /usr/local
$ git clone git://github.com/mknx/smarthome.git
```

To get the latest updates:
```
$ cd /usr/local/smarthome
$ git pull
```

If `smarthome.js` has been chaged, it should be copied:
```
$ cp /usr/local/smarthome/exampleis/visu/js/smarthome.* /var/www/smarthome/js/*
```


# Structure
Structure of the smarthome.py directory, e.g. <code>/usr/local/smarthome/</code>:

 * bin/: contains <code>smarthome.py</code>
 * dev/ development files
 * etc/: should contain the basic configuration files (smarthome.conf, plugin.conf, logic.conf)
 * examples/: contains some example files for the configaration and the visu plugin
 * items/: should contain one or more item configuration files.
 * lib/: contains the core libraries of SmartHome.py
 * logics/: should contain the logic scripts
 * plugins/: contains the available plugins
 * tools/: contains little programms helping to maintain SmartHome.py
 * var/log/: contains the logfiles
 * var/rrd/: contains the Round Robin Databases

#Configuration
[There is a dedicated page for the configuration.](/smarthome/config)

Plugins
=======
Every [plugin](/smarthome/plugins/) has it's own installation section.

Running SmartHome.py
====================
Arguments for running SmartHome.py (`/usr/local/smarthome/bin/smarthome.py`):

* `--start` or 'None'
* `--stop`
* `--debug` or `-d`: set the log level to debug
* `--no-daemon` or `-n`: run as foreground process, setting the loglevel to debug
* `--help` or `-h`: to show the options
