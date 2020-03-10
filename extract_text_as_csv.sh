#!/bin/sh

#
# Extracts text from tweets (JSON) provided via stdin and outputs as rows of CSV
# Aware of extended_tweet structures.
#
# Usage: cat file_of_tweets.json | ./extract_text_as_csv.sh
#
# Author: Derek Weber
# Date: 2020-01-13
#

jq -cr '. |
  {
    user_id: .user.id_str,
    user_screen_name: .user.screen_name,
    ts: .created_at,
    tweet_id: .id_str,
    text: (if .extended_tweet == null then (if .full_text == null then .text else .full_text end) else .extended_tweet.full_text end)
  } |
  [.user_id,.user_screen_name,.ts,.tweet_id,.text] |
  map(gsub("\n"; "\\n")) |
  @csv'
