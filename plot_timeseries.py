#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser
from datetime import datetime, timedelta
from itertools import cycle


import csv
import json
import gzip
import math
import matplotlib.pyplot as plt
import os
import sys
import time

#
# Plot per-time comparisons of the provided timestamped datasets, which can be lists of dates
# tweets including dates.
#



class Options:
    def __init__(self):
        self.usage = '%s [options] <file> [<file>]*' % os.path.basename(__file__)
        self._init_parser()

    def _init_parser(self):

        self.parser = ArgumentParser(usage=self.usage,conflict_handler='resolve')
        self.parser.add_argument(
            'i_files', metavar='i_file', type=str, nargs='*',
            help='A file of timestamps or tweets to consider'
        )
        self.parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            default=False,
            dest='verbose',
            help='Turn on verbose logging (default: False)'
        )
        self.parser.add_argument(
            '--tweets',
            action='store_true',
            default=False,
            dest='tweets_mode',
            help='Expect to be given tweets, not timestamps (default: False)'
        )
        self.parser.add_argument(
            '--batch-mode',
            action='store_true',
            default=False,
            dest='batch_mode',
            help='Batch mode (non-interactive) - do not display plot onscreen, write straight to disk (default: False)'
        )
        self.parser.add_argument(
            '--log-scale',
            action='store_true',
            default=False,
            dest='log_scale',
            help='Use a log scale on the y axis (default: False)'
        )
        self.parser.add_argument(
            '--cumulative',
            action='store_true',
            default=False,
            dest='cumulative',
            help='Accumulate y values over time (default: False)'
        )
        self.parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            dest='dry_run',
            help='Do not write to disk (default: False)'
        )
        self.parser.add_argument(
            '--bar',
            action='store_true',
            default=False,
            dest='bar_chart',
            help='Render bar chart, not line plot (default: False)'
        )
        self.parser.add_argument(
            '--secs',
            action='store_true',
            default=False,
            dest='secs',
            help='Timestamps are provided in epoch seconds (default: False)'
        )
        self.parser.add_argument(
            '-t', '--title',
            default='Posts',
            dest='chart_title',
            required=False,
            help='Chart title (default: "Posts").'
        )
        self.parser.add_argument(
            '-l', '--labels',
            default=None,
            dest='labels',
            required=False,
            help='Labels for the time series (label count needs to match file count) (default: filenames).'
        )
        self.parser.add_argument(
            '-x', '--x-axis-label',
            default=None,
            dest='xlabel',
            required=False,
            help='Label for the x axis (default: "Time window (x minutes)").'
        )
        self.parser.add_argument(
            '-j', '--json-field',
            default=None,
            dest='json_field',
            required=False,
            help='JSON field to use for timestamp, in case the data is not just a timestamp or a tweet (default: "None").'
        )
        self.parser.add_argument(
            '-w', '--window',
            default=15,
            dest='window_mins',
            type=int,
            help='Size of time window to use, in minutes (default: 15)'
        )
        self.parser.add_argument(
            '--fig-width',
            default=5,
            dest='fig_width',
            type=int,
            help='Width of figure (default: 5)'
        )
        self.parser.add_argument(
            '--fig-height',
            default=3,
            dest='fig_height',
            type=int,
            help='Height of figure (default: 3)'
        )
        self.parser.add_argument(
            '--tz-fix',
            default=0,
            dest='tz_fix_mins',
            type=int,
            required=False,
            help='Timezone fix (in minutes) to apply to timestamps provided as epoch milliseconds.'
        )
        self.parser.add_argument(
            '-o', '--out-file',
            dest='out_file',
            default='',
            required=False,
            help='File to write charts to.'
        )


    def parse(self, args=None):
        return self.parser.parse_args(args)


def read_lines(file):
    def open_file(fn):
        if fn[-1] in 'zZ':
            return gzip.open(fn, 'rb')
        else:
            return open(fn, 'r', encoding='utf-8')

    if file:
        with open_file(file) as f:
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
    time_struct = time.strptime(ts_str, fmt)
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


