#!/usr/bin/env python3
from __future__ import print_function

import gzip
import json
import sys
import time

from argparse import ArgumentParser
from datetime import datetime


class Options:
    def __init__(self):
        self.usage = 'filter_tweets_by_id.py -t|--tweets_file <file of tweets> -i|--ids-file <tweet_id_file> -o|--out-file <file of tweets> [-v|--verbose]'
        self._init_parser()

    def _init_parser(self):
        self.parser = ArgumentParser(usage=self.usage, conflict_handler='resolve')
        self.parser.add_argument(
            '-t', '--tweets-file',
            default='-',
            required=True,
            dest='tweets_file',
            help='Tweets file (default: all)'
        )
        self.parser.add_argument(
            '-i', '--ids-file',
            default=None,
            required=True,
            dest='ids_file',
            help='Tweet IDs file (default: "")'
        )
        self.parser.add_argument(
            '-o', '--out-file',
            required=True,
            dest='out_file',
            help='File to write filtered tweets to'
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

def parse_ts(ts_str, fmt=TWITTER_TS_FORMAT):
    try:
        time_struct = time.strptime(ts_str, fmt)
    except TypeError:
        return int(ts_str)  # epoch millis
    return datetime.fromtimestamp(time.mktime(time_struct))


def fetch_lines(file=None):
    """Gets the lines from the given file or stdin if it's None or '' or '-'."""
    if file and file != '-':
        with gzip.open(file, 'rt') if file[-1] in 'zZ' else open(file, 'r', encoding='utf-8') as f:
            return [l.strip() for l in f.readlines()]
    else:
        return [l.strip() for l in sys.stdin]


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

    ids_of_interest = fetch_lines(opts.ids_file) if opts.ids_file else opts.i_files
    tweets_file = opts.tweets_file
    # pretty = opts.pretty

    tweets_of_interest = [
        (l, t) for l, t in [(l, json.loads(l)) for l in fetch_lines(tweets_file)]
        if t['id_str'] in ids_of_interest
    ]

    log('all lines: %d' % len(tweets_of_interest))
    log('tweet IDs: %d' % len(set([t['id_str'] for l,t in tweets_of_interest])))

    tweets_of_interest.sort(key=lambda tup: parse_ts(tup[1]['created_at']))
    with open(opts.out_file, 'w', encoding='utf-8') as f:
        for t in tweets_of_interest:
            # f.write('%\n' % t[0])
            f.write('{}\n'.format(t[0]))
