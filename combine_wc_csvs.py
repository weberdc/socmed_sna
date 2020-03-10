#!/usr/bin/env python3

#
# Simple programme to combine two-column key-value CSVs, e.g., word counts.
# Example usage:
#  python combine_wc_csvs.py -o combined-lang-counts.csv lang-counts1.csv lang-counts2.py
#

from __future__ import print_function
from argparse import ArgumentParser

import sys

class Options:
    def __init__(self):
        self.usage = 'combine_wc_csvs.py [options] wc1.csv [wc2.csv ...]'
        self._init_parser()

    def _init_parser(self):

        self.parser = ArgumentParser(usage=self.usage,conflict_handler='resolve')
        self.parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            default=False,
            dest='verbose',
            help='Turn on verbose logging (default: False)'
        )
        self.parser.add_argument(
            '-o', '--out-file',
            dest='out_csv',
            required=True,
            help='Filename of CSV to which to write'
        )
        self.parser.add_argument(
            '-h', '--header',
            action='store_true',
            default=False,
            dest='expect_header',
            help='Expect headers in the CSVs (default: False)'
        )
        self.parser.add_argument(
            'i_files', metavar='i_file', type=str, nargs='*',
            help='A file of tweets to consider'
        )


    def parse(self, args=None):
        return self.parser.parse_args(args)


def flatten(list_of_lists):
    """Takes a list of lists and turns it into a list of the sub-elements"""
    return [item for sublist in list_of_lists for item in sublist]

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

    csv_files = opts.i_files

    csvs = {}
    header = []
    for csv_file in csv_files:
        csv = {}
        with open(csv_file, 'r', encoding='utf-8') as f:
            count = 0
            for l in f:
                count += 1
                parts = l.split(',')  # assume "word,count"
                if opts.expect_header and count == 1:
                    header = parts
                    continue
                csv[parts[0].strip()] = parts[1].strip()
            csvs[csv_file] = csv

    all_keys = list(set(flatten([list(csvs[k].keys()) for k in csvs])))
    all_keys.sort()

    with open(opts.out_csv, 'w', encoding='utf-8') as out:
        out.write(','.join(['%s,' % f for f in csv_files]))
        out.write('\n')
        if opts.expect_header:
            out.write('%s\n' % ','.join([','.join(header)] * len(csv_files)))
        else:
            out.write('%s\n' % ','.join(['Word,Count'] * len(csv_files)))
        for k in all_keys:
            for f in csv_files:
                out.write('%s,%s' % (k, csvs[f].get(k, 0)))
                if csv_files.index(f) != len(csv_files) - 1:
                    out.write(',')
                else:
                    out.write('\n')
