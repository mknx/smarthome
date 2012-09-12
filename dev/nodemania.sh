#!/bin/sh
#

INDEX=0
CONF=/usr/local/smarthome/etc/smarthome.conf

echo "[nodemania]" >> $CONF
while [ $INDEX -le 1000 ] ; do
    echo "  [[node$INDEX]]" >> $CONF
    echo "    type = num" >> $CONF
    echo "    visu = div" >> $CONF
    INDEX=$(($INDEX+1))
done
