#!/usr/bin/env python3
from __future__ import print_function

import gzip
import json
import re
import sys
# import time

from argparse import ArgumentParser
# from datetime import datetime


class Options:
    def __init__(self):
        self.usage = 'characterise_inauthentic_tweets.py -i <file of tweets> [-v|--verbose]'
        self._init_parser()

    def _init_parser(self):
        self.parser = ArgumentParser(usage=self.usage, conflict_handler='resolve')
        self.parser.add_argument(
            '-i', '--tweets-file',
            default='-',
            required=True,
            dest='tweets_file',
            help='Tweets file (default: all)'
        )
        self.parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            default=False,
            dest='verbose',
            help='Turn on verbose logging (default: False)'
        )

    def parse(self, args=None):
        return self.parser.parse_args(args)


TWITTER_TS_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'  #Tue Apr 26 08:57:55 +0000 2011

# def parse_ts(ts_str, fmt=TWITTER_TS_FORMAT):
#     try:
#         time_struct = time.strptime(ts_str, fmt)
#     except TypeError:
#         return int(ts_str)  # epoch millis
#     return datetime.fromtimestamp(time.mktime(time_struct))
def extract_text(tweet):
    """Gets the full text from a tweet if it's short or long (extended)."""

    def get_available_text(t):
        if t['truncated'] and 'extended_tweet' in t:
            # if a tweet is retreived in 'compatible' mode, it may be
            # truncated _without_ the associated extended_tweet
            #eprint('#%s' % t['id_str'])
            return t['extended_tweet']['full_text']
        else:
            return t['text'] if 'text' in t else t['full_text']

    if 'retweeted_status' in tweet:
        rt = tweet['retweeted_status']
        return extract_text(rt)
        # return 'RT @%s: %s' % (rt['user']['screen_name'], extract_text(rt))

    # if 'quoted_status' in tweet:
    #     qt = tweet['quoted_status']
    #     return get_available_text(tweet) + " --> " + extract_text(qt)

    return get_available_text(tweet)


def fetch_lines(file=None):
    """Gets the lines from the given file or stdin if it's None or '' or '-'."""
    if file and file != '-':
        with gzip.open(file, 'rt') if file[-1] in 'zZ' else open(file, 'r', encoding='utf-8') as f:
            return [l.strip() for l in f.readlines()]
    else:
        return [l.strip() for l in sys.stdin]


def extract_tokens(pattern, str):
    return list(
        filter(
            lambda t: len(t) > 0,
            map(
                lambda t: t.strip(),
                re.findall(pattern, str)
            )
        )
    )


def count_tokens_starting_with(chars, tokens):
    return sum([1 for _ in tokens if _[0] in chars])


def eprint(*args, **kwargs):
    """Print to stderr"""
    print(*args, file=sys.stderr, **kwargs)


DEBUG=False
def log(msg):
    if DEBUG: eprint(msg)


if __name__=='__main__':

    options = Options()
    opts = options.parse(sys.argv[1:])

    DEBUG=opts.verbose

    tweets_file = opts.tweets_file
    # pretty = opts.pretty

    tweets = [json.loads(l) for l in fetch_lines(tweets_file)]
    log(f'read: {len(tweets)} tweets')

    hashtags_only = 0
    hashtags_plus_url = 0
    mentions_plus_hashtags = 0
    mentions_hashtags_plus_url = 0

    ht_splitter_re = '[a-zA-Z#]+'
    me_splitter_re = '[a-zA-Z@]+'
    htme_splitter_re = '[a-zA-Z#@]+'
    X = 0
    for t in tweets:
        text = extract_text(t)
        # hashtag(s) only
        if '#' in text:
            tokens = extract_tokens(ht_splitter_re, text)
            if len(tokens) == count_tokens_starting_with('#', tokens):
                hashtags_only += 1
                log(tokens)

        # hashtag(s) and URL
        if '#' in text and 'http' in text:
            tokens = extract_tokens(htme_splitter_re, text[:text.index('http')])
            if len(tokens) == count_tokens_starting_with('#', tokens):
                hashtags_plus_url += 1
                # print(tokens)
                log(text)

        # mention(s) and hashtag(s)
        if '#' in text and '@' in text:
            tokens = extract_tokens(htme_splitter_re, text)
            if len(tokens) == count_tokens_starting_with('#@', tokens):
                mentions_plus_hashtags += 1
                log(tokens)

        # mention(s), hashtag(s) and URL
        if '#' in text and '@' in text and 'http' in text:
            tokens = extract_tokens(htme_splitter_re, text[:text.index('http')])
            if len(tokens) == count_tokens_starting_with('#@', tokens):
                mentions_hashtags_plus_url += 1
                # print(tokens)
                log(text)

    print(f'All:       {len(tweets):,}')
    print(f'HT:        {hashtags_only:>6} ({float(hashtags_only)/len(tweets):.1%})')
    print(f'HT+URL:    {hashtags_plus_url:>6} ({float(hashtags_plus_url)/len(tweets):.1%})')
    print(f'@m+HT:     {mentions_plus_hashtags:>6} ({float(mentions_plus_hashtags)/len(tweets):.1%})')
    print(f'@m+HT+URL: {mentions_hashtags_plus_url:>6} ({float(mentions_hashtags_plus_url)/len(tweets):.1%})')
