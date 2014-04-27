This is the subproject 'plugin.sonos' for the Smarthome.py framework (https://github.com/mknx/smarthome).
The plugin is designed to control the sonos speakers in connection with the sonos server.


##Release
  v0.7    2014-04-27

    -- version string added
    -- changed subscription method from own thread to internal scheduler function
    -- thread stable change of sonos values added
    -- new command:
        -   status [readonly] (Is the speaker online / offline, should be updated within 20sec)
        -   max_volume [read/write] (set maximum volume for the speaker. This setting will be ignored, if play_tts or
            play_snippet are used.
    -- new functions:
        -   get_favorite_radiostations()    Gets favorite radio stations from sonos library
        -   version                         Just the version of the current plugin

  v0.6    2014-03-29

    -- new structure for play_tts and play_snippet items
        - it's now possible to set the volume and language (play_tts) dynamically
        (e.g sh.sonos.play_tts.volume(20))

  v0.5    2014-03-26

    -- Google Text-To-Speech support added
    -- new commands:
        -   play_tts (play any text through Google TTS API)
    -- broken_pipe bugfix


##Requirements:

  sonos_broker server v0.1.2
  (https://github.com/pfischi/shSonos)

  smarthome.py


##Integration in Smarthome.py

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

    [[max_volume]]
        type = num
        value = -1
        enforce_updates = True
        visu_acl = rw
        sonos_recv = max_volume
        sonos_send = max_volume

        #This setting will be ignored, if play_tts or 'play_snippet' are used.
        #Unset max_volume with value -1
_
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
        type = str                  #x-file-cifs://192.168.0.10/music/snippets/welcome.mp3
        enforce_updates = True
        sonos_send = play_snippet

        [[[volume]]
            type = num
            value = -1              #-1: use current volume for tts snippet

    [[play_tts]]
        type = str                  #text is truncated to 100 chars
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

    [[status]]
        type = bool
        sonos_recv = status

  To get your sonos speaker id, type this command in your browser (while sonos server running):

    http://<sonos_server_ip:port>/client/list


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

