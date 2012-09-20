---
title: Asterisk Plugin
layout: default
summary: A UDP Plugin to send and receive UDP Messages and trigger logics.
created: 2011-08-08T20:58:06+0200
changed: 2011-08-08T20:58:06+0200
tags:
- Plugin
- Asterisk
---


Requirements
============
You need a running asterisk daemon with a configured Asterisk Manager Interface (AMI). In the manager.config you have to enable at least: <code>read = call,user</code> and `write = call`.
In misc/asterisk you could find some configuration files from my asterisk setup to guide you.

Configuration
=============

## plugin.conf

You have to provide the username and password of the AMI and you could specify a differnt IP and port address.

<pre>
['ast']
    class_name = Asterisk
    class_path = plugins.asterisk
    username = admin
    password = secret
    host = 127.0.0.1 # default
    port = 5038 # default
</pre>

## smarthome.conf

### ast_dev

You could specify the `ast_dev` attribute to an bool item in your smarthome.conf. The argument could be a number or string and corrospond to your asterisk device configuration.
E.g. <code>2222</code> for the following device in your asterisk sip.conf:
<pre>[2222]
secret=very
context=internal
</pre>

And in your smarthome.conf:
<pre>
['office']
    [['fon']]
        type = bool
        ast_dev = 2222
</pre>

If you call the '2222' sip client or making a call from it, <code>office.fon</code> will be set to True. If you finish the call it will be set to False.

logic.conf
----------
You could specify the `ast_userevent` keyword to every logic in your logic.conf.
<pre>
['logic1']
    ast_userevent = Call

['logic2']
    ast_userevent = Action
</pre>

In your asterisk extensions.conf `exten => _X.,n,UserEvent(Call,Source: ${CALLERID(num)},Value: ${CALLERID(name)})` would trigger 'logic1' every time you send this UserEvent.


Functions
=========

call(source, dest, context, callerid=None)
------------------------------------------
`sh.ast.call('SIP/200', '240', 'door')` would initate a call from the SIP extention '200' to the extention '240' with the 'door' context. If you want you could provied a callerid for the call.

db_write(key, value)
--------------------
<code>sh.ast.db_write('dnd/office', 1)</code> would set the asterisk db entry 'dnd/office' to 1.

db_read(key)
------------
<code>dnd = sh.ast.db_read('dnd/office')</code> would set 'dnd' to the value of the asterisk db entry 'dnd/office'.

mailbox_count(mailbox, context='default')
-----------------------------------------
<code>mbc = sh.ast.mailbox_count('2222')</code> would set 'mbc' to a tuple (old_messages, new_messages).

## hangup(device)
`sh.ast.hangup('30')` would close all connections from or to the device '30'.

