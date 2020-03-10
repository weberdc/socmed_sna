#!/usr/bin/env python3
from __future__ import print_function

import json
import sys
import time

from argparse import ArgumentParser
from datetime import datetime


class Options:
    def __init__(self):
        self.usage = 'filter_objects_by_fields_with_these_values.py -i|--in-file <file of JSON objects> -p|--property <.json.path.to.field> --values-file <screen_names_file> [--inverse][-v|--verbose]'
        self._init_parser()

    def _init_parser(self):
        self.parser = ArgumentParser(usage=self.usage, conflict_handler='resolve')
        self.parser.add_argument(
            '-i', '--in-file',
            default='-',
            required=True,
            dest='in_file',
            help='File of JSON objects (default: "-")'
        )
        self.parser.add_argument(
            '-p', '--property',
            default=None,
            required=True,
            dest='property_path',
            help='Path into JSON objects (default: "")'
        )
        self.parser.add_argument(
            '--values-file',
            default=None,
            required=True,
            dest='values_file',
            help='File of interesting values, case-insensitive (default: "")'
        )
        self.parser.add_argument(
            '-o',
            default='out.json',
            required=True,
            dest='out_file',
            help='File to write filtered objects to (default: "out.json")'
        )
        self.parser.add_argument(
            '--inverse',
            action='store_true',
            default=False,
            dest='inverse',
            help='Invert the findings - ignore the named values (default: False)'
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


# TWITTER_TS_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'  #Tue Apr 26 08:57:55 +0000 2011
#
# def parse_ts(ts_str, fmt=TWITTER_TS_FORMAT):
#     try:
#         time_struct = time.strptime(ts_str, fmt)
#     except TypeError:
#         return int(ts_str)  # epoch millis
#     return datetime.fromtimestamp(time.mktime(time_struct))


def fetch_lines(file=None):
    """Gets the lines from the given file or stdin if it's None or '' or '-'."""
    if file and file != '-':
        with open(file, 'r', encoding='utf-8') as f:
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

    values_of_interest = fetch_lines(opts.values_file) if opts.values_file else opts.i_files
    values_of_interest = list(map(lambda s: s.lower(), values_of_interest))
    # prop_path          = (opts.property_path if opts.property_path[0] != '.' else opts.property_path[1:]).split('.')
    prop_path          = list(filter(lambda s: len(s.strip()), opts.property_path.split('.')))
    tweets_file        = opts.in_file
    invert             = opts.inverse

    def id_of_interest(o):
        v = o
        for p in prop_path:
            if p in v:
                v = v[p]
        if type(v) != type(''):
            return invert
        if not invert:
            return v.lower() in values_of_interest
        else:
            return v.lower() not in values_of_interest

    tweets_of_interest = [
        (l, t) for l, t in [(l, json.loads(l)) for l in fetch_lines(tweets_file)]
        if id_of_interest(t)
    ]

    log('all lines: %d' % len(tweets_of_interest))
    # log('tweet IDs: %d' % len(set([t['id_str'] for l,t in tweets_of_interest])))

    # tweets_of_interest.sort(key=lambda tup: parse_ts(tup[1]['created_at']))
    with open(opts.out_file, 'w', encoding='utf-8') as f:
        for t in tweets_of_interest:
            f.write(t[0])
            f.write('\n')

    log('DONE')
