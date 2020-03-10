#!/bin/sh

jq -cr '.|select(.entities.hashtags|length > 0)|
  {
    hts: (if .extended_tweet == null then
      .entities.hashtags
    else
      .extended_tweet.entities.hashtags
    end)
  }|.hts[].text' | tr '[:upper:]' '[:lower:]' | sort | uniq -c | sort -nr | tr -s ' ' | awk '{ print $2 "," $1 }'
