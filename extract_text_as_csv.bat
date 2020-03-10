@echo off
rem
rem Extracts text from tweets (JSON) provided via stdin and outputs as rows of CSV
rem Aware of extended_tweet structures.
rem
rem Usage: cat file_of_tweets.json | ./extract_text_as_csv.sh
rem
rem Author: Derek Weber
rem Date: 2020-01-13
rem

set JQ=C:\cygwin64\bin\jq.exe

%JQ% -cr ". | {user_id: .user.id_str, user_screen_name: .user.screen_name, ts: .created_at, tweet_id: .id_str, text: (if .extended_tweet == null then (if .full_text == null then .text else .full_text end) else .extended_tweet.full_text end) } | [.user_id,.user_screen_name,.ts,.tweet_id,.text] | map(gsub(\"\n\"; \"\\\n\")) | @csv" %1
