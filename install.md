---
title: Installation
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

* OS: Any Linux or Unix System should be fine. I'm running SmartHome.py on Ubuntu 10.04 (amd64). So your installation commands may differ from this guide.
* NTP: You should really run a NTP daemon. <code>apt-get install openntpd</code>

Python
------
Python 2.6 is tested, 2.7 should run, but I'm expecting problems with 3.x.

The base system needs two modules:
<code>apt-get install python-configobj python-dateutil</code>

If you want to use sunset/sunrise triggers, you have to install pyephem as well.
<code>apt-get install python-setuptools python-dev</code>
<code>easy_install pyephem</code>

### User
You may want to create an separate user to run SmartHome.py. <code>adduser smarthome</code>

Download
========
At [http://sourceforge.net/projects/smarthome/files/](http://sourceforge.net/projects/smarthome/files/) you could download the latest version.

Install
=======
<pre>$ cd /
$ sudo tar --owner=smarthome xvzf path-to-tgz/smarthome-X.X.tgz
</pre>
Now everything is extracted to <code>/usr/local/smarthome/</code>.

Structure
---------
Within <code>/usr/local/smarthome/</code> is the following structure:

 * bin/: contains scripts like <code>smarthome.py</code>
 * etc/: should contain the configuration files
 * lib/: contains the core functions of SmartHome.py
 * logic/ should contain your logic scripts
 * plugins/ contains the available plugins
 * var/log/ contains the logfiles

Confguration
============
[There is a dedicated page for the configuration.](/config/)

Plugins
=======
Every [plugin](/plugins/) has it's own  installation section.

Running SmartHome.py
====================
You could run SmartHome.py (`/usr/local/smarthome/bin/smarthome.py`) with different arguments.

* `--start` or 'None'
* `--stop`
* `--restart` or `-r`: to restart the application
* `--debug` or `-d`: set the log level to debug
* `--no-daemon` or `-n`: run as foreground process, setting the loglevel to debug
* `--help` or `-h`: to show the options

