#!/bin/bash

if [ "$1" == "" ]; then
    echo "ERROR, usage is: $0 start|stop|restart|status" 
    exit 1
fi

DBA_PW=Gx3DWCyHsj3bVY3MU2nR
DAEMON=virtuoso-t
ISQL=isql-vt

status() {
    pid=$(pgrep $DAEMON)
    if [ "$pid" == "" ]; then
        echo "$(date) virtuoso daemon is NOT running"
    else
        echo "$(date) virtuoso is running, pid is $pid"
    fi
}

stop() {
    status
    if pgrep $DAEMON; then
        echo "$(date) stopping virtuoso..."
        echo "$(date) requesting checkpoint"
        isql 1111 dba $DBA_PW exec="checkpoint;"
        echo "$(date) requesting shutdown"
        isql 1111 dba $DBA_PW exec="shutdown;"
        sleep 5
        echo "$(date) virtuoso stopped"
    fi
}

start() {
    status
    if pgrep $DAEMON; then exit

    echo "$(date) starting virtuoso..."
    /usr/bin/virtuoso-t +wait +configfile /etc/virtuoso-opensource-7/virtuoso.ini

    echo -n "$(date) checking virtuoso listening on 1111 "
    while true; do
        echo -n "."
        isqlok=$(netstat -plant 2> /dev/null | grep 1111 | grep virtuoso | grep LISTEN | wc -l)
        if [ "$isqlok" == "1" ]; then break; fi
        sleep 5
    done
    echo " OK"

    echo -n "$(date) checking virtuoso listening on 8890 "
    while true; do
    echo -n "."
    webok=$(netstat -plant 2> /dev/null | grep 8890 | grep virtuoso  | wc -l)
    if [ "$webok" == "1" ]; then break; fi
    sleep 5
    done
    echo " OK"

    echo "$(date) virtuoso restarted on $(hostname)"   
}


action=$1

if [ "$action" == "status" ]; then
    status
fi
if [ "$action" == "start" ]; then
    start
fi
if [ "$action" == "stop" ]; then
    stop
fi
if [ "$action" == "restart" ]; then
    stop
    start
fi


