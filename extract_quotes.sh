#!/bin/sh

#
# Extracts quote info from tweets (JSON) provided via stdin, with an optional
# header if -h or --header is provided. Aware of extended_tweet structures.
#
# Usage: cat file_of_tweets.json | ./exract_quotes.sh [-h|--header]
#
# Author: Derek Weber
# Date: 2018-12-04
#

if test "$1" == "-h" || test "$1" == "--header" ; then
  echo "quoting_user_id,quoted_user_id,quote_created_at,tweet_type,quote_id,original_tweet_id"
fi

# we don't want to catch retweets of quotes - they should be counted as retweets, so we filter them out
jq -cr '.|select(.retweeted_status == null)|select(.quoted_status != null)|
  {
    quoter_user_id: .user.id_str,
    quoted_user_id: .quoted_status.user.id_str,
    ts: .created_at,
    quote_id: .id_str,
    original_tweet_id: .quoted_status.id_str
  }|[.quoter_user_id,.quoted_user_id,.ts,"QUOTE",.quote_id,.original_tweet_id]|@csv'
