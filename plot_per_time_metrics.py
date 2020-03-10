#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser
from datetime import datetime, timedelta
from itertools import cycle


import csv
import json
import math
import matplotlib.pyplot as plt
import os
import os.path
import sys
import time


class Options:
    def __init__(self):
        self.usage = 'plot_per_time_metrics.py -f <filenamebase> [options]'
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
            '--batch-mode',
            action='store_true',
            default=False,
            dest='batch_mode',
            help='Batch mode (non-interactive) - do not display plot onscreen, write straight to disk (default: False)'
        )
        self.parser.add_argument(
            '-i', '-f', '--file',
            default=None,
            dest='in_filebase',
            required=True,
            help='Basename for files to inspect, e.g., "tweets" for "tweets.json", "tweets-RETWEETS.csv", etc.'
        )
        self.parser.add_argument(
            '-l', '--label',
            default=None,
            dest='label',
            required=False,
            help='Label for the plots (default: filename base).'
        )
        self.parser.add_argument(
            '-w', '--window',
            default=15,
            dest='window_mins',
            type=int,
            help='Size of time window to use, in minutes (default: 15)'
        )
        self.parser.add_argument(
            '-y', '--y-limits',
            default='auto-auto-auto-auto',
            dest='y_limits',
            required=False,
            help='Hyphen-separated limits to use for y values, expecting a value for each chart (default: auto,auto,auto)'
        )
        self.parser.add_argument(
            '-o', '--out-dir',
            dest='out_dir',
            default='.',
            required=False,
            help='Alternative directory to which to write output (default .)'
        )
        self.parser.add_argument(
            '--out-filebase',
            dest='out_filebase',
            default=None,
            required=False,
            help='Alternative filename prefix to use for output file (default input filename base)'
        )


    def parse(self, args=None):
        return self.parser.parse_args(args)


def read_lines(file):
    if file:
        with open(file, 'r', encoding='utf-8') as f:
            return [l.strip() for l in f.readlines()]
    else:
        log("WARNING: can't read %s" % file)
        return []


def timestamp_2_epoch_seconds(ts):
    return int(time.mktime(ts.timetuple()))


TWITTER_TS_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'  #Tue Apr 26 08:57:55 +0000 2011
ARG_TS_FORMAT = '%Y-%m-%d %H:%M' # 2016-12-25 7:53


def parse_ts(ts_str, fmt=TWITTER_TS_FORMAT):
    # print(ts_str)
    try:
        time_struct = time.strptime(ts_str, fmt)
    except TypeError:
        # timestamps are in millis since epoch
        # props to https://stackoverflow.com/a/12458703
        time_struct = time.gmtime(float(ts_str) / 1000.0)
    return datetime.fromtimestamp(time.mktime(time_struct))


def format_twitter_ts(epoch_seconds):
    secs = int(epoch_seconds)
    ts = datetime.fromtimestamp(secs)  # not UTC
    return ts.strftime(TWITTER_TS_FORMAT)


def parse_twitter_ts(ts_str, tz_delta_hrs=0, tz_delta_mins=0):
    ts = parse_ts(ts_str, TWITTER_TS_FORMAT)
    if tz_delta_hrs or tz_delta_mins:
        ts += timedelta(hours=tz_delta_hrs, minutes=tz_delta_mins)
    return ts


class CsvTable:
    def __init__(self, fn, columns, ts_col):
        self.fn = fn
        self.columns = columns
        self.ts_col = ts_col


    # def get(self, row_idx, col_idx):
    #     return self.rows[row_idx][self.column_names[col_idx]]


    def load_csv(self):
        self.parse_csv(self.fn, self.columns, self.ts_col)
        self.rows.sort(key=lambda r: r[self.column_names[self.ts_col]])


    def parse_csv(self, fn, columns, ts_col):
        with open(fn, encoding='utf-8') as f:
            csv_reader = csv.reader(f, delimiter=',')   # handles URLs with commas
            line_count = 0
            self.rows = []
            for row in csv_reader:
                if line_count == 0:
                    self.column_names = row
                else:
                    r = {}
                    for i in range(len(self.column_names)):
                        field = row[i]
                        if field[0] == '"': field = field[1:-1]  # strip quotes
                        if i == ts_col:
                            try:
                                # is it already an epoch int?
                                r[self.column_names[i]] = int(field) / 1000  # I want seconds, not millis
                            except ValueError:  # typecast to int fails
                                r[self.column_names[i]] = timestamp_2_epoch_seconds(parse_twitter_ts(field))
                        else:
                            r[self.column_names[i]] = field

                    self.rows.append(r)
                line_count += 1


