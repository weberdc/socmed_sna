#!/bin/sh

#
# Extracts reply info from tweets (JSON) provided via stdin, with an optional
# header if -h or --header is provided. Aware of extended_tweet structures.
#
# Usage: cat file_of_tweets.json | ./exract_replies.sh [-h|--header]
#
# Author: Derek Weber
# Date: 2018-12-04
#

if test "$1" == "-h" || test "$1" == "--header" ; then
  echo "replying_user_id,replied_to_user_id,reply_created_at,tweet_type,reply_tweet_id,original_tweet_id"
fi

jq -cr '.|select(.in_reply_to_status_id_str != null)|
  {
    replying_user_id: .user.id_str,
    replied_to_user_id: .in_reply_to_user_id_str,
    ts: .created_at,
    reply_tweet_id: .id_str,
    original_tweet_id: .in_reply_to_status_id_str
  }|[.replying_user_id,.replied_to_user_id,.ts,"REPLY",.reply_tweet_id,.original_tweet_id]|@csv'
