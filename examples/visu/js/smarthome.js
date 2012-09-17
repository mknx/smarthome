// vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
//########################################################################
// Copyright 2012 KNX-User-Forum e.V.            http://knx-user-forum.de/
//########################################################################
//  This file is part of SmartHome.py.   http://smarthome.sourceforge.net/
//
//  SmartHome.py is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
//
//  SmartHome.py is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
//########################################################################

var shVersion = 0.64;
var shWS = false; // WebSocket
var shLock = false;
var shURL = '';
var shBuffer = {};
var shOpt = {};
var shMonitor = [];

// little helper functions
Array.prototype.diff = function(a) {
        return this.filter(function(i) {return !(a.indexOf(i) > -1);});
};
function shUnique(arr) {
    arr = arr.sort();
    var ret = [arr[0]];
    for (var i = 1; i < arr.length; i++) {
        if (arr[i-1] !== arr[i]) {
            ret.push(arr[i]);
        }
    }
    return ret;
};

function shInit(url) {
    // Init WebSocket
    shURL = url;
    shWsInit();
    setTimeout(shWSCheckInit , 2000);
    $(window).unload(function(){ shWS.close(); shWS = null });
    // Adding Listeners
    $(document).on( "pagecreate", function(){
        shPageCreate();
    });
    $(document).on( "pageinit", function(){
        shPageInit();
    });
    $(document).on( "pageshow", function(){
        shPageShow();
    });
    $(document).on("click", 'a[data-logic]', function() { // Button
        shTriggerLogic(this);
    });
    $(document).on("click", 'img[data-logic]', function() { // Logic-Trigger Button
        shTriggerLogic(this);
    });
    $(document).on("click", 'img.switch[data-sh]', function() { // Switch Button
        shSwitchButton(this);
    });
    $(document).on("click", 'img.set[data-sh]', function() { // Send Button
        shSendFix(this);
    });
    $(document).on("vmousedown", 'img.push[data-sh]', function(event) { // Push Button
        event.preventDefault();
        shSendPush(this, true);
    });
    $(document).on("vmouseup", 'img.push[data-sh]', function() { // Push Button
        shSendPush(this, false);
    });
    $(document).on("change", 'select[data-sh]', function() { // Select
        shSendSelect(this);
    });
    $(document).on("change", 'input[data-sh][data-type="range"]', function() { // Slider
        shSendNum(this);
    });
    $(document).on("change", 'input[data-sh][type="time"]', function() { // Slider
        shSendVal(this);
    });
    $(document).on("change", 'input[data-sh]:text', function() { // Text
        shSendVal(this);
    });
    $(document).on("change", 'textarea[data-sh]', function() { // Textarea
        shSendVal(this);
    });
    $(document).on("change", 'input[data-sh][type="checkbox"]', function() { // Checkbox
        shSendCheckbox(this);
    });
    $(document).on("change", 'input[data-sh][type="radio"]', function() { // Radio
        shSendRadio(this);
    });
};

function shWsInit() {
    shWS = new WebSocket(shURL);
    shWS.onopen = function(){
        shSend([ 'SmartHome.py', 1 ]);
        shSend([ 'monitor', shMonitor ]);
        $('.ui-dialog').dialog('close');
    };
    shWS.onmessage = function(event) {
        var path, val;
        var data = JSON.parse(event.data);
        console.log("receiving data: " + event.data);
        command = data[0];
        delete data[0];
        switch(command) {
            case 'item':
                for (var i = 1; i < data.length; i++) {
                    path = data[i][0];
                    val = data[i][1];
                    if ( data[i].length > 2 ) {
                        shOpt[path] = data[i][2];
                    };
                    shLock = path;
                    shBuffer[path] = val;
                    shUpdateItem(path, val);
                    shLock = false;
                };
                break;
            case 'dialog':
                shDialog(data[1][0], data[1][1]);
                break;
        };
    };
    shWS.onerror = function(error){
        console.log('Websocket error: ' + error);
    };
    shWS.onclose = function(){
        shDialog('Network error', 'Could not connect to the backend!');
    };
};

function shWSCheckInit() {
    setInterval(shWSCheck, 2000);
};
function shWSCheck() {
    // check connection
    // if connection is lost try to reconnect
    if ( shWS.readyState > 1 ){ shWsInit(); };
};

// page handling //
function shPageCreate() {
    console.log('Page Create');
    shMonitor = $("[data-sh]").map(function() { if (this.tagName != 'A') { return $(this).attr("data-sh"); }}).get();
    shMonitor = shUnique(shMonitor);
    shSend(['monitor', shMonitor]);
    // create dialog page
    if ($('#shDialog').length == 0) {
        $.mobile.pageContainer.append('<div data-role="page" id="shDialog"><div data-role="header"><h1 id="shDialogHeader"></h1></div><div data-role="content"><div id="shDialogContent"></div></div></div>');
    }
};

function shPageInit() {
    // update page items
    console.log('PageInit');
    for (path in shBuffer) {
        if (shMonitor.indexOf(path) != -1) { // if path in shMonitor
            shUpdateItem(path, shBuffer[path]);
        } else {
            delete shBuffer[path];
            delete shOpt[path];
        };
    };
};

function shPageShow() {
    // check connection
    if ( shWS.readyState > 1 ){ // Socket closed
        shWsInit();
    };
};

