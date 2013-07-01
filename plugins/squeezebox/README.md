# Requirements

A properly installed and configured Logitech Media Server is required.  

## Supported Hardware

Tested with:
* Logitech Squeezebox Radio

Should work with other Squeezebox players as well - please let me know!

# Configuration

## plugin.conf

<pre>
[squeezebox]
    class_name = Squeezebox
    class_path = plugins.squeezebox
#    host = <server>
#    port = <port>
</pre>

Description of the attributes:

* __host__: IP or hostname of the Logitech Media Server if not local
* __port__: Port number of the Logitech Media Server if not 9090

## items.conf

You can use all commands available by the telnet-interface.

For a explanation of all available commands see http://<server>:9000/html/docs/cli-api.html

Up to four identifier strings are used:
* __squeezebox_playerid__: used in the parent item to allow using <playerid> placeholder in the children
* __squeezebox_send__: used to set the item
* __squeezebox_recv__: used to get notifications when running
* __squeezebox_init__: used to query the item at start-up
 
Fields:
* __<playerid>__: gets replaced by the player-id set in the parent item
* __{}__: the value of the item is written to this placeholder (don't use if a fixed/no value is required)

You should verify all your commands manually by using the telnet-interface on port 9090.
<pre>
telnet <server>:<port>
listen 1
<playerid> name ?
...
</pre>

<pre>
[Squeezebox]
  squeezebox_playerid = your-players-ID-in-here

  [[Name]]
    type = str
    visu = yes
    squeezebox_send = <playerid> name {}   
    squeezebox_recv = <playerid> name    
  [[IP]]
    type = str
    visu = yes
    squeezebox_recv = player ip <playerid>   
  [[Signal_Strength]]
    type = num
    visu = yes
    squeezebox_recv = <playerid> signalstrength    

  [[Power]]
    type = bool
    visu = yes
    squeezebox_send = <playerid> power {}
    squeezebox_recv = <playerid> prefset server power
    squeezebox_init = <playerid> power    
    
  [[Mute]]
    type = bool
    visu = yes
    squeezebox_send = <playerid> mixer muting {}
    squeezebox_recv = <playerid> prefset server mute
    squeezebox_init = <playerid> mixer muting
  [[Volume]]
    type = num
    visu = yes
    squeezebox_send = <playerid> mixer volume {}
    squeezebox_recv = <playerid> prefset server volume
    squeezebox_init = <playerid> mixer volume    
  [[Volume_Up]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> button volup
  [[Volume_Down]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> button voldown
    
  [[Play]]
    type = bool
    visu = yes
    squeezebox_send = <playerid> play
    squeezebox_recv = <playerid> play
    squeezebox_init = <playerid> mode
  [[Stop]]
    type = bool
    visu = yes
    squeezebox_send = <playerid> stop
    squeezebox_recv = <playerid> stop
    squeezebox_init = <playerid> mode
  [[Pause]]
    type = bool
    visu = yes
    squeezebox_send = <playerid> pause {}
    squeezebox_recv = <playerid> pause
    squeezebox_init = <playerid> mode
    
  [[Current_Title]]
    type = str
    visu = yes
    squeezebox_recv = <playerid> playlist newsong
    squeezebox_init = <playerid> current_title

  [[Genre]]
    type = str
    visu = yes
    squeezebox_recv = <playerid> genre
  [[Artist]]
    type = str
    visu = yes
    squeezebox_recv = <playerid> artist
  [[Album]]
    type = str
    visu = yes
    squeezebox_recv = <playerid> album
  [[Title]]
    type = str
    visu = yes
    squeezebox_recv = <playerid> title
  [[Duration]]
    type = num
    visu = yes
    squeezebox_recv = <playerid> duration

  [[Time]]
    type = num
    visu = yes
    squeezebox_send = <playerid> time {}
    squeezebox_recv = <playerid> time

  [[Playlist_Index]]
    type = num
    visu = yes
    squeezebox_send = <playerid> playlist index {}
    squeezebox_recv = <playerid> playlist index
  [[Playlist_Forward]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist index +1
  [[Playlist_Backward]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist index -1
    
  [[Playlist_Name]]
    type = str
    visu = yes
    squeezebox_send = <playerid> playlist name {}
    squeezebox_recv = <playerid> playlist name
  [[Playlist_Save]]
    type = str
    visu = yes
    squeezebox_send = <playerid> playlist save {}   
  [[Playlist_Load]]
    type = str
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist load {}
  [[Playlist_Load_Internetradio]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist load file:///home/robert/playlists/Internetradio.m3u
    
  [[Repeat]]
    type = num
    visu = yes
    squeezebox_send = <playerid> playlist repeat {}
    squeezebox_recv = <playerid> playlist repeat    
  [[Repeat_Song]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist repeat 1
  [[Repeat_Playlist]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist repeat 2
  [[Repeat_None]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist repeat 0
    
  [[Shuffle]]
    type = num
    visu = yes
    squeezebox_send = <playerid> playlist shuffle {}
    squeezebox_recv = <playerid> playlist shuffle    
  [[Shuffle_By_Song]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist shuffle 1
  [[Shuffle_By_Album]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist shuffle 2
  [[Shuffle_None]]
    type = bool
    enforce_updates = true
    visu = yes
    squeezebox_send = <playerid> playlist shuffle 0 
</pre>
