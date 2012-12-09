#!/bin/sh
#

VERSION=0

JS=/usr/local/smarthome/examples/visu/js/smarthome
cat $JS.js | grep -v 'console.log' > $JS.tmp.js
java -jar /usr/local/smarthome/dev/yuicompressor-*.jar $JS.tmp.js -o $JS.min.js --charset utf-8
rm -f $JS.tmp.js

