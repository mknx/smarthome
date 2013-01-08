
console.log('Init SmartHome.py v' + shVersion)
shInit("ws://"+ location.host + ":2121/");

// adapt default settings
$.mobile.page.prototype.options.addBackBtn= true;
$.mobile.page.prototype.options.backBtnText = "Zurück";

