#!/bin/sh

#
# Extracts mentions from tweets (JSON) provided via stdin, with an optional
# header if -h or --header is provided. Aware of extended_tweet structures.
#
# Usage: cat file_of_tweets.json | ./exract_mentions.sh [-h|--header]
#
# Author: Derek Weber
# Date: 2018-12-04
#

if test "$1" == "-h" || test "$1" == "--header" ; then
  echo "mentioning_user_id,mentioned_user_id,created_at,tweet_type,mentioning_tweet_id,tweet_lang"
fi

jq -cr '.|select(.entities.user_mentions|length > 0)|
  {
    user_id: .user.id_str,
    mentions: (if .extended_tweet != null then
      .extended_tweet.entities.user_mentions
    else
      .entities.user_mentions
    end),
    ts: .created_at,
    tweet_id:.id_str,
    lang: .lang
  }|{user_id:.user_id,mention:.mentions[].id_str,ts:.ts,tweet_id:.tweet_id,t_lang:.lang}|
  [.user_id,.mention,.ts,"MENTION",.tweet_id,.t_lang]|@csv'
