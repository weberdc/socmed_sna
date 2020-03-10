#!/usr/bin/env python3
from __future__ import print_function

import csv
import json
import os
import sys
import time

from argparse import ArgumentParser
from datetime import datetime


class Options:
    def __init__(self):
        self.usage = '%s.py -t|--tweets_file <file of tweets> -i|--ids-file <tweet_id_file> [--pretty]' % os.path.basename(__file__)
        self._init_parser()

    def _init_parser(self):
        self.parser = ArgumentParser(usage=self.usage, conflict_handler='resolve')
        self.parser.add_argument(
            '-i', '--tweets-file',
            required=True,
            dest='tweets_file',
            help='Tweets file ("-" for stdin)'
        )
        self.parser.add_argument(
            '-o', '--csv-file',
            required=True,
            dest='csv_file',
            help='File to write CSV to'
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

def to_epoch(ts_str, fmt=TWITTER_TS_FORMAT):
    return time.mktime(time.strptime(ts_str, fmt))  # "%a %b %d %H:%M:%S +0000 %Y"))
    # time_struct = time.strptime(ts_str, fmt)
    # ts = datetime.fromtimestamp(time.mktime(time_struct))
    # return int(time.mktime(ts.timetuple()))


def get_text(t):
    if XT_KEY in t and t[XT_KEY] != None:
        text = t[XT_KEY]['full_text']
    elif 'full_text' in t and t['full_text'] != None:
        return t['full_text']
    else:
        return t['text']


def open_file(file=None):
    """Gets the lines from the given file or stdin if it's None or '' or '-'."""
    if file and file != '-':
        if file[-1] in 'zZ':
            in_f = gzip.open(tweets_file, 'rb')
        else:
            in_f = open(file, 'r', encoding = 'utf-8')
        return in_f
#        with in_f as f:
#            return [l.strip() for l in f.readlines()]
    else:
        return sys.stdin
#        return [l.strip() for l in sys.stdin]

HEADINGS = [
  'sharer_user_id', 'original_user_id', 'sharer_user_screen_name',
  'original_user_screen_name', 'shared_tweet_id', 'original_tweet_id',
  'shared_tweet_created_at_ms', 'original_tweet_created_at_ms',
  'shared_tweet_created_at_str', 'original_tweet_created_at_str', 'interaction',
  'original_text', 'comment_text'
]
def write_header(f):
    f.write('%s\n' % ','.join(HEADINGS))


def extract_info(t, is_quote):
    SHARE_KEY = QT_KEY if is_quote else RT_KEY
    return {
        'sharer_user_id': t['user']['id_str'],
        'original_user_id': t[SHARE_KEY]['user']['id_str'],
        'sharer_user_screen_name': t['user']['screen_name'],
        'original_user_screen_name': t[SHARE_KEY]['user']['screen_name'],
        'shared_tweet_id': t['id_str'],
        'original_tweet_id': t[SHARE_KEY]['id_str'],
        'shared_tweet_created_at_ms': to_epoch(t['created_at']),
        'original_tweet_created_at_ms': to_epoch(t[SHARE_KEY]['created_at']),
        'shared_tweet_created_at_str': t['created_at'],
        'original_tweet_created_at_str': t[SHARE_KEY]['created_at'],
        'interaction': 'QUOTE' if is_quote else 'RETWEET'
    }


def eprint(*args, **kwargs):
    """Print to stderr"""
    print(*args, file=sys.stderr, **kwargs)

RT_KEY = 'retweeted_status'
QT_KEY = 'quoted_status'
XT_KEY = 'extended_tweet'

DEBUG=False
def log(msg):
    if DEBUG: eprint(msg)


if __name__=='__main__':

    options = Options()
    opts = options.parse(sys.argv[1:])

    DEBUG=opts.verbose

    csv_file = opts.csv_file
    tweets_file = opts.tweets_file

    with open(csv_file, mode='w', newline='\n', encoding='utf-8') as out_f:
        write_header(out_f)
        csv_writer = csv.writer(out_f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        line_count = 0
        for line in open_file(tweets_file):
            line_count += 1
            t = json.loads(line)

            is_retweet = RT_KEY in t and t[RT_KEY] != None
            is_quote   = QT_KEY in t and t[QT_KEY] != None
            is_rt_of_a_qt = is_retweet and is_quote

            if not (is_quote or is_retweet): continue

            info = extract_info(t, is_quote)

            if is_rt_of_a_qt:
                info['comment_text'] = repr(get_text(t[RT_KEY]))
                info['original_text'] = repr(get_text(t[QT_KEY]))
            elif is_retweet:
                info['comment_text'] = ''
                info['original_text'] = repr(get_text(t[RT_KEY]))
            elif is_quote:
                info['comment_text'] = repr(get_text(t))
                info['original_text'] = repr(get_text(t[QT_KEY]))

            # print('RT: %s, QT: %s, RT/QT: %s' % (is_retweet, is_quote, is_rt_of_a_qt))

            row = [info[h] for h in HEADINGS]
            csv_writer.writerow(row)

            if DEBUG:
                if line_count % 10000 == 0: log('%8d' % line_count)

    log('DONE')
