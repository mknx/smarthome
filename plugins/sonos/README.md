This is the subproject 'plugin.sonos' for the Smarthome.py framework (https://github.com/mknx/smarthome).
The plugin is designed to control the sonos speakers in connection with the sonos server.


##Release

  v1.0  2014-07-08
    
    --  parameter 'broker_url' in plugin configuration now optional
        -   if value is not set, the current system ip and the default broker port (12900) will be assumed
        -   manually add  this parameter, if the sonos broker is not running on the same system
    --  added optional parameter 'refresh' to plugin configuration (edit /usr/smarthome/etc/plugin.conf)
        -   this parameter specifies, how often the broker is requested for sonos status updates (default: 120s)
        -   Normally, all changes to the speakers will be triggered automatically to the plugin.
    --  bug: if a sonos speaker was reported by the broker but was not declared in sonos.conf, an error occured
    
  
  v0.9    2014-06-15
    
    --  changed values play, pause, stop, led back to normal values (no toggle values). 
        It makes logics easier to write.
    --  new commands:
        -   bass [read/write]: sets the bass for a speaker (value between -10 and 10)
        -   treble [read/write]: sets the treble value for a speaker (value between -10 and 10)
        -   loudness [read/write]: sets the loudness compensation for a speaker (value 0|1)
        -   playmode [read/write] sets the playmode for a sonos speaker 
            values: 'normal', 'shuffle_norepeat', 'shuffle', 'repeat_all'
    
  v0.8.1  2014-06-07
    
    --  bugfixes in some command processing

  v0.8    2014-06-06

    --  changed some values in sonos plugin config to 'foo' (commands without parameter like play, pause, next etc),
        updated usage of 'enforce_updates = True' for some values,
        !! please update / replace  your sonos config file !!
    --  new command:
        -   join [write]: joins a speaker to another speaker (uid as parameter)
        -   unjoin [write]: removes the speaker from current group
        -   partymode [write]: group all speaker to one zone (partymode)
        -   volume_up [write]: increases the volume (+2)
        -   volume_down [write]: decreases the volume (-2)
    --  new value:
        -   additional_zone_members [read]: additional zone members if speaker is in a group
    --  changed commands: pause, play, stop, led, mute now toggle commands
    --  documentation: 'Group behaviour' added

  v0.7    2014-04-27

    --  version string added
    --  changed subscription method from own thread to internal scheduler function
    --  thread stable change of sonos values added
    --  new command:
        -   status [readonly] (Is the speaker online / offline, should be updated within 20sec)
        -   max_volume [read/write] (set maximum volume for the speaker. This setting will be ignored, if play_tts or
            play_snippet are used.
    --  new functions:
        -   get_favorite_radiostations()    Gets favorite radio stations from sonos library
        -   version                         Just the version of the current plugin


##Requirements:

  sonos_broker server v0.2
  (https://github.com/pfischi/shSonos)

  smarthome.py


##Integration in Smarthome.py

Go to /usr/smarthome/etc and edit plugins.conf and add ths entry:

    [sonos]
      class_name = Sonos
      class_path = plugins.sonos
      #broker_url = 192.168.178.31:12900        #optional
      #refresh = 120                            #optional
      
You dont't have to set the ***broker_url*** variable. If value is not set, the current system ip and the default 
broker port (12900) will be assumed. Add this this parameter manually, if the sonos broker is not running on 
the same system.
The ***refresh*** parameter specifies, how often the broker is requested for sonos status updates (default: 120s).
Normally, all changes to the speakers will be triggered automatically to the plugin.

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

    [[volume_up]]
        type = foo
        visu_acl = rw
        enforce_updates = True
        sonos_send = volume_up

    [[volume_down]]
        type = foo
        visu_acl = rw
        enforce_updates = True
        sonos_send = volume_down

    [[max_volume]]
        type = num
        value = -1
        enforce_updates = True
        visu_acl = rw
        sonos_recv = max_volume
        sonos_send = max_volume

        #This setting will be ignored, if play_tts or 'play_snippet' are used.
        #Unset max_volume with value -1

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
        type = foo
        enforce_updates = True
        visu_acl = rw
        sonos_send = next

    [[previous]]
        type = foo
        visu_acl = rw
        enforce_updates = True
        sonos_send = previous

    [[track_title]]
        type = str
        visu_acl = rw
        sonos_recv = track_title

    [[track_duration]]
        type = str
        visu_acl = rw
        sonos_recv = track_duration

    [[track_position]]
        type = str
        visu_acl = rw
        sonos_recv = track_position

    [[track_artist]]
        type = str
        visu_acl = rw
        sonos_recv = track_artist

    [[track_uri]]
        type = str
        visu_acl = rw
        sonos_recv = track_uri

    [[track_album_art]]
        type = str
        visu_acl = rw
        sonos_recv = track_album_art

    [[playlist_position]]
        type = num
        visu_acl = rw
        sonos_recv = playlist_position

    [[radio_show]]
        type = str
        visu_acl = rw
        sonos_recv = radio_show

    [[radio_station]]
        type = str
        visu_acl = rw
        sonos_recv = radio_station

    [[streamtype]]
        type = str
        visu_acl = rw
        sonos_recv = streamtype

    [[play_uri]]
        type = str                  #x-file-cifs://192.168.0.10/music/Depeche Mode - Heaven.mp3
        visu_acl = rw
        enforce_updates = True
        sonos_send = play_uri

    [[play_snippet]]
        type = str                  #x-file-cifs://192.168.0.10/music/snippets/welcome.mp3
        visu_acl = rw
        enforce_updates = True
        sonos_send = play_snippet

        [[[volume]]
            type = num
            value = -1              #-1: use current volume for tts snippet

    [[play_tts]]
        type = str                  #text is truncated to 100 chars
        visu_acl = rw
        enforce_updates = True
        sonos_send = play_tts

        [[[volume]]
            type = num
            value = -1              #-1: use current volume for tts snippet

        [[[language]]]
            type = str
            value = 'de'            #(see google translate url http://translate.google.com/translate_tts?tl=en....
                                    #for more languages e.g. 'en', 'fr')
                                    #If no value is given, 'en' is used

    [[uid]]
        type = str
        visu_acl = rw
        sonos_recv = uid

    [[ip]]
        type = str
        visu_acl = rw
        sonos_recv = ip

    [[model]]
        type = str
        visu_acl = rw
        sonos_recv = model

    [[zone_name]]
        type = str
        visu_acl = rw
        sonos_recv = zone_name

    [[zone_icon]]
        type = str
        visu_acl = rw
        sonos_recv = zone_icon

    [[serial_number]]
        type = str
        visu_acl = rw
        sonos_recv = serial_number

    [[software_version]]
        type = str
        visu_acl = rw
        sonos_recv = software_version

    [[hardware_version]]
        type = str
        visu_acl = rw
        sonos_recv = hardware_version

    [[mac_address]]
        type = str
        visu_acl = rw
        sonos_recv = mac_address

    [[status]]
        type = bool
        visu_acl = rw
        sonos_recv = status

    [[join]]
        type = str              #uid from speaker to join
        visu_acl = rw
        enforce_updates = True
        sonos_send = join

    [[unjoin]]
        type = foo
        visu_acl = rw
        enforce_updates = True
        sonos_send = unjoin

    [[partymode]]
        type = foo
        visu_acl = rw
        enforce_updates = True
        sonos_send = partymode

    [[additional_zone_members]]
        type = str
        visu_acl = rw
        sonos_recv = additional_zone_members

    [[bass]]
        type = num
        enforce_updates = True
        visu_acl = rw
        sonos_recv = bass
        sonos_send = bass
    
    [[treble]]
        type = num
        enforce_updates = True
        visu_acl = rw
        sonos_recv = treble
        sonos_send = treble
        
    [[loudness]]
        type = bool
        enforce_updates = True
        visu_acl = rw
        sonos_recv = loudness
        sonos_send = loudness
    
    [[playmode]]
        type = str
        enforce_updates = True
        visu_acl = rw
        sonos_recv = playmode
        sonos_send = playmode
        
        
You can find an example config in the plugin sub-directory "examples". 


To get your sonos speaker id, type this command in your browser (while sonos server is running):
  
    http://<sonos_server_ip:port>/client/list


##Group behaviour

If one or more speakers are in the same zone, almost all commands will be passed to the master speaker. You don't
have to worry about which speaker is the zone master. Just send your command to one of the zone speaker. There are
few 'single' speaker commands like 'volume', which are passed to the specified speaker exclusively.

###Group commands

    mute
    stop
    play
    seek
    pause
    next
    previous
    play_uri
    play_snippet
    play_tts
    partymode
    playmode

###Single Speaker commands

    led
    volume
    max_volume
    join
    unjoin
    bass
    treble
    loudness

##Methods

get_favorite_radiostations(<start_item>, <max_items>)

    Get all favorite radio stations from sonos library

    start_item [optional]: item to start, starting with 0 (default: 0)
    max_items [optional]: maximum items to fetch. (default: 50)

    Parameter max_items can only be used, if start_item is set (positional argument)

    It's a good idea to check to see if the total number of favorites is greater than the amount you
    requested ('max_items'), if it is, use `start` to page through and  get the entire list of favorites.

    Response:

    JSON object, utf-8 encoded

    Example:

    {
        "favorites":
        [
            { "title": "Radio TEDDY", "uri": "x-sonosapi-stream:s80044?sid=254&flags=32" },
            { "title": "radioeins vom rbb 95.8 (Pop)", "uri": "x-sonosapi-stream:s25111?sid=254&flags=32" }
        ],
            "returned": 2,
            "total": "10"
    }

version()

    current plugin version


##smartVISU Integration

more information here: https://github.com/pfischi/shSonos/tree/develop/widget.smartvisu


##Logic examples

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