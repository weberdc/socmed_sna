#!/bin/sh

if [ "$1" == "-u" ]; then
    # make sure to strip 'en-gb' and 'en-au' down to 'en'
    jq -cr '.|{user_id:.user.id_str,lang:.user.lang}' | sort -u | jq -cr '.lang' | cut -d '-' -f 1 | tr '[:upper:]' '[:lower:]' | sort | uniq -c | sort -nr | tr -s ' ' | awk '{ print $2 "," $1 }'
else
    jq -cr '.lang' | tr '[:upper:]' '[:lower:]' | sort | uniq -c | sort -nr | tr -s ' ' | awk '{ print $2 "," $1 }'
fi
