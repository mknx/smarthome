#!/bin/sh
### BEGIN INIT INFO
# Provides:          smarthome
# Required-Start:    $syslog $network
# Required-Stop:     $syslog $network
# Should-Start:      eibd owserver
# Should-Stop:       eibd owserver
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start SmartHome.py
### END INIT INFO

DESC="SmartHome.py"
NAME=smarthome.py
SH_ARGS=""
SH_UID='smarthome'

PATH=/sbin:/usr/sbin:/bin:/usr/bin:/usr/local/bin
DAEMON=/usr/local/smarthome/bin/$NAME
PIDFILE=/usr/local/smarthome/var/run/smarthome.pid
SCRIPTNAME=/etc/init.d/$NAME

[ -x "$DAEMON" ] || exit 0

[ -r /etc/default/$NAME ] && . /etc/default/$NAME

DAEMON_ARGS="$SH_ARGS"

do_start()
{
    #touch $PIDFILE
    #chown $SH_UID $PIDFILE
    #start-stop-daemon --start --quiet --chuid $SH_UID --pidfile $PIDFILE --exec $DAEMON --test > /dev/null || return 1
    #start-stop-daemon --start --quiet --chuid $SH_UID --pidfile $PIDFILE --exec $DAEMON -- $DAEMON_ARGS || return 2
    sudo -u $SH_UID $DAEMON --start
}

do_stop()
{
    sudo -u $SH_UID $DAEMON --stop
    #start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 --pidfile $PIDFILE --name $NAME
    #RETVAL="$?"
    #[ "$RETVAL" = 2 ] && return 2
    #start-stop-daemon --stop --quiet --oknodo --retry=0/30/KILL/5 --exec $DAEMON
    #[ "$?" = 2 ] && return 2
    #rm -f $PIDFILE
    #return "$RETVAL"
}

do_reload() {
    start-stop-daemon --stop --signal 1 --quiet --pidfile $PIDFILE --name $NAME
    return 0
}

case "$1" in
    start)
        do_start
        ;;
    stop)
        do_stop
        ;;
    #reload|force-reload)
        #echo "Reloading $DESC" "$NAME"
        #do_reload
        #log_end_msg $?
        #;;
    restart)
        #
        # If the "reload" option is implemented then remove the
        # 'force-reload' alias
        #
        echo "Restarting $DESC" "$NAME"
        do_stop
        sleep 1
        do_start
        ;;
    *)
        echo "Usage: $SCRIPTNAME {start|stop|restart}" >&2
        exit 3
        ;;
esac
