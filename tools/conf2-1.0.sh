#!/bin/sh
#

for CONF in items/*.conf etc/*.conf; do
    sed -i.bak \
            -e '/crontab *=/s/ *| */ | /g' \
            -e '/crontab\|eval *=\|sv_widget/!s/, */ | /g' \
            -e "/\[\|filename/s/'//g" \
            -e '/sv_widget/s/" *, *"/" | "/g' \
            -e '/sv_widget/s/"//g' \
            -e "/tz *=/s/'//g" \
            -e '/knx_dpt/s/4002/4.002/g' \
            -e '/knx_dpt/s/5001/5.001/g' \
            -e '/knx_dpt/s/16000/16/g' \
            -e '/knx_dpt/s/16001/16.001/g' \
            -e '/eval *=/s/"//g' $CONF
done
