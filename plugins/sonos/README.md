This is the subproject 'plugin.sonos' for the Smarthome.py framework (https://github.com/mknx/smarthome).
The plugin is designed to control the sonos speakers in connection with the sonos server.


0. Release
-----------------------------

  v0.4    2014-03-08

    -- audio snippet integration
    -- many many code improvements
    -- JSON format, less network traffic
    -- easier to configure sonos speaker in conf-file
    -- better radio integration
    -- new commands:
        -   track_uri [readonly] (can be used for command 'play_uri)
        -   track_album_art [readonly] (track album url to show it in the visu)
        -   radio_station [readonly] (if radio, name of radio station)
        -   radio_show [readonly] (if radio, name of current radio station)
        -   playlist_position [readonly] (current track position in playlist)
        -   play_snippet (plays a audio snippet. If a track / radio stream is active, the current track stops,
            the audio snippets will be played. After the snippet is finished, the last play track is resumed.
            The volume behaviour can be adjusted. Use the sonos_volume attribute within the play_snippet command
            to set a higher volume. When the snippet is finished, the volume fades to its original value.
        -   uid [readonly] (sonos speaker uid)
        -   ip [readonly] (sonos speaker ip)
        -   model [readonly] (sonos seaker model)
        -   zone_name [readonly] (zone name where the speaker is currently located)
        -   zone_icon [readonly] (zone icon)
        -   serial_number [readonly] (sonos speaker serial number)
        -   software_version [readonly] (sonos speaker software version)
        -   hardware_version [readonly] (sonos speaker hardware version)
        -   mac_address [readonly] (sonos speaker mac address)

  v0.3.1  2014-02-18

    -- bugfix in parse_input method: '\r' was not stripped correctly
  
  v0.3    2014-02-12
    
    -- bug in thread routine 'subscribe' caused plugin not to resubscribed to sonos broker

  v0.2    2014-02-10
  
    -- command 'next' and 'previous' added

  v0.1    2014-01-28
    
    -- Initial release
    -- new commands: seek, track_position, track_duration
    -- requires sonos_broker server v0.1.2


1. Requirements:
-----------------------------

  sonos_broker server v0.1.2
  (https://github.com/pfischi/shSonos)

  smarthome.py


2. Integration in Smarthome.py
------------------------------

  Go to /usr/smarthome/etc and edit plugins.conf and add ths entry:

    [sonos]
  
      class_name = Sonos
      class_path = plugins.sonos
      broker_url = 192.168.178.31:12900               #this is the sonos server ip and port


  Go to /usr/smarthome/items
    
  Create a file named sonos.conf
  
  Edit file with this sample of mine:
  
    [sonos]
        sonos_uid = RINCON_000E58C3892E01400

    [[mute]]
        type = bool
        enforce_updates = True
        visu_acl = rw
        sonos_recv = mute
        sonos_send = mute

    [[led]]
        type = bool
        enforce_updates = True
        visu_acl = rw
        sonos_recv = led
        sonos_send = led

    [[volume]]
        type = num
        enforce_updates = True
        visu_acl = rw
        sonos_recv = volume
        sonos_send = volume

    [[stop]]
        type = bool
        enforce_updates = True
        visu_acl = rw
        sonos_recv = stop
        sonos_send = stop

    [[play]]
        type = bool
        enforce_updates = True
        visu_acl = rw
        sonos_recv = play
        sonos_send = play

    [[seek]]
        type = str
        enforce_updates = True
        visu_acl = rw
        sonos_send = seek    #use HH:mm:ss

    [[pause]]
        type = bool
        enforce_updates = True
        visu_acl = rw
        sonos_recv = pause
        sonos_send = pause

    [[next]]
        type = bool
        enforce_updates = True
        sonos_send = next

    [[previous]]
        type = bool
        enforce_updates = True
        sonos_send = previous

    [[track_title]]
        type = str
        enforce_updates = True
        sonos_recv = track_title

    [[track_duration]]
        type = str
        enforce_updates = True
        sonos_recv = track_duration

    [[track_position]]
        type = str
        enforce_updates = True
        sonos_recv = track_position

    [[track_artist]]
        type = str
        enforce_updates = True
        sonos_recv = track_artist

    [[track_uri]]
        type = str
        enforce_updates = True
        sonos_recv = track_uri

    [[track_album_art]]
        type = str
        enforce_updates = True
        sonos_recv = track_album_art

    [[playlist_position]]
        type = num
        sonos_recv = playlist_position

    [[radio_show]]
        type = str
        sonos_recv = radio_show

    [[radio_station]]
        type = str
        sonos_recv = radio_station

    [[streamtype]]
        type = str
        sonos_recv = streamtype

    [[play_uri]]
        type = str
        enforce_updates = True
        sonos_send = play_uri
        #x-file-cifs://192.168.0.10/music/Depeche Mode - Heaven.mp3

    [[play_snippet]]
        type = str
        enforce_updates = True
        sonos_send = play_snippet
        sonos_volume = <-1 - 100>   #-1: use current volume for snippet
        #x-file-cifs://192.168.0.10/music/snippets/welcome.mp3

    [[uid]]
        type = str
        sonos_recv = uid

    [[ip]]
        type = str
        sonos_recv = ip

    [[model]]
        type = str
        sonos_recv = model

    [[zone_name]]
        type = str
        sonos_recv = zone_name

    [[zone_icon]]
        type = str
        sonos_recv = zone_icon

    [[serial_number]]
        type = str
        sonos_recv = serial_number

    [[software_version]]
        type = str
        sonos_recv = software_version

    [[hardware_version]]
        type = str
        sonos_recv = hardware_version

    [[mac_address]]
        type = str
        sonos_recv = mac_address


  To get your sonos speaker id, type this command in your browser (while sonos server running):
  
    http://<sonos_server_ip:port>/client/list
      

  To run this plugin with a logic, here is my example:
    
  Go to /usr/smarthome/logics and create a self-named file (e.g. sonos.py)
  Edit this file and place your logic here:
    
    
    #!/usr/bin/env python
    #

    if sh.ow.ibutton():
        sh.sonos.mute(1)
    else:
        sh.sonos.mute(0)

    
  Last step: go to /usr/smarthome/etc and edit logics.conf
  Add a section for your logic:
    
    # logic
    [sonos_logic]
        filename = sonos.py
        watch_item = ow.ibutton
    
    
  In this small example, the sonos speaker with uid RINCON_000E58D5892E11230 is muted when the iButton is connected
  to an iButton Probe.
    
