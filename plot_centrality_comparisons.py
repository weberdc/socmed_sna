#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser
from datetime import datetime, timedelta
from itertools import cycle
from plot_ranked_items import calc_nasim


import csv
import json
import math
import matplotlib.pyplot as plt
import os
import os.path
import sys
import time


#
# Given a CSV (header optional) with two columns, each including the same
# values in potentially different orders, this will generate a scatter plot
# of the values using their ranks as x and y coordinates.
#


class Options:
    def __init__(self):
        self.usage = 'plot_centrality_comparisons.py -f <ranked_items.csv> [options]'
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
            dest='in_filebase',
            required=True,
            help='File base for two-column CSVs of ranked items (all items appear in each column)'
        )
        self.parser.add_argument(
            '-l', '--labels',
            default=None,
            dest='labels',
            required=True,
            help='Labels for the axes (default: "X" and "Y").'
        )
        self.parser.add_argument(
            '-t', '--title',
            default=None,
            dest='title',
            required=False,
            help='Overall chart title (default: provided filebase).'
        )
        self.parser.add_argument(
            '--header',
            action='store_true',
            default=False,
            dest='expect_header',
            help='Expect a header in the CSV input (default: False)'
        )
        self.parser.add_argument(
            '-g', '--grey',
            action='store_true',
            default=False,
            dest='grey',
            help='Use greyscale for the chart points to refer to rank (default: False)'
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


def load_xy_data(fb, interaction, centrality, header, algo):
    results = {'x_values': [], 'y_values': []}

    filename = '%s-%s-%s.csv' % (fb, interaction, centrality)

    if not os.path.exists(filename):
        return results

    ranked_items = []

    with open(filename, 'r', encoding='utf-8') as f:
        count = 0
        for l in f:
            count += 1
            if count > 1 or not header:
                ranked_items.append(l.strip().split(','))

    column2 = list(map(lambda t: t[1], ranked_items))

    if algo == 'NASIM':
        x_values, y_values = calc_nasim(ranked_items)
        results['x_values'] = x_values
        results['y_values'] = y_values
    if algo == 'SIMPLE':
        for pair in ranked_items:
            results['x_values'].append(pair[0])
            results['y_values'].append(column2.index(pair[0]))

    return results


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
    out_file = opts.out_file
    header   = opts.expect_header
    labels   = opts.labels.split(',')
    title    = opts.title if opts.title else in_fb
    algo     = opts.algo
    grey     = opts.grey

    data = {}
    cmaps = {}
    interactions = ['mentions', 'replies']
    centralities = ['DEGREE', 'BETWEENNESS', 'CLOSENESS', 'EIGENVECTOR']
    for interaction in interactions:
        for centrality in centralities:
            key = '%s-%s' % (interaction, centrality)
            data[key] = load_xy_data(in_fb, interaction, centrality, header, algo)
            count = len(data[key]['x_values'])
            cmaps[key] = [str(((i / count) * 0.8) + 0.1) for i in range(count)]

    # fig = plt.figure(figsize=(15,7))
    fig, axes = plt.subplots(2, 4, figsize=(15,7))
    st = fig.suptitle(title, fontsize='x-large')

    for row in range(2):
        for col in range(4):
            ax = fig.add_subplot(axes[row][col])

            # had to put these three lines first to remove the y ticks and labels
            # see https://stackoverflow.com/a/45824309
            key = '%s-%s' % (interactions[row], centralities[col])
            c_value = cmaps[key] if grey else 'b'
            ax.scatter(data[key]['x_values'], data[key]['y_values'], marker='o', c=c_value)  # cmaps[key])  # 'b')

            count = len(data[key]['x_values'])
            chart_title = 'Top %d ranked %s by\n%s centrality' % (
                count, interactions[row], centralities[col]
            )
            ax.set_title(chart_title)
            ax.set_xlabel(labels[0])
            y_label = labels[1] + (' score' if algo == 'NASIM' else '')
            ax.set_ylabel(y_label)  # labels[1])
            ax.set_xticks([])
            if count == 0:
                ax.set_yticks([])

    fig.tight_layout()

    # shift subplots down to make room for the overall label
    st.set_y(0.95)
    fig.subplots_adjust(top=0.85)

    plt.savefig(out_file)

    if not opts.batch_mode:
        plt.show()
