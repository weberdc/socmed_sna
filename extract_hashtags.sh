#!/bin/sh

#
# Extracts hashtags from tweets (JSON) provided via stdin, with an optional
# header if -h or --header is provided. Aware of extended_tweet structures.
#
# Usage: cat file_of_tweets.json | ./exract_hashtags.sh [-h|--header]
#
# Author: Derek Weber
# Date: 2018-12-04
#

if test "$1" == "-h" || test "$1" == "--header" ; then
  echo "user_id,hashtag,created_at,tweet_type,tweet_id,tweet_lang"
fi

jq -cr '.|select(.entities.hashtags|length > 0)|
  {
    user_id: .user.id_str,
    hashtags: (if .extended_tweet != null then
      .extended_tweet.entities.hashtags
    else
      .entities.hashtags
    end),
    ts: .created_at,
    tweet_id: .id_str,
    lang: .lang
  }|{user_id:.user_id,hashtag:.hashtags[].text,ts:.ts,tweet_id:.tweet_id,t_lang:.lang}|
  [.user_id,.hashtag,.ts,"HASHTAG",.tweet_id,.t_lang]|@csv'
