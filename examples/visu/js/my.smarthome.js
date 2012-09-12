
console.log('Init SmartHome.py');
//shInit("ws://"+ location.host + ":2000/");
shInit("ws://"+ location.host + ":2121/");

// adapt default settings
$.mobile.page.prototype.options.addBackBtn= true;
$.mobile.page.prototype.options.backBtnText = "Zurück";

