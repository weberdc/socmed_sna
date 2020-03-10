#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser


import csv
import networkx as nx
import ntpath  # https://stackoverflow.com/a/8384788
import os
import sys


class Options:
    def __init__(self):
        self.usage = 'csv_to_weighted_digraph.py -f <csvfilename> -s <srccol> -t <tgtcol> [-k <kindcol> -v -o <outdir>]'
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
            '-h', '--header',
            action='store_true',
            default=False,
            dest='expect_header',
            help='Expect a header when reading the CSV file (default: False)'
        )
        self.parser.add_argument(
            '--case-insensitive',
            action='store_true',
            default=False,
            dest='case_insensitive',
            help='Force string comparisons to be case-insensitive (default: False)'
        )
        self.parser.add_argument(
            '-s', '--src-col',
            dest='src_col',
            required=True,
            type=int,
            help='Column for source nodes IDs (column index starts at 1)'
        )
        self.parser.add_argument(
            '-t', '--tgt-col',
            dest='tgt_col',
            required=True,
            type=int,
            help='Column for target nodes IDs (column index starts at 1)'
        )
        self.parser.add_argument(
            '-k', '--kind-col',
            default=None,
            dest='type_col',
            type=int,
            help='Column with link types (column index starts at 1)'
        )
        self.parser.add_argument(
            '--src-type',
            dest='src_type',
            default='USER',
            help='Value for n_type property on source nodes (default: USER)'
        )
        self.parser.add_argument(
            '--tgt-type',
            dest='tgt_type',
            default='USER',
            help='Value for n_type property on target nodes (default: USER)'
        )
        self.parser.add_argument(
            '-f', '--csvfile',
            dest='csv_file',
            required=True,
            help='CSV filename to read'
        )
        self.parser.add_argument(
            '-o', '--out-file',
            dest='out_file',
            default=None,
            required=False,
            help='Filename to which to write output (default <infile-".csv">.graphml)'
        )


    def parse(self, args=None):
        return self.parser.parse_args(args)


def extract_parent_dir(filepath, default_dir='./'):
    if not filepath:
        return default_dir

    return os.path.abspath(os.path.join(filepath, os.pardir))


def extract_filename(filepath, default_name='UNKNOWN.txt'):
    if not filepath:
        return default_name

    head, tail = ntpath.split(filepath)
    filename = tail or ntpath.basename(head)
    return os.path.splitext(filename)[0]


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
    log('Inspecting CSV file %s' % opts.csv_file)

    csv_file = opts.csv_file
    src_col  = opts.src_col - 1
    tgt_col  = opts.tgt_col - 1
    type_col = opts.type_col - 1
    out_file = opts.out_file
    header   = opts.expect_header
    src_type = opts.src_type
    tgt_type = opts.tgt_type
    ci       = opts.case_insensitive

    g = nx.DiGraph()
    with open(csv_file, encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=',')   # handles URLs with commas
        line_count = 0
        for row in csv_reader:
            # print('linecount: %d, header: %s' % (line_count, header))
            line_count += 1
            if line_count == 1 and header:
                continue

            src = row[src_col]
            tgt = row[tgt_col]
            e_t = row[type_col]

            if ci:
                src = src.lower()
                tgt = tgt.lower()

            if g.has_edge(src, tgt):
                g[src][tgt]['weight'] += 1.0
            else:
                if not g.has_node(src): g.add_node(src, label=src, n_type=src_type)
                if not g.has_node(tgt): g.add_node(tgt, label=tgt, n_type=tgt_type)
                g.add_edge(src, tgt, weight=1.0, e_type=e_t)

            line_count += 1

    if not out_file:
        out_file = os.path.join(out_dir, '%s.graphml' % extract_filename(csv_file))
    parent_dir = extract_parent_dir(out_file)
    if not os.path.exists(parent_dir):
        os.mkdir(parent_dir)
    nx.write_graphml(g, out_file)

    log('Wrote graph to %s' % out_file)