def tw_to_utc_sec(created_at, tz_fix_mins=0):
    try:
        ts = parse_twitter_ts(created_at)  # created_at as a Twitter date
        return timestamp_2_epoch_seconds(ts)
    except TypeError:
        # created_at is milliseconds since epoch instead
        return int(created_at / 1000) + (tz_fix_mins * 60)


def epoch_seconds_2_ts(ts_sec):
    return datetime.fromtimestamp(int(ts_sec))


def load_json_objects(fn):
    try:
        return [json.loads(l) for l in read_lines(fn)]
    except json.decoder.JSONDecodeError as e:
        eprint('Barfed on %s' % fn)
        eprint(str(e))
        return []


def extract(o, prop_path):
    if not prop_path:
        return o
    curr_v = o
    k_idx = 0
    while k_idx < len(prop_path):
        curr_k = prop_path[k_idx]
        curr_v = o[curr_k] if curr_k in o else None
        if not curr_v: break
        k_idx += 1
    return str(curr_v)


NOW_TS_FORMAT='%Y-%m-%d %H:%M:%S'  # 2011-04-26 08:57:23

def now_str(fmt=NOW_TS_FORMAT):
    """ A timestamp string to the current second to use as for logging. """
    return datetime.now().strftime(fmt)


def eprint(*args, **kwargs):
    """Print to stderr"""
    print(*args, file=sys.stderr, flush=True, **kwargs)


DEBUG=False
def log(msg):
    if DEBUG: eprint('[%s] %s' % (now_str(), msg))


