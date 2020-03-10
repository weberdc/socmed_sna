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
        self.usage = 'csv_to_co-occurrence_weighted_graph.py -f <csvfilename> -n <nodecol> -w <weightcol> -o <outfile> [-v --header]'
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
            '-n', '--node-col',
            dest='node_col',
            required=True,
            type=int,
            help='Column for node IDs (column index starts at 1)'
        )
        self.parser.add_argument(
            '-u', '--unique-col',
            dest='id_col',
            required=True,
            type=int,
            help='Column for distinguishing co-occurrence of nodes (column index starts at 1)'
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
    node_col = opts.node_col - 1
    id_col   = opts.id_col - 1
    out_file = opts.out_file
    header   = opts.expect_header
    ci       = opts.case_insensitive

    log('csv_file: %s' % csv_file)
    log('node_col: %s' % node_col)
    log('id_col:   %s' % id_col)
    log('out_file: %s' % out_file)
    log('header:   %s' % header)
    log('case-ins: %s' % ci)

    cooccurrences = {}  # tweet ID: [hashtags]
    with open(csv_file, encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=',')   # handles URLs with commas
        line_count = 0
        for row in csv_reader:
            # log('linecount: %d, header: %s, row: %s' % (line_count, header, row))
            line_count += 1
            # print(len(row))
            # print('%s' % (not len(row)))
            if not len(row) or (line_count == 1 and header):
                continue

            node = row[node_col]
            t_id = row[id_col]

            if ci:
                node = node.lower()

            if t_id in cooccurrences:
                cooccurrences[t_id].append(node)
            else:
                cooccurrences[t_id] = [node]

    log(cooccurrences)
    g = nx.Graph()
    for t_id in cooccurrences:
        if len(cooccurrences[t_id]) > 1:
            nodes = cooccurrences[t_id]
            for i in range(len(nodes) - 1):
                for j in range(i+1, len(nodes)):
                    log('[%d,%d]' % (i,j))
                    n1 = nodes[i]
                    n2 = nodes[j]
                    if n1 not in g: g.add_node(n1, label=n1)
                    if n2 not in g: g.add_node(n2, label=n2)
                    if g.has_edge(n1, n2):
                        g[n1][n2]['weight'] += 1.0
                    else:
                        g.add_edge(n1, n2, weight=1.0)

    for u,v,d in g.edges(data=True):
        d['label'] = '%d' % d['weight']

    if not out_file:
        out_file = os.path.join(out_dir, '%s-cooccurrence.graphml' % extract_filename(csv_file))
    parent_dir = extract_parent_dir(out_file)
    if not os.path.exists(parent_dir):
        os.mkdir(parent_dir)
    nx.write_graphml(g, out_file)

    print('Wrote graph to %s' % out_file)
