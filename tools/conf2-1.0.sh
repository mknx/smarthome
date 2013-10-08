#!/bin/sh
#

for CONF in items/*.conf etc/*.conf; do
    sed -i.bak \
            -e '/crontab *=/s/ *| */ | /g' \
            -e '/crontab\|eval *=\|sv_widget/!s/, */ | /g' \
            -e "/\[\|filename/s/'//g" \
            -e '/sv_widget/s/" *, *"/" | "/g' \
            -e '/sv_widget/s/"//g' \
            -e '/eval *=/s/"//g' $CONF
done