def bucket_rows(table, buckets_required, first_ts, w_mins=15, label_col=1, ts_col=2, to_lower=False, unique=False):
    def get_ts_from(r):
        return get_col_from(r, ts_col)
    def get_col_from(r, col_idx):
        return r[table.column_names[col_idx]]

    w_secs = w_mins * 60

    buckets = [{} for b in range(buckets_required)]  # bucket is a map of label:count
    # log('buckets required: %d' % buckets_required)

    current_ts = first_ts
    for r in table.rows:
        current_ts = get_ts_from(r)
        current_bucket_idx = int(math.floor((current_ts - first_ts) / w_secs))
        # print('first ts  : %d' % first_ts)
        # print('current ts: %d' % current_ts)
        # print('Window (s): %d' % w_secs)
        bucket = buckets[current_bucket_idx]
        label = get_col_from(r, label_col)
        if to_lower: label = label.lower()
        bucket[label] = bucket.get(label, 0) + 1

    return buckets


def bucket_tweets(tweets, w_mins=15):
    w_secs = w_mins * 60
    t_alpha = timestamp_2_epoch_seconds(parse_ts(tweets[0]['created_at']))
    t_omega = timestamp_2_epoch_seconds(parse_ts(tweets[-1]['created_at']))
    buckets_required = int(math.ceil((t_omega - t_alpha) / w_secs))
    buckets = [[] for b in range(buckets_required)]

    for t in tweets:
        ts = timestamp_2_epoch_seconds(parse_ts(t['created_at']))
        bucket_idx = int(math.floor((ts - t_alpha) / w_secs))
        buckets[bucket_idx].append(t)

    return buckets


def load_table(in_fb, interaction, columns, ts_col, log_on=True):
    fn = '%s-%s.csv' % (in_fb, interaction)
    if log_on: log('Loading %s...' % fn)
    table = CsvTable(fn, columns=columns, ts_col=ts_col)
    table.load_csv()

    return table


def log_buckets(buckets):
    if not DEBUG: return
    log('Num buckets: %d' % len(buckets))
    log('Per Day:')
    idx = 1
    for bucket in buckets:
        log('Window %3d. %7d' % (idx, sum(bucket.values())))
        idx += 1