if __name__=='__main__':
    options = Options()
    opts = options.parse(sys.argv[1:])

    DEBUG=opts.verbose
    log('Looking at %d files' % len(opts.i_files))

    in_files   = opts.i_files
    out_file   = opts.out_file
    t_mode     = opts.tweets_mode
    json_p     = (opts.json_field.split('.') if opts.json_field else [])
    w_mins     = opts.window_mins
    labels     = (opts.labels.split(',') if opts.labels else in_files)
    title      = opts.chart_title
    tz_fix     = opts.tz_fix_mins
    accum      = opts.cumulative
    log_scale  = opts.log_scale
    dry_run    = opts.dry_run
    fig_width  = opts.fig_width
    fig_height = opts.fig_height
    xlabel     = opts.xlabel if opts.xlabel else 'Time window (%d minutes)' % w_mins
    bar_chart  = opts.bar_chart
    secs       = opts.secs

    log('File count   : %d' % len(in_files))
    log('Out file     : %s' % out_file)
    log('Tweets?      : %s' % t_mode)
    log('Window (mins): %d' % w_mins)
    log('Title        : %s' % title)
    log('TZ fix (mins): %d' % tz_fix)
    log('Cumulative   : %s' % accum)
    log('Log scale    : %s' % log_scale)
    log('Dry run      : %s' % dry_run)
    log('Figure size  : %s' % [fig_width, fig_height])
    log('X axis label : %s' % xlabel)
    log('Bar chart    : %s' % bar_chart)
    log('Epoch secs   : %s' % secs)

    timestamps = {}  # filename/series label : [ts_epoch_sec, ts_epoch_sec, ...]
    count = 0
    for f in in_files:
        series = labels[count]
        count += 1
        if t_mode:
            timestamps[series] = list(map(lambda t: tw_to_utc_sec(t['created_at'], tz_fix), load_json_objects(f)))
        elif json_p:
            timestamps[series] = list(map(lambda o: tw_to_utc_sec(extract(o, json_p), tz_fix), load_json_objects(f)))
        elif secs:
            timestamps[series] = list(map(int, read_lines(f))) #map(format_twitter_ts, read_lines(f)))
        else:
            timestamps[series] = list(map(lambda ts: tw_to_utc_sec(ts, tz_fix), read_lines(f)))
        print('%s (%s): %d entries' % (series, f, len(timestamps[series])))

    # ts_str_to_utc = {}
    first_ts_str  = None
    first_ts      = 10000000000
    final_ts_str  = None
    final_ts      = 0
    for series in timestamps:
        timestamps[series].sort()  # key=lambda ts: tw_to_utc_sec(ts, tz_fix))
        # for ts_str in timestamps[series]:
        #     utc_ts = tw_to_utc_sec(ts_str, tz_fix)
        for utc_ts in timestamps[series]:
            # ts_str_to_utc[ts_str] = utc_ts
            if utc_ts < first_ts:
                first_ts     = utc_ts
                first_ts_str = format_twitter_ts(utc_ts)
            if utc_ts > final_ts:
                final_ts     = utc_ts
                final_ts_str = format_twitter_ts(utc_ts)

    # if isinstance(first_ts_str, int):
    #     first_ts_str = format_twitter_ts(int(first_ts_str / 1000))
    # if isinstance(final_ts_str, int):
    #     final_ts_str = format_twitter_ts(int(final_ts_str / 1000))

    log('Earliest timestamp: %s (%d)' % (first_ts_str, first_ts))
    log('Latest timestamp:   %s (%d)' % (final_ts_str, final_ts))

    w_secs = w_mins * 60
    num_buckets = int(math.ceil((final_ts - first_ts) / w_secs))

    log('Buckets required: %d' % num_buckets)

    log('Calculating buckets (one . per time window)')
    y_values = dict([(s, []) for s in timestamps])
    # TODO: process each file separately, not by window, that way
    # each file is only processed once.
    current_ts = first_ts
    while current_ts < final_ts:
        def in_range(ts): #_str):
            # ts = ts_str_to_utc[ts_str]
            return ts >= current_ts and ts < current_ts + w_secs

        for l in timestamps:
            time_series = timestamps[l]
            # hit_count = len(list(filter(in_range, time_series)))
            hit_count = 0
            for ts in time_series:
                if ts < current_ts: continue # skip early entries
                if ts > current_ts + w_secs: break # jump out once we're past it
                hit_count += 1
            y_values[l].append(hit_count)

        current_ts += w_secs
        if DEBUG: eprint('.', end='')
    log('')

    x_values    = range(1, num_buckets+1)
    x_labels    = [first_ts_str, final_ts_str]
    colours     = cycle('bgrcmk')
    linestyles  = cycle([(), (1,2), (1,5), (1,10)])#(['-', '--', ':', '-.'])

    if DEBUG:
        log('Num buckets: %d' % num_buckets)
        for ts in timestamps:
            # log('[%s]: %s' % (ts, ','.join(map(lambda l: str(l), y_values[ts]))))
            log('File: %s' % ts)
            first_ts_dt = parse_ts(first_ts_str)
            for i in range(len(y_values[ts])):
                log('[%10d]:\t%10d\t%s' % (i, y_values[ts][i], first_ts_dt + timedelta(minutes=w_mins*i)))

    if accum: # accumulate the values in each list
        for l_key in y_values:
            l = y_values[l_key]
            for i in range(1, len(l)):
                l[i] += l[i - 1]

    fig = plt.figure(figsize=(fig_width, fig_height))

    if log_scale:
        plt.yscale('log')

    ax1 = fig.add_subplot(1,1,1)
    ax1.set_title(title)

    ax1.set_xlabel(xlabel)
    # ax1.set_ylabel('Tweets')
    ax1.set_xlim(1, num_buckets)
    # ax1.set_xticks(x_labels)
    # set_y_limit(ax1, y_limits, 0)

    if not bar_chart:
        for l in y_values:
            ax1.plot(x_values, y_values[l], label=l, color=next(colours), linewidth=1)
    else:
        width = 0.9 / len(y_values)
        count = 0
        for l in y_values:
            shift = count*width/(len(y_values)-1) if len(y_values) > 1 else 0
            new_x_values = [x - width/2.0 + shift for x in x_values]
            ax1.bar(new_x_values, y_values[l], width, label=l, color=next(colours), linewidth=1)
            count += 1

    ax1.legend()

    plt.tight_layout()

    if opts.out_file and not dry_run:
        print('Writing to %s' % out_file)
        plt.savefig(out_file)

    if not opts.batch_mode:
        plt.show()
