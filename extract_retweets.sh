#!/bin/sh

#
# Extracts retweet info from tweets (JSON) provided via stdin, with an optional
# header if -h or --header is provided. Aware of extended_tweet structures.
#
# Usage: cat file_of_tweets.json | ./exract_retweets.sh [-h|--header]
#
# Author: Derek Weber
# Date: 2018-12-04
#

if test "$1" == "-h" || test "$1" == "--header" ; then
  echo "retweeting_user_id,retweeted_user_id,retweet_created_at,tweet_type,retweet_id,original_tweet_id"
fi

jq -cr '.|select(.retweeted_status != null)|
  {
    retweeter_user_id: .user.id_str,
    retweeted_user_id: .retweeted_status.user.id_str,
    ts: .created_at,
    retweet_id: .id_str,
    original_tweet_id: .retweeted_status.id_str
  }|[.retweeter_user_id,.retweeted_user_id,.ts,"RETWEET",.retweet_id,.original_tweet_id]|@csv'
