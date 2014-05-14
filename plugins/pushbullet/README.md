# Pushbullet  
  
## Requirements  
### Python libraries  
* requests - [http://docs.python-requests.org/en/latest/](http://docs.python-requests.org/en/latest/ "http://docs.python-requests.org/en/latest/")
  
### Other  
* Pushbullet API-KEY - get it from [__here__](http://www.pushbullet.com/ "http://www.pushbullet.com") for free  
  
---
## Configuration  
  
### plugin.conf  
  
<pre>
[pushbullet]
    class_name = Pushbullet
    class_path = plugins.pushbullet
#	deviceid = <your-default-device-id>
#   apikey = <your-api-key>
</pre>
  
Description of the attributes:
  
* __apikey__: set api-key globally so you do not have to set it in the function calls  
* __deviceid__: set deviceid globally so it will be used as defaul target, you can override this on each call  
    
---  
## Functions
  
*Pass a 'deviceid' if no set globally or if you want to send to another device.*  
*Add 'apikey' if not set globally.*  
  
### sh.pushbullet.note(title, body [, deviceid] [, apikey])
Send a note to your device.  
  
#### Parameters  
* __title__: The title of the note  
* __body__:  The note's body 
  
#### Example
<pre>
#send simple note to default device
sh.pushbullet.note("Note to myself.", "Call my mother.")
</pre>
--- 
### sh.pushbullet.link(title, url [, deviceid] [, apikey])
Send a link to your device.  
  
#### Parameters:  
* __title__: The title of the page linked to
* __url__:  The link url 
  
#### Example
<pre>
# send link to device with id: x28d7AJFx13
sh.pushbullet.link("Pushbullet", "http://www.pushbullet.com", "x28d7AJFx13")
</pre>
--- 
### sh.pushbullet.address(name, address [, deviceid] [, apikey])
Send a address to your device.  
  
#### Parameters:  
* __name__: The name of the place at the address  
* __address__:  The full address or Google Maps query  
  
#### Example
<pre>
# send address of "Eifel Tower" to default device
sh.pushbullet.address("Eifel Tower", "https://www.google.com/maps/place/Eiffelturm/@48.85837,2.294481,17z/data=!3m1!4b1!4m2!3m1!1s0x47e66e2964e34e2d:0x8ddca9ee380ef7e0")
</pre>
---
### sh.pushbullet.list(title, title [, deviceid] [, apikey])
Send a list of items to your device.  
  
#### Parameters:  
* __title__: The title of the list  
* __items__:  The list items
  
#### Example
<pre>
#send a shopping list to default device
sh.pushbullet.list("Shopping list", ["Milk", "Eggs", "Salt"])
</pre>
---
### sh.pushbullet.file(filepath [, deviceid] [, apikey])
Send a file to your device.  
  
#### Parameters:  
* __filepath__: absolute path to the file to push  
  
#### Example
<pre>
#send smarthome log file to default device
sh.pushbullet.note("/usr/local/smarthome/var/log/smarthome.log")
</pre>