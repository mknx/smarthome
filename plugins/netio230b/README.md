---
title: NetIO230B
layout: default
summary: control power status of netio230b power distribution
---

# Requirements
## Supported Hardware

* KOUKAAM NETIO230B

# Configuration
## plugin.conf

<pre>
[netio230b0]
    class_name = NetIO230B
    class_path = plugins.netio230b
    address = 10.0.0.10
    user = username
    password = password
#   netio_id = 1
</pre>

address  : ip address of the netio230b power distribution
user     : username needed for login
password : password needed for login
netio_id : optional, set id if you want to control more than one device

## items.conf

There are two types of items in this plugin. Items to control the state of the power
distribution (control item) and items to detect an error (error item). The error item
is used to detect wether it is not possible to communicate with the device.

### netio_id

Contains the device id specified in plugin.conf. This attribute is optional for the control item.

### netio_port

Specify one of the 4 ports of the power distribution, starting with 0. This attribute must not
be set for the error item.

### Example

<pre>
# items/netio230b.conf

[someroom]
    [[control0]]
        type = bool
        netio_id = 1
        netio_port = 0

    [[control1]]
        type = bool
        netio_port = 3

    [[control2]]
        type = bool
        netio_id = 2
        netio_port = 2

    [[error1]]
        type = bool
        netio_id = 1

    [[error2]]
        type = bool
        netio_id = 1
</pre>

control0 - item to control port 0 of netio230b device with id 1
control1 - item to control port 3 of netio230b device with id 1 (default for netio_id is 1)
control2 - item to control port 2 of netio230b device with id 2
error1   - item to get error state of netio230b device with id 1
error1   - item to get error state of netio230b device with id 2

## logic.conf

The state of a port can be changed by setting the belonging item to true or false.

# Methodes

none
