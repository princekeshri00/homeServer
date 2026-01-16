#!/bin/bash
# DuckDNS IPv4 & IPv6 dynamic update script

DOMAIN="<domain name>"
TOKEN="<duckdns token>"

LASTIPFILE4=./last_ipv4.txt
LASTIPFILE6=./last_ipv6.txt
LOGFILE=./duck.log
MAXLINES=1000  # Logfile max lines

IP4=$(curl -4 -s https://checkip.amazonaws.com) #ipv4 grab

if [ -n "$IP4" ]; then
    LASTIP4=$(cat $LASTIPFILE4 2>/dev/null || echo "")
    if [ "$IP4" != "$LASTIP4" ]; then
        STATUS4=$(curl -s "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=$IP4")
        DT=$(date +"%d-%m-%Y %H:%M:%S")
        if [ "$STATUS4" = "OK" ]; then
            echo "$DT | IPv4: $IP4 | $STATUS4" >> $LOGFILE
            echo $IP4 > $LASTIPFILE4
            tail -n $MAXLINES $LOGFILE > $LOGFILE.tmp && mv $LOGFILE.tmp $LOGFILE
        else
            echo "$DT | IPv4: $IP4 | FAILED" >> $LOGFILE
        fi
    fi
fi


IP6=$(curl -6 -s https://ifconfig.co) #ipv6 grab

#local ipv6 ignored
if [[ -n "$IP6" && "$IP6" != fe80* && "$IP6" != fd* ]]; then
    LASTIP6=$(cat $LASTIPFILE6 2>/dev/null || echo "")
    if [ "$IP6" != "$LASTIP6" ]; then
        STATUS6=$(curl -s "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ipv6=$IP6")
        DT=$(date +"%d-%m-%Y %H:%M:%S")
        if [ "$STATUS6" = "OK" ]; then
            echo "$DT | IPv6: $IP6 | $STATUS6" >> $LOGFILE
            echo $IP6 > $LASTIPFILE6
            tail -n $MAXLINES $LOGFILE > $LOGFILE.tmp && mv $LOGFILE.tmp $LOGFILE
        else
            echo "$DT | IPv6: $IP6 | FAILED" >> $LOGFILE
        fi
    fi
fi