// outgoing data //
function shSend(data){
    console.log("Websocket state: " + shWS.readyState);
    if ( shWS.readyState > 1 ){
        shWsInit();
    };
    if ( shWS.readyState == 1 ) {
        console.log('sending data: ' + data);
        shWS.send(unescape(encodeURIComponent(JSON.stringify(data))));
        return true;
    } else {
        console.log('Websocket (' + shURL + ') not available. Could not send data.');
        return false;
    };
};

function shBufferUpdate(path, val, src){
    console.log(path + " changed to: " + val + " (" + typeof(val) + ")");
    if ( path in shBuffer) {
        if (shBuffer[path] !== val){
            shBuffer[path] = val;
            shSend([ 'item', [ path, val ]]);
            shUpdateItem(path, val, src);
        };
    };
};

function shTriggerLogic(obj){
    shSend(['logic', [ $(obj).attr('data-logic'), $(obj).attr('value') ]]);
};

function shSwitchButton(obj){
    var path = $(obj).attr('data-sh');
    var val = true;
    if ( String($(obj).val()) == '1') {
        val = false;
    };
    shBufferUpdate(path, val, obj);
    $(obj).val(Number(val));
    $(obj).attr("src", shOpt[path][Number(val)]);
};

function shSendSelect(obj){
    var path = $(obj).attr('data-sh');
    if ( path == shLock) { return; };
    var val;
    if ($(obj).attr('data-role') == 'slider') { // toggle
        val = Boolean($(obj)[0].selectedIndex)
    } else { // regular select
        val = $(obj).val();
    };
    shBufferUpdate(path, val, obj);
};

function shSendFix(obj){
    var path = $(obj).attr('data-sh');
    if ( path == shLock) { return; };
    var val = Number($(obj).attr("value"));
    shBufferUpdate(path, val, obj);
};

function shSendPush(obj, val){
    var path = $(obj).attr('data-sh');
    if ( path == shLock) { return; };
    shBufferUpdate(path, val, obj);
};

function shSendVal(obj){
    var path = $(obj).attr('data-sh');
    if ( path == shLock) { return; };
    var val = $(obj).val();
    shBufferUpdate(path, val, obj);
};

function shSendNum(obj){
    var path = $(obj).attr('data-sh');
    if ( path == shLock) { return; };
    var val = Number($(obj).val());
    shBufferUpdate(path, val, obj);
};

function shSendRadio(obj){
    var path = $(obj).attr('data-sh');
    if ( path == shLock) { return; };
    var val = $(obj).val();
    shBufferUpdate(path, val, obj);
};

function shSendCheckbox(obj){
    var path = $(obj).attr('data-sh');
    if ( path == shLock) { return; };
    var val = $(obj).prop('checked');
    shBufferUpdate(path, val, obj);
};

// Incoming Data //

function shUpdateItem(path, val, src) {
    var obj = $('[data-sh="' + path + '"]');
    if (obj.length == 0) {
        console.log("unknown id: "+ path);
        return;
    }
    //console.log('update found ' + obj.length + ' elements');
    $(obj).filter('[type!="radio"]').each(function() { // ignoring radio - see below
        element = this.tagName;
        if (src == this ) { // ignore source
            return true;
        };
        switch(element) {
            case 'DIV':
                $(this).html(val);
                break;
            case 'SPAN':
                $(this).html(val);
                break;
            case 'TEXTAREA':
                $(this).val(val);
                break;
            case 'SELECT':
                updateSelect(this, val);
                break;
            case 'INPUT':
                updateInput(this, val);
                break;
            case 'IMG':
                if ( $(this).attr("class") != "set" ){
                    if ( path in shOpt ){
                        $(this).attr("src", shOpt[path][Number(val)]);
                        $(this).val(Number(val));
                    } else {
                        $(this).attr("src", val);
                    };
                };
                break;
            default:
                console.log("unknown element: " + element);
                break;
        };
    });
    // special care for input radio
    var radio = $(obj).filter('[type="radio"]')
    radio.removeAttr('checked');
    radio.filter("[value='" + val + "']").attr("checked","checked");
    try {
        $(radio).checkboxradio('refresh');
    } catch (e) {};
};

function updateSelect(obj, val) {
    if ($(obj).attr('data-role') == 'slider') { // toggle
        obj.selectedIndex = val;
        try {
            $(obj).slider("refresh");
        } catch (e) {};

    } else { // select
        $(obj).val(val);
        try {
            $(obj).selectmenu("refresh");
        } catch (e) {};
    };
};

function updateInput(obj, val) {
    var type = $(obj).attr('type');
    if (type == undefined) {
        type = $(obj).attr('data-type');
    }
    //console.log('type: '+ type);
    switch(type) {
        case 'text': // regular text
            $(obj).val(val);
            break;
        case 'range': // slider
            try {
                $(obj).val(val).slider("refresh");
            } catch (e) {};
            break;
        case 'number': // slider
            try {
                $(obj).val(val).slider("refresh");
            } catch (e) {};
            break;
        case 'checkbox': // checkbox
            try {
                $(obj).attr("checked",val).checkboxradio("refresh");
            } catch (e) {};
            break;
        case 'image': // image
            $(obj).val(Number(val));
            $(obj).attr("src", shOpt['example.toggle'][Number(val)]); // XXX
            break;
        case 'time': // time
            $(obj).val(val);
            break;
        default:
            console.log("unknown type: " + type);
            break;
    };
};

function shDialog(header, content){
    $('#shDialogHeader').html(header);
    $('#shDialogContent').html(content);
    //$('#shDialog').trigger('create');
    $.mobile.changePage('#shDialog', {transition: 'pop', role: 'dialog'} );
};
