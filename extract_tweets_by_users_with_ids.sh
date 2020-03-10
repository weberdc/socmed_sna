#!/bin/sh

TWEETS_FILE=$1
IDS_FILE=$2
VERBOSE=$3

for id in `cat $IDS_FILE`; do
    if [[ "${VERBOSE}" != "" ]]; then
        (>&2 echo "User ${id}")  # Echo to stderr. Props to https://stackoverflow.com/a/23550347
    fi
    jq -cr --arg ID "${id}" 'select(.user.id_str==$ID)' $TWEETS_FILE
done