def load_tweets(in_fb):
    fn = '%s.json' % in_fb
    if not os.path.isfile(fn):
        fn = '%s.jsonl' % in_fb
    return [json.loads(l) for l in read_lines(fn)]


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
    log('Looking at files starting with %s' % opts.in_filebase)

    in_fb    = opts.in_filebase
    out_fb   = opts.out_filebase if opts.out_filebase else in_fb
    w_mins   = opts.window_mins
    label    = opts.label if opts.label else in_fb
    y_limits = opts.y_limits.split('-')

    tweets        = load_tweets(in_fb)
    hashtag_table = load_table(in_fb, 'hashtags', columns=5, ts_col=2)
    mention_table = load_table(in_fb, 'mentions', columns=5, ts_col=2)
    quote_table   = load_table(in_fb, 'quotes',   columns=6, ts_col=2)
    reply_table   = load_table(in_fb, 'replies',  columns=6, ts_col=2)
    retweet_table = load_table(in_fb, 'retweets', columns=6, ts_col=2)
    url_table     = load_table(in_fb, 'urls',     columns=5, ts_col=2)

    tables   = [hashtag_table, mention_table, quote_table, reply_table, retweet_table, url_table]
    start_ts = sys.maxsize
    end_ts   = 0
    for t in tables:
        for r in t.rows:
            ts = r[t.column_names[2]]
            start_ts = min(ts, start_ts)
            end_ts   = max(ts, end_ts)
            # if start_ts > ts: start_ts = ts
            # if end_ts   < ts: end_ts   = ts

    log('Earliest timestamp: %s' % start_ts)
    log('Latest timestamp:   %s' % end_ts)

    num_buckets = int(math.ceil((end_ts - start_ts) / (w_mins * 60)))

    log('Buckets required: %d' % num_buckets)

    tweet_buckets = bucket_tweets(tweets, w_mins)

    hashtag_buckets = bucket_rows(hashtag_table, num_buckets, start_ts, w_mins, ts_col=2, label_col=1, to_lower=True)
    log_buckets(hashtag_buckets)
    mention_buckets = bucket_rows(mention_table, num_buckets, start_ts, w_mins, ts_col=2, label_col=1)
    log_buckets(mention_buckets)
    quote_buckets   = bucket_rows(quote_table,   num_buckets, start_ts, w_mins, ts_col=2, label_col=1)
    log_buckets(quote_buckets)
    reply_buckets   = bucket_rows(reply_table,   num_buckets, start_ts, w_mins, ts_col=2, label_col=1)
    log_buckets(reply_buckets)
    retweet_buckets = bucket_rows(retweet_table, num_buckets, start_ts, w_mins, ts_col=2, label_col=1)
    log_buckets(retweet_buckets)
    url_buckets     = bucket_rows(url_table,     num_buckets, start_ts, w_mins, ts_col=2, label_col=1)
    log_buckets(url_buckets)

    def totals(buckets):
        return [sum(b.values()) for b in buckets]

    def unique(buckets):
        return [len(b) for b in buckets]

    def cum_uniq_type(buckets):
        seen_keys = set()
        results = []
        for b in buckets:
            seen_keys = seen_keys.union(b.keys())
            results.append(len(seen_keys))
        return results

    def set_y_limit(axis, y_lims, index):
        # if True: return
        y_lim = y_lims[index]
        if y_lim != 'auto':
            axis.set_ylim(top=int(y_lim))


    num_buckets = len(hashtag_buckets)
    x_values    = range(1, num_buckets+1)
    # colours     = plt.cm.get_cmap("hsv", num_buckets+1)
    colours     = cycle('bgrcmk')
    linestyles  = cycle([(), (1,2), (1,5), (1,10)])#(['-', '--', ':', '-.'])

    # print(num_buckets)

    fig = plt.figure(figsize=(10,10))

    ax1 = fig.add_subplot(2,2,1)
    ax1.set_title('%s - Interaction instances' % label)
    ax1.set_xlabel('Time window (%d minutes)' % w_mins)
    ax1.set_xlim(1, num_buckets)
    set_y_limit(ax1, y_limits, 0)
    ax1.plot(x_values, totals(hashtag_buckets), label='Hashtags', c=next(colours), linewidth=1)
    ax1.plot(x_values, totals(mention_buckets), label='Mentions', c=next(colours), linewidth=1)
    ax1.plot(x_values, totals(quote_buckets),   label='Quotes',   c=next(colours), linewidth=1)
    ax1.plot(x_values, totals(reply_buckets),   label='Replies',  c=next(colours), linewidth=1)
    ax1.plot(x_values, totals(retweet_buckets), label='Retweets', c=next(colours), linewidth=1)
    ax1.plot(x_values, totals(url_buckets),     label='URLs',     c=next(colours), linewidth=1)
    # ax1.plot(x_values, totals(hashtag_buckets), label='Hashtags', c=next(colours), linestyle=next(linestyle), linewidth=1)
    # ax1.plot(x_values, totals(mention_buckets), label='Mentions', c=next(colours), linestyle=next(linestyle), linewidth=1)
    # ax1.plot(x_values, totals(quote_buckets),   label='Quotes',   c=next(colours), linestyle=next(linestyle), linewidth=1)
    # ax1.plot(x_values, totals(reply_buckets),   label='Replies',  c=next(colours), linestyle=next(linestyle), linewidth=1)
    # ax1.plot(x_values, totals(retweet_buckets), label='Retweets', c=next(colours), linestyle=next(linestyle), linewidth=1)
    # ax1.plot(x_values, totals(url_buckets),     label='URLs',     c=next(colours), linestyle=next(linestyle), linewidth=1)
    ax1.legend()

    ax2 = fig.add_subplot(2,2,2)
    ax2.set_title('%s - Interaction types' % label)
    ax2.set_xlabel('Time window (%d minutes)' % w_mins)
    ax2.set_xlim(1, num_buckets)
    set_y_limit(ax2, y_limits, 1)
    ax2.plot(x_values, unique(hashtag_buckets), label='Hashtags', c=next(colours), linewidth=1)
    ax2.plot(x_values, unique(mention_buckets), label='Mentions', c=next(colours), linewidth=1)
    ax2.plot(x_values, unique(quote_buckets),   label='Quotes',   c=next(colours), linewidth=1)
    ax2.plot(x_values, unique(reply_buckets),   label='Replies',  c=next(colours), linewidth=1)
    ax2.plot(x_values, unique(retweet_buckets), label='Retweets', c=next(colours), linewidth=1)
    ax2.plot(x_values, unique(url_buckets),     label='URLs',     c=next(colours), linewidth=1)
    ax2.legend()

    ax3 = fig.add_subplot(2,2,3)
    ax3.set_title('%s - Cumulative int. types' % label)
    ax3.set_xlabel('Time window (%d minutes)' % w_mins)
    ax3.set_xlim(1, num_buckets)
    set_y_limit(ax3, y_limits, 2)
    ax3.plot(x_values, cum_uniq_type(hashtag_buckets), label='Hashtags', c=next(colours), linewidth=1)
    ax3.plot(x_values, cum_uniq_type(mention_buckets), label='Mentions', c=next(colours), linewidth=1)
    ax3.plot(x_values, cum_uniq_type(quote_buckets),   label='Quotes',   c=next(colours), linewidth=1)
    ax3.plot(x_values, cum_uniq_type(reply_buckets),   label='Replies',  c=next(colours), linewidth=1)
    ax3.plot(x_values, cum_uniq_type(retweet_buckets), label='Retweets', c=next(colours), linewidth=1)
    ax3.plot(x_values, cum_uniq_type(url_buckets),     label='URLs',     c=next(colours), linewidth=1)
    ax3.legend()

    ax4 = fig.add_subplot(2,2,4)
    ax4.set_title('%s - Tweets over time' % label)
    ax4.set_xlabel('Time window (%d minutes)' % w_mins)
    ax4.set_xlim(1, num_buckets)
    set_y_limit(ax4, y_limits, 3)
    ax4.plot(x_values, [len(b) for b in tweet_buckets], label='Tweets', c=next(colours), linewidth=1)
    # ax4.legend()

    plt.tight_layout()
    plt.savefig('%s-totals-%dm.png' % (os.path.join(opts.out_dir, out_fb), w_mins))

    if not opts.batch_mode:
        plt.show()
