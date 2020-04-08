#!/bin/sh

#
# Extracts URLs from tweets (JSON) provided via stdin, with an optional
# header if -h or --header is provided. Aware of extended_tweet structures.
#
# Usage: cat file_of_tweets.json | ./exract_urls.sh [-h|--header]
#
# Author: Derek Weber
# Date: 2018-12-04
#

if test "$1" == "-h" || test "$1" == "--header" ; then
  echo "user_id,expanded_url,created_at,tweet_type,tweet_id,tweet_lang"
fi

# I filter .url != "" because extended tweets include an internal URL to the extended tweet content
# which is not really a URL in the text of the tweet.
jq -cr '.|select(.entities.urls|length > 0)|
  {
    user_id: .user.id_str,
    urls: (if .extended_tweet != null then
      .extended_tweet.entities.urls
    else
      .entities.urls
    end),
    ts: .created_at,
    tweet_id: .id_str,
    lang: .lang
  }|{user_id:.user_id,url:.urls[].expanded_url,ts:.ts,tweet_id:.tweet_id,t_lang:.lang}|
  select(.url|length  > 0)|
  [.user_id,.url,.ts,"URL",.tweet_id,.t_lang]|@csv'
