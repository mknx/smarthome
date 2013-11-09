---
title: ComfoAir
layout: default
summary: Plugin to control a Zehnder ComfoAir (based on wiregate-plugin from SWISS)
---
# Requirements

This plugin has no requirements or dependencies.

# Configuration

## plugin.conf

<pre>
[comfoAir]
	class_name = comfoAir
	class_path = plugins.comfoair
	serialport = /dev/ttyUSB0
	#update_time = 300 #default=300

</pre>

This plugin needs an serial port attribute and you could specify a update_teime attribute which differs from the default '300'.

## items.conf

List and describe the possible item attributes.

### my_attr

Description of the attribute...

### my_attr2

### Example

Please provide an item configuration with every attribute and usefull settings.

<pre>
[[[Lueftung]]]
	name = Lueftung
	sv_page = room
	sv_img = scene_livingroom.png
	[[[[Daten]]]]
		visu = yes
		[[[[[Allgemein]]]]]
			name = Allgemein
			[[[[[[FilterStunden]]]]]]
				name = FilterStunden
				type = num
				comfoAir_listen = KEY_StundenFilter
				visu = yes
			[[[[[[Badschalter]]]]]]
				name = Badschalter
				type = num
				comfoAir_listen = KEY_Badschalter
				visu = yes
			[[[[[[BypassStatus]]]]]]
				name = BypassStatus
				type = num
				comfoAir_listen = KEY_BypassZustand
				visu = yes
		[[[[[Temperaturen]]]]]
			name = Temperaturen
			[[[[[[SetKomforttemperatur]]]]]]
				name = SetKomforttemperatur
				type = num
				comfoAir_send = KEY_Komforttemperatur
				visu = yes
				value = 22
			[[[[[[AktuellKomforttemperatur]]]]]]
				name = Komforttemperatur
				type = num
				comfoAir_listen = KEY_Komforttemp
				visu = yes
			[[[[[[Aussentemperatur]]]]]]
				name = Aussen
				type = num
				comfoAir_listen = KEY_Aussentemp
				visu = yes
			[[[[[[Zulufttemperatur]]]]]]
				name = Zuluft
				type = num
				comfoAir_listen = KEY_Zulufttemp
				visu = yes
			[[[[[[Ablufttemperatur]]]]]]
				name = Abluft
				type = num
				comfoAir_listen = KEY_Ablufttemp
				visu = yes
			[[[[[[Fortlufttemperatur]]]]]]
				name = Fortluft
				type = num
				comfoAir_listen = KEY_Fortlufttemp
				visu = yes
			[[[[[[EWTTemperatur]]]]]]
				name = EWTTemperatur
				type = num
				comfoAir_listen = KEY_EWTtemp
				visu = yes
		[[[[[Ventilatoren]]]]]
			name = Ventilatoren
			[[[[[[Zuluftventilator]]]]]]
				name = Zuluftventilator
				type = num
				comfoAir_listen = KEY_Vent_Zuluft_Status
				visu = yes
			[[[[[[Abluftventilator]]]]]]
				name = Abluftventilator
				type = num
				comfoAir_listen = KEY_Vent_Abluft_Status
				visu = yes
		[[[[[Stufen]]]]]
			name = Stufen
			[[[[[[AktuelleStufe]]]]]]
				name = AktuelleStufe
				type = num
				comfoAir_listen = KEY_AktuelleStufe
				visu = yes
				enforce_updates = on
			[[[[[[StufeEins]]]]]]
				name = StufeEins
				type = num
				comfoAir_send = KEY_StufeEins
				visu = yes
				enforce_updates = on
			[[[[[[StufeZwei]]]]]]
				name = StufeZwei
				type = num
				comfoAir_send = KEY_StufeZwei
				visu = yes
				enforce_updates = on
			[[[[[[StufeDrei]]]]]]
				name = StufeDrei
				type = num
				comfoAir_send = KEY_StufeDrei
				visu = yes
				enforce_updates = on
			[[[[[[StufeAbwesend]]]]]]
				name = StufeAbwesend
				type = num
				comfoAir_send = KEY_StufeAbwesend
				visu = yes
				enforce_updates = on
</pre>

## logic.conf
Currently there is no logic configuration for this plugin.


# Methodes
Currently there are no functions offered from this plugin.
