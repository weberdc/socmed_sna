#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser
from community import community_louvain
from numpy import array, zeros
from sklearn.metrics.cluster import adjusted_rand_score


import json
import networkx as nx
import ntpath  # https://stackoverflow.com/a/8384788
import numpy
import os
import sys


#
# Given two GraphML graphs, extract clusters using the Louvain method and do
# a pairwise similarity comparison of those clusters using a Jaccard-style
# similarity calculation. Output the results as a table, with columns and rows
# reordered to maximise diagonality.
#


class Options:
    def __init__(self):
        self.usage = 'compare_communities.py [options] -f1 <g1.graphml> -f2 <g2.graphml>'
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
            '-f1', '--file1',
            default=None,
            dest='file1',
            required=True,
            help='First GraphML file.'
        )
        self.parser.add_argument(
            '-f2', '--file2',
            default=None,
            dest='file2',
            required=True,
            help='Second GraphML file.'
        )
        self.parser.add_argument(
            '-x', '--top-x',
            dest='top_x',
            default=20,
            type=int,
            help='Top x results to compare (default: 20)'
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


def compare_communities(c1, c2):
    # log('c1: %d, c2: %d' % (len(c1), len(c2)))
    numerator   = len(set(c1).intersection(c2))
    denominator = len(set(c1).union(c2))
    return numerator / denominator  # |communities in common| / |unique communities| 


def keep_top_x(x, communities):
    as_list = list(communities.items())  # convert the key/value entries to tuples
    as_list.sort(key=lambda t: len(t[1]), reverse=True)  # sort the tuples by the community size
    return dict(as_list[:x])  # turn the remaining tuples back into a dictionary


def key_by_community(partition):
    # partition is keyed by node, whereas we want a map keyed by the community ID
    cmap = {}
    for n in partition.keys():
        c = partition[n]
        community = cmap.get(c, [])
        community.append(n)
        cmap[c] = community
    return cmap


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
    print('Comparing communities detected in graphs %s and %s' % (opts.file1, opts.file2))

    f1 = opts.file1
    f2 = opts.file2

    g1 = nx.read_graphml(f1).to_undirected()
    g2 = nx.read_graphml(f2).to_undirected()

    print('graph1 %d nodes' % len(g1))
    print('graph2 %d nodes' % len(g2))

    partition1 = community_louvain.best_partition(g1, weight='weight')
    partition2 = community_louvain.best_partition(g2, weight='weight')
    
    # do the RandIndex comparison (on the entire lists)
    def get_1st(t): return t[0]
    def get_2nd(t): return t[1]
    part1_items = list(partition1.items())
    part1_items.sort(key=get_1st)
    part2_items = list(partition2.items())
    part2_items.sort(key=get_1st)
    
    # - strip down to common IDs
    part1_ids = set(map(str, g1.nodes()))
    part2_ids = set(map(str, g2.nodes()))
    common_ids = part1_ids.intersection(part2_ids)
    print('Common nodes: %d' % len(common_ids))
    print('Common edges: %d' % len(g1.subgraph(common_ids).edges))

    # - extract the labels
    def in_common(t): return get_1st(t) in common_ids
    part1_community_labels = list(map(get_2nd, filter(in_common, part1_items)))
    part2_community_labels = list(map(get_2nd, filter(in_common, part2_items)))
        
    # - compare part1_community_labels and part2_community_labels with randindex
    # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html
    print('ARI: %s' % str(adjusted_rand_score(part1_community_labels, part2_community_labels)))
    print('Reversed ARI: %s' % str(adjusted_rand_score(part2_community_labels, part1_community_labels)))
    
    # do the pairwise comparison
    all_communities1 = key_by_community(partition1)
    all_communities2 = key_by_community(partition2)
    
    print('communities1: %d' % len(all_communities1))
    print('communities2: %d' % len(all_communities2))

    communities1 = keep_top_x(opts.top_x, all_communities1)
    communities2 = keep_top_x(opts.top_x, all_communities2)

    print('top x community1 %d nodes' % sum([len(c) for c in communities1.values()]))
    print('top x community2 %d nodes' % sum([len(c) for c in communities2.values()]))

    print('Top ' + str(opts.top_x) + ' sizes1, %s' % str(sorted(list(map(len, communities1.values())), reverse=True))[1:-1])
    print('Top ' + str(opts.top_x) + ' sizes2, %s' % str(sorted(list(map(len, communities2.values())), reverse=True))[1:-1])

    # communities2 are the rows, communities1 are the columns
    table = zeros([len(communities2), len(communities1)])

    r = 0
    for c2_id in communities2:
        c = 0
        for c1_id in communities1:
            # log('Generating [%d,%d]' % (r,c))
            # community IDs are 1-indexed, arrays are 0-indexed
            c1 = communities1[c1_id]
            c2 = communities2[c2_id]
            table[r,c] = compare_communities(c1, c2)
            c += 1
        r += 1

    log('Table shape: %s' % str(table.shape))

    column_indices = numpy.argmax(table, axis=1)
    sorted_table = table[:, column_indices]

    row_indices = numpy.argmax(table, axis=0)
    sorted_table = sorted_table[:, row_indices]

    table = sorted_table

#    print(table)

    column_labels = [
        '%s (%d)' % (list(communities1.keys())[idx],len(communities1[list(communities1.keys())[idx]])) 
        for idx in column_indices
    ]
    row_labels = [
        '%s (%d)' % (list(communities2.keys())[idx],len(communities2[list(communities2.keys())[idx]]))
        for idx in row_indices
    ]

    table_str = 'F1 v|F2 >,%s\n' % ','.join(map(str, column_labels))
    r = 0
    for c2_id in communities2:
        c = 0
        table_str += '%s,' % row_labels[r]
        for c1_id in communities1:
            cell = table[r,c]
            table_str += '%s,' % cell
            c += 1
        table_str = table_str[:-1] + '\n'  # replace trailing comma with a newline
        r += 1
    print(table_str)

    fn1 = extract_filename(f1)
    dir1 = extract_parent_dir(f1)
    out1 = os.path.join(dir1, '%s-top-%d-communities.json' % (fn1, opts.top_x))
    with open(out1, 'w', encoding='utf-8') as f:
        f.write(json.dumps(all_communities1))
        f.write('\n')

    fn2 = extract_filename(f2)
    dir2 = extract_parent_dir(f2)
    out2 = os.path.join(dir2, '%s-top-%d-communities.json' % (fn2, opts.top_x))
    with open(out2, 'w', encoding='utf-8') as f:
        f.write(json.dumps(all_communities2))
        f.write('\n')
