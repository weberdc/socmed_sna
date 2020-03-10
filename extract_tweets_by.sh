#!/bin/sh

jq -rc --arg ID "${1}" '.|select(.user.id_str==$ID)|.'

#jq -cr --arg ID "${id}" 'select(.id_str==$ID)' $TWEETS_FILE

