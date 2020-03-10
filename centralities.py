#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser
from copy import deepcopy


import csv
import heapq
import networkx as nx
import ntpath  # https://stackoverflow.com/a/8384788
import os
import sys


class Options:
    def __init__(self):
        self.usage = 'centralities.py -f <graphmlfilename>'
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
            '-x', '--top-x',
            dest='top_x',
            default=20,
            type=int,
            help='Top x results to list (default: 20)'
        )
        self.parser.add_argument(
            '-f', '--file',
            dest='graphml_file',
            required=True,
            help='GraphML filename to read'
        )


    def parse(self, args=None):
        return self.parser.parse_args(args)


def extract_filename(filepath, default_name='UNKNOWN.txt'):
    if not filepath:
        return default_name

    head, tail = ntpath.split(filepath)
    filename = tail or ntpath.basename(head)
    return os.path.splitext(filename)[0]


def get_top(top_x, kv_map):
    heap = []
    for k in kv_map:
        v = kv_map[k]
        # If we have not yet found top_x items, or the current item is larger
        # than the smallest item on the heap,
        if len(heap) < top_x or v > heap[0][1]:  # [1] is the value
            # If the heap is full, remove the smallest element on the heap.
            if len(heap) == top_x: heapq.heappop( heap )
            # Add the current element as the new smallest.
            heapq.heappush( heap, (k,v) )

    # Sort tuples by largest value first
    heap.sort(key=lambda kv: kv[1], reverse=True)

    return heap


def average(l):
    return sum(l)/len(l) if len(l) else 0


def pad(kv_list, k, v):
    if len(kv_list) < k:
        return kv_list + [deepcopy(v) for i in k - len(kv_list)]
    else:
        return kv_list


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
    log('Inspecting GraphML file %s' % opts.graphml_file)

    gf = opts.graphml_file
    fn = extract_filename(gf)
    g  = nx.read_graphml(gf)

    degree_cs = nx.degree_centrality(g)
    betw_cs   = nx.betweenness_centrality(g, weight='weight')
    close_cs  = nx.closeness_centrality(g, distance='weight')
    eigen_cs  = nx.eigenvector_centrality(g, weight='weight')

    ave_degree_c = average(degree_cs.values())
    ave_betw_c   = average(betw_cs.values())
    ave_close_c  = average(close_cs.values())
    ave_eigen_c  = average(eigen_cs.values())

    x = opts.top_x
    top_x_degree_cs = pad(get_top(x, degree_cs), x, ('', 0))
    top_x_betw_cs   = pad(get_top(x, betw_cs),   x, ('', 0))
    top_x_close_cs  = pad(get_top(x, close_cs),  x, ('', 0))
    top_x_eigen_cs  = pad(get_top(x, eigen_cs),  x, ('', 0))

    print('Filename,AveDegC,AveBetwC,AveCloseC,AveEigenC')
    print('%s,%s,%s,%s,%s\n' % (fn, ave_degree_c, ave_betw_c, ave_close_c, ave_eigen_c))

    print('DegNodeID,DegC,BetwNodeID,BetwC,CloseNodeID,CloseC,EigenNodeID,EigenC')
    for i in range(x):
        d = top_x_degree_cs[i]
        b = top_x_betw_cs[i]
        c = top_x_close_cs[i]
        e = top_x_eigen_cs[i]
        print(','.join(['"%s",%s']*4) % (d[0],d[1],b[0],b[1],c[0],c[1],e[0],e[1]))
