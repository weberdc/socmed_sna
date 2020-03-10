#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime


import csv
import heapq
import json
import math
import networkx as nx
import ntpath  # https://stackoverflow.com/a/8384788
import operator
import os
import scipy.stats as stats
import sys
import time


CENTRALITY_FUNCTIONS = {
    'DEGREE'      : lambda g: nx.degree_centrality(g),
    'BETWEENNESS' : lambda g: nx.betweenness_centrality(g, weight='weight'),
    'CLOSENESS'   : lambda g: nx.closeness_centrality(g, distance='weight'),
    'EIGENVECTOR' : lambda g: nx.eigenvector_centrality_numpy(g, weight='weight')
}
GRAPH_TYPES = ['RETWEET','REPLY','QUOTE','MENTION','RTQT']
class Options:
    def __init__(self):
        self.usage = 'compare_centralities_longitudinally_from_tweets.py -f1 <tweets_file1> -f2 <tweets_file2> -w <window_in_mins> -c (DEGREE|BETWEENNESS|CLOSENESS|EIGENVECTOR) -t (REPLY|RETWEET|QUOTE|MENTION|RTQT) [-x <top_x>]'
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
            '--cumulative',
            action='store_true',
            default=False,
            dest='cumulative',
            help='Turn on cumulative calculations (default: False)'
        )
        # self.parser.add_argument(
        #     '-h', '--header',
        #     action='store_true',
        #     default=False,
        #     dest='incl_header',
        #     help='Include a header in the (CSV) output (default: False)'
        # )
        self.parser.add_argument(
            '-x', '--top-x',
            dest='top_x',
            default=20,
            type=int,
            help='Top x results to list (default: 20)'
        )
        self.parser.add_argument(
            '-c', '--centrality',
            dest='c_type',
            required=True,  # default='DEGREE',
            choices=list(CENTRALITY_FUNCTIONS.keys()),
            help='Centrality metric (default: DEGREE)'
        )
        self.parser.add_argument(
            '-t', '--graph-type',
            dest='g_type',
            required=True,  # default=GRAPH_TYPES[0],
            choices=GRAPH_TYPES,
            help='Graph type to analyse (options: %s, default: %s)' % (str(GRAPH_TYPES), GRAPH_TYPES[0])
        )
        self.parser.add_argument(
            '-f1', '--tweets1',
            dest='tweets_file1',
            required=True,
            help='First file of tweets to analyse'
        )
        self.parser.add_argument(
            '-f2', '--tweets2',
            dest='tweets_file2',
            required=True,
            help='First file of tweets to analyse'
        )
        self.parser.add_argument(
            '-w', '--window',
            dest='window_mins',
            required=True,
            type=int,
            help='Window size to use (in minutes)'
        )
        # self.parser.add_argument(
        #     '-o', '--out-file',
        #     dest='out_file',
        #     default='ranked_nodes.csv',
        #     help='Top common ranked nodes from each file (default: ranked_nodes.csv)'
        # )


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


def read_lines(file=None):
    """Gets the lines from the given file or stdin if it's None or '' or '-'."""
    if file and file != '-':
        with open(file, 'r', encoding='utf-8') as f:
            return [l.strip() for l in f.readlines()]
    else:
        return [l.strip() for l in sys.stdin]


def load_tweets(tweets_file):
    tweets = []
    for line in read_lines(tweets_file):
        # read tweet from JSON
        tweet = json.loads(line)
        tweet['ts'] = timestamp_2_epoch_seconds(parse_ts(tweet['created_at']))
        tweets.append(tweet)

    tweets.sort(key=lambda t: t['ts'])
    return tweets


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


def timestamp_2_epoch_seconds(ts):
    return int(time.mktime(ts.timetuple()))


TWITTER_TS_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'  #Tue Apr 26 08:57:55 +0000 2011
ARG_TS_FORMAT = '%Y-%m-%d %H:%M' # 2016-12-25 7:53


def parse_ts(ts_str, fmt=TWITTER_TS_FORMAT):
    # print(ts_str)
    time_struct = time.strptime(ts_str, fmt)
    return datetime.fromtimestamp(time.mktime(time_struct))


def get_ts_extrema(tweets1, tweets2, idx, comp_func):
    ts = comp_func(tweets1[idx]['ts'], tweets2[idx]['ts'])
    ts_str = tweets1[idx]['created_at'] if tweets1[idx]['ts'] == ts else tweets2[idx]['created_at']
    return (ts, ts_str)


def fill_buckets(tweets, buckets, bucket_span_secs, first_ts):
    current_bucket_idx = 0
    for t in tweets:
        current_bucket_idx = int(math.floor((t['ts'] - first_ts) / bucket_span_secs))
        buckets[current_bucket_idx].append(t)


