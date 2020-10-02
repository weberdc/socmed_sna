#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser
from copy import deepcopy


import csv
import heapq
import networkx as nx
import ntpath  # https://stackoverflow.com/a/8384788
import operator
import os
import scipy.stats as stats
import sys


def safe_eigenvector(g):
    try:
        return nx.eigenvector_centrality(g, weight='weight')
    except nx.PowerIterationFailedConvergence:
        log('power iteration failed to converge within 100 iterations')
        return dict([(n, 0.0) for n in g.nodes()])

CENTRALITY_FUNCTIONS = {
    'DEGREE'      : lambda g: nx.degree_centrality(g),
    'BETWEENNESS' : lambda g: nx.betweenness_centrality(g, weight='weight'),
    'CLOSENESS'   : lambda g: nx.closeness_centrality(g, distance='weight'),
    'EIGENVECTOR' : safe_eigenvector
}
class Options:
    def __init__(self):
        self.usage = 'compare_centralities.py -f1 <graphmlfilename> -f2 <graphmlfilename> -t (DEGREE|BETWEENNESS|CLOSENESS|EIGENVECTOR) [-x <top_x>]'
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
            dest='incl_header',
            help='Include a header in the (CSV) output (default: False)'
        )
        self.parser.add_argument(
            '-x', '--top-x',
            dest='top_x',
            default=20,
            type=int,
            help='Top x results to list (default: 20)'
        )
        self.parser.add_argument(
            '-t', '--type',
            dest='c_type',
            default='D',
            choices=list(CENTRALITY_FUNCTIONS.keys()),
            help='Centrality metric (default: degree)'
        )
        self.parser.add_argument(
            '-f1', '--file1',
            dest='graphml_file1',
            required=True,
            help='GraphML filename to read'
        )
        self.parser.add_argument(
            '-f2', '--file2',
            dest='graphml_file2',
            required=True,
            help='GraphML filename to read'
        )
        self.parser.add_argument(
            '-o', '--out-file',
            dest='out_file',
            default='ranked_nodes.csv',
            help='Top common ranked nodes from each file (default: ranked_nodes.csv)'
        )


    def parse(self, args=None):
        return self.parser.parse_args(args)


def extract_filename(filepath, default_name='UNKNOWN.txt'):
    if not filepath:
        return default_name

    head, tail = ntpath.split(filepath)
    filename = tail or ntpath.basename(head)
    return os.path.splitext(filename)[0]


def extract_parent_dir(filepath, default_dir='./'):
    if not filepath:
        return default_dir

    return os.path.abspath(os.path.join(filepath, os.pardir))


def get_top(top_x, kv_tuples):
    heap = []
    for kv in kv_tuples:
        k,v = kv
        # v = kv_map[k]
        # If we have not yet found top_x items, or the current item is larger
        # than the smallest item on the heap,
        if len(heap) < top_x or v > heap[0][1]:  # [1] is the value
            # If the heap is full, remove the smallest element on the heap.
            if len(heap) == top_x: heapq.heappop( heap )
            # Add the current element as the new smallest.
            heapq.heappush( heap, (k,v) )

    # Sort tuples by largest value first
    # heap.sort(key=lambda kv: kv[1], reverse=True)
    heap.sort(key=operator.itemgetter(1), reverse=True)  # faster than lambda x: x[1])

    return heap


def log_top_x(ids1, ids2):
    top_x = min(len(ids1), len(ids2))  # in case len(ids1) or len(ids2) < top_x
    log('Revised top x: %d' % top_x)
    anon_ids = {}
    counter = 1
    all_ids = ids1 + ids2
    widest_id = 0
    widest_anon = 0
    ids_in_common = set(ids1).intersection(ids2)
    log('Revised in common: %d' % len(ids_in_common))
    for i in range(len(all_ids)):  # anon IDs make them easier to compare
        id = all_ids[i]
        if id not in anon_ids:
            anon_ids[id] = ('%s*' if id in common_ids else '%s') % counter
            counter += 1
        if len(str(id)) > widest_id: widest_id = len(str(id))
        if len(anon_ids[id]) > widest_anon: widest_anon = len(anon_ids[id])

    for i in range(top_x):
        id1 = ids1[i]
        id2 = ids2[i]
        log('%s (%s)\t%s (%s)' % (
            str(id1).ljust(widest_id), anon_ids[id1].rjust(widest_anon),
            str(id2).ljust(widest_id), anon_ids[id2].rjust(widest_anon)
        ))


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

    gf1 = opts.graphml_file1
    gf2 = opts.graphml_file2
    fn1 = extract_filename(gf1)
    fn2 = extract_filename(gf2)
    log('f1: %s' % fn1)
    log('f2: %s' % fn2)

    g1  = nx.read_graphml(gf1)
    g2  = nx.read_graphml(gf2)

    log('G1: %d' % len(g1))
    log('G2: %d' % len(g2))
    common_ids = set(g1.nodes()).intersection(g2.nodes())
    log('in common: %d' % len(common_ids))

    cs1 = CENTRALITY_FUNCTIONS[opts.c_type](g1)
    cs2 = CENTRALITY_FUNCTIONS[opts.c_type](g2)

    in_common_ids = lambda t: t[0] in common_ids
    first = lambda t: t[0]
    cs1_topx = list(map(first, get_top(opts.top_x, filter(in_common_ids, cs1.items()))))
    cs2_topx = list(map(first, get_top(opts.top_x, filter(in_common_ids, cs2.items()))))

    log('cs1_topx: %d' % len(cs1_topx))
    log('cs2_topx: %d' % len(cs2_topx))

    topx_common_ids = set(cs1_topx).intersection(cs2_topx)

    in_topx_common_ids = lambda id: id in topx_common_ids
    cs1_topx = list(map(str, filter(in_topx_common_ids, cs1_topx)))
    cs2_topx = list(map(str, filter(in_topx_common_ids, cs2_topx)))

    if DEBUG: log_top_x(cs1_topx, cs2_topx)

    try:
        tau, tau_p_value = stats.kendalltau(cs1_topx, cs2_topx, nan_policy='omit')
    except OverflowError as e:
        eprint('Overflow error: %s' % e)
        tau, tau_p_value = (0, 0)
    rho, rho_p_value = stats.spearmanr(cs1_topx, cs2_topx)

    if opts.incl_header:
        print('top_x,in_common,tau,tau_p-value,rho,rho_p-value')
    print('%d,%d,%s,%s,%s,%s' % (
        opts.top_x, len(topx_common_ids),
        tau, tau_p_value,
        rho, rho_p_value
    ))

    with open(opts.out_file, 'w', encoding='utf-8') as f:
        f.write('%s,%s\n' % (fn1, fn2))
        for i in range(len(topx_common_ids)):
            f.write('%s,%s\n' % (cs1_topx[i], cs2_topx[i]))
