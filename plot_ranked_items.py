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
import sys
import time


#
# Given a CSV (header optional) with two columns, each including the same
# values in potentially different orders, this will generate a scatter plot
# of the values using their ranks as x and y coordinates.
#

class Options:
    def __init__(self):
        self.usage = 'plot_per_time_metrics.py -f <ranked_items.csv> [options]'
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
            '-f', '--file',
            default=None,
            dest='csv_file',
            required=True,
            help='Two column CSV of ranked items (all items appear in each column)'
        )
        self.parser.add_argument(
            '-l', '--labels',
            default=None,
            dest='labels',
            required=False,
            help='Labels for the axes (default: "X" and "Y").'
        )
        self.parser.add_argument(
            '-t', '--title',
            default='Ranked by centrality',
            dest='title',
            required=False,
            help='Chart title (default: "Ranked by centrality").'
        )
        self.parser.add_argument(
            '--header',
            action='store_true',
            default=False,
            dest='expect_header',
            help='Expect a header in the CSV input (default: False)'
        )
        self.parser.add_argument(
            '-o', '--out-file',
            dest='out_file',
            default='out.png',
            required=True,
            help='File to which to write scatterplot'
        )
        self.parser.add_argument(
            '-a', '--algorithm',
            dest='algo',
            default='SIMPLE',
            choices=['SIMPLE', 'NASIM'],
            help='Plotting algorithm (default: SIMPLE)'
        )


    def parse(self, args=None):
        return self.parser.parse_args(args)


def calc_simple(ranked_items):
    column2 = list(map(lambda t: t[1], ranked_items))

    x_values = []
    y_values = []

    for pair in ranked_items:
        x_values.append(pair[0])
        y_values.append(column2.index(pair[0]))

    return (x_values, y_values)


def calc_nasim(ranked_items):
    num_items = len(ranked_items)
    column1   = list(map(lambda t: t[0], ranked_items))
    column2   = list(map(lambda t: t[1], ranked_items))

    # rank is higher for earlier items (i.e. 1st item has rank column length - 1)
    # list [a,b,c,d,e,f] is given list of ranks [5,4,3,2,1,0]
    col1_ranks = [(num_items - column1.index(id) - 1) for id in column1]
    col2_ranks = [(num_items - column2.index(id) - 1) for id in column1]

    x_values = col1_ranks
    y_values = []

    for i in range(num_items):
        r = col2_ranks[i]
        y = len(list(filter(lambda v: r > v, col2_ranks[i+1:])))
        y_values.append(y)

    return (x_values, y_values)


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
    log('Looking at files starting with %s' % opts.csv_file)

    in_csv = opts.csv_file
    out_file = opts.out_file
    header = opts.expect_header
    chart_title = opts.title
    labels = ['X', 'Y']
    if opts.labels:
        labels = opts.labels.split(',')

    ranked_items = []
    with open(in_csv, 'r') as f:
        count = 0
        for l in f:
            count += 1
            if header and count == 1:
                if not opts.labels:
                    labels = l.strip().split(',')
            elif len(l.strip()):
                ranked_items.append(l.strip().split(','))

    if opts.algo == 'NASIM':
        x_values, y_values = calc_nasim(ranked_items)
    else:
        x_values, y_values = calc_simple(ranked_items)

    fig = plt.figure(figsize=(7,7))

    ax = fig.add_subplot(1,1,1)
    ax.set_title(chart_title)
    ax.set_xlabel(labels[0])
    ax.set_ylabel(labels[1])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.scatter(x_values, y_values, marker='o', c='b')

    if DEBUG:
        for i, txt in enumerate(list(map(lambda t: t[0], ranked_items))):
            label = '%s(%d,%d)' % (txt, x_values[i], y_values[i])
            ax.annotate(label, (x_values[i], y_values[i]))

    plt.tight_layout()
    plt.savefig(out_file)

    if not opts.batch_mode:
        plt.show()