def build_graph(tweets, g_type):
    g = nx.DiGraph()
    def link(src, tgt):
        if g.has_edge(src, tgt):
            g[src][tgt]['weight'] += 1
        else:
            g.add_edge(src, tgt, weight=1, edge_type=g_type)

    for t in tweets:
        if g_type in ['RETWEET', 'RTQT'] and 'retweeted_status' in t and t['retweeted_status'] != None:
            link(t['user']['id_str'], t['retweeted_status']['user']['id_str'])
        elif g_type in ['QUOTE', 'RTQT'] and 'quoted_status' in t and t['quoted_status'] != None:
            link(t['user']['id_str'], t['quoted_status']['user']['id_str'])
        elif g_type == 'REPLY' and t['in_reply_to_status_id_str'] != None:
            link(t['user']['id_str'], t['in_reply_to_user_id_str'])
        elif g_type == 'MENTION' and len(t['entities']['user_mentions']) > 0:
            mentions = t['entities']['user_mentions']
            if 'extended_tweet' in t:
                mentions = t['extended_tweet']['entities']['user_mentions']
            for m in mentions:
                link(t['user']['id_str'], m['id_str'])

    return g


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

    tweets_file1 = opts.tweets_file1
    tweets_fn1 = extract_filename(tweets_file1)
    tweets_file2 = opts.tweets_file2
    tweets_fn2 = extract_filename(tweets_file2)
    w_mins = opts.window_mins
    top_x = opts.top_x
    g_type = opts.g_type
    c_type = opts.c_type
    cumulative = opts.cumulative
    log('Tweets file #1: %s' % tweets_fn1)
    log('Tweets file #2: %s' % tweets_fn2)
    log('Window (mins): %d' % w_mins)
    log('Top X: %d' % top_x)
    log('Graph: %s' % g_type)
    log('Centrality: %s' % c_type)
    log('Cumulative: %s' % cumulative)

    tweets1 = load_tweets(tweets_file1)
    tweets2 = load_tweets(tweets_file2)
    log('Tweets in #1: %d' % len(tweets1))
    log('Tweets in #2: %d' % len(tweets2))

    (first_ts, first_ts_str) = get_ts_extrema(tweets1, tweets2, 0, min)
    (last_ts, last_ts_str)   = get_ts_extrema(tweets1, tweets2, -1, max)
    duration_secs = last_ts - first_ts
    log('First: %s (UTC %d)' % (first_ts_str, first_ts))
    log('Last:  %s (UTC %d)' % (last_ts_str, last_ts))

    bucket_span_secs = w_mins * 60
    num_buckets = int(duration_secs / bucket_span_secs) + 1
    log('Buckets required: %d' % num_buckets)

    buckets1 = [[] for i in range(num_buckets)]
    buckets2 = [[] for i in range(num_buckets)]
    fill_buckets(tweets1, buckets1, bucket_span_secs, first_ts)
    fill_buckets(tweets2, buckets2, bucket_span_secs, first_ts)

    if cumulative:
        for i in range(1, num_buckets):
            buckets1[i] = buckets1[i-1] + buckets1[i]
            buckets2[i] = buckets2[i-1] + buckets2[i]

    log('Buckets,%s,%s' % (tweets_fn1, tweets_fn2))
    for i in range(num_buckets):
        r = 'bucket %2d:\t%d\t%d' % (i+1, len(buckets1[i]), len(buckets2[i]))
        r += '\t%d' % (first_ts + i * bucket_span_secs)
        def ts_str(bucket, idx):
            return '%s [%d]' % (bucket[idx]['created_at'], bucket[idx]['ts']) if len(bucket) != 0 else 'XXX [0]'
        r += '\t(%s - %s)' % (ts_str(buckets1[i], 0), ts_str(buckets1[i], -1))
        r += '\t(%s - %s)' % (ts_str(buckets2[i], 0), ts_str(buckets2[i], -1))
        log(r)
        # log('bucket %2d:\t%d\t%d' % (i+1, len(buckets1[i]), len(buckets2[i])))
        # log('bucket %2d:\t%d\t%d\t(%s - %s)\t(%s - %s)' % (i+1, len(buckets1[i]), len(buckets2[i]), buckets1[i][0]['created_at'], buckets1[i][-1]['created_at'], buckets2[i][0]['created_at'], buckets1[i][-1]['created_at']))
        # log('bucket %2d:\t%d\t%d\t(%s[%d] - %s[%d])\t(%s[%d] - %s[%d])' % (i+1, len(buckets1[i]), len(buckets2[i]), buckets1[i][0]['created_at'], buckets1[i][0]['ts'], buckets1[i][-1]['created_at'], buckets1[i][-1]['ts'], buckets2[i][0]['created_at'], buckets2[i][0]['ts'], buckets2[i][-1]['created_at'], buckets2[i][-1]['ts']))
    log('Total:\t%d\t%d' % (len(tweets1), len(tweets2)))

    # create graphs
    graphs1 = []
    graphs2 = []
    for tweets in (buckets1 + [tweets1]):
        graphs1.append(build_graph(tweets, g_type))
    for tweets in (buckets2 + [tweets2]):
        graphs2.append(build_graph(tweets, g_type))

    log('G\tnodes,edges\tnodes,edges')
    for i in range(len(graphs1)):
        log('%d\t%d,%d\t%d,%d' % (i, len(graphs1[i]), len(graphs1[i].edges), len(graphs2[i]), len(graphs2[i].edges)))

    # compare graphs, calculating tau for them.
    # G1 nodes, G2 nodes, in common, tau, p_value
    print('window, %s nodes, %s nodes, compared, %% compared, top_x, in common, tau, tau_p, rho, rho_p' % (tweets_fn1, tweets_fn2))
    window_labels = list(map(str, range(1, num_buckets + 1)))
    if not cumulative:
        window_labels += ['Total']
    else:
        window_labels[-1] = 'Total'
    for (w, g1, g2) in zip(window_labels,graphs1, graphs2):
        common_ids = set(g1.nodes()).intersection(g2.nodes())
        if len(common_ids) == 0:
            print('%s,%d,%d,0,0.0,0,0,0,0,0,0' % (w, len(g1), len(g2)))
            continue
        cs1 = CENTRALITY_FUNCTIONS[c_type](g1)
        cs2 = CENTRALITY_FUNCTIONS[c_type](g2)

        in_common_ids = lambda t: t[0] in common_ids
        first = lambda t: t[0]
        cs1_topx = list(map(first, get_top(top_x, filter(in_common_ids, cs1.items()))))
        cs2_topx = list(map(first, get_top(top_x, filter(in_common_ids, cs2.items()))))

        topx_common_ids = set(cs1_topx).intersection(cs2_topx)
        in_topx_common_ids = lambda id: id in topx_common_ids
        cs1_topx = list(filter(in_topx_common_ids, cs1_topx))
        cs2_topx = list(filter(in_topx_common_ids, cs2_topx))

        tau, tau_p = stats.kendalltau(cs1_topx, cs2_topx, nan_policy='omit')
        rho, rho_p = stats.spearmanr(cs1_topx, cs2_topx)

        compared = len(cs1_topx)
        proportion_compared = float(compared) / min(len(g1), len(g2))
        print('%s,%d,%d,%d,%.2f,%d,%d,%s,%s,%s,%s' % (
            w, len(g1), len(g2), compared, proportion_compared, top_x, len(common_ids),
            tau, tau_p, rho, rho_p
        ))


    # gf1 = opts.graphml_file1
    # gf2 = opts.graphml_file2
    # fn1 = extract_filename(gf1)
    # fn2 = extract_filename(gf2)
    # log('f1: %s' % fn1)
    # log('f2: %s' % fn2)
    #
    # g1  = nx.read_graphml(gf1)
    # g2  = nx.read_graphml(gf2)
    #
    # log('G1: %d' % len(g1))
    # log('G2: %d' % len(g2))
    # common_ids = set(g1.nodes()).intersection(g2.nodes())
    # log('in common: %d' % len(common_ids))
    #
    # cs1 = CENTRALITY_FUNCTIONS[opts.c_type](g1)
    # cs2 = CENTRALITY_FUNCTIONS[opts.c_type](g2)
    #
    # in_common_ids = lambda t: t[0] in common_ids
    # first = lambda t: t[0]
    # cs1_topx = list(map(first, get_top(opts.top_x, filter(in_common_ids, cs1.items()))))
    # cs2_topx = list(map(first, get_top(opts.top_x, filter(in_common_ids, cs2.items()))))
    #
    # log('cs1_topx: %d' % len(cs1_topx))
    # log('cs2_topx: %d' % len(cs2_topx))
    #
    # topx_common_ids = set(cs1_topx).intersection(cs2_topx)
    #
    # in_topx_common_ids = lambda id: id in topx_common_ids
    # cs1_topx = list(filter(in_topx_common_ids, cs1_topx))
    # cs2_topx = list(filter(in_topx_common_ids, cs2_topx))
    #
    # if DEBUG: log_top_x(cs1_topx, cs2_topx)
    #
    # tau, tau_p_value = stats.kendalltau(cs1_topx, cs2_topx, nan_policy='omit')
    # rho, rho_p_value = stats.spearmanr(cs1_topx, cs2_topx)
    #
    # if opts.incl_header:
    #     print('top_x,in_common,tau,tau_p-value,rho,rho_p-value')
    # print('%d,%d,%s,%s,%s,%s' % (
    #     opts.top_x, len(topx_common_ids),
    #     tau, tau_p_value,
    #     rho, rho_p_value
    # ))
    #
    # with open(opts.out_file, 'w', encoding='utf-8') as f:
    #     f.write('%s,%s\n' % (fn1, fn2))
    #     for i in range(len(topx_common_ids)):
    #         f.write('%s,%s\n' % (cs1_topx[i], cs2_topx[i]))
