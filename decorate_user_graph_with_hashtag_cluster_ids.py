#!/usr/bin/env python3

import json
import networkx as nx
import statistics
import sys


from argparse import ArgumentParser
from basic_tweet_corpus_stats import lowered_hashtags_from
from collections import Counter
from community import community_louvain


class Options:
    def __init__(self):
        self.usage = 'decorate_user_graph_with_hashtag_cluster_ids.py --user-graph <users.graphml> --tweets <tweets.json> --hashtag-graph <hashtag.graphml> -o <decorated.graphml>'
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
            '--dry-run',
            action='store_true',
            default=False,
            dest='dry_run',
            help='Turn on verbose logging (default: False)'
        )
        self.parser.add_argument(
            '--user-graph',
            dest='users_file',
            required=True,
            help='File of users graph to decorate.'
        )
        self.parser.add_argument(
            '--hashtag-graph',
            dest='ht_file',
            required=True,
            help='File of hashtag graph.'
        )
        self.parser.add_argument(
            '--tweets',
            dest='tweets_file',
            required=True,
            help='File of tweets the users appear in.'
        )
        self.parser.add_argument(
            '-p', '--propagate-labels',
            action='store_true',
            default=False,
            dest='label_prop',
            help='Turn on label propagation, colouring uncoloured nodes using neighbours (default: False)'
        )
        self.parser.add_argument(
            '-o',
            dest='out_file',
            required=True,
            help='GraphML file to write hashtag graph to.'
        )
        # self.parser.add_argument(
        #     '--ignore',
        #     dest='ignore_hashtags',
        #     default=[],
        #     help='Hashtags to ignore (default: filenames)'
        # )
        # self.parser.add_argument(
        #     '--min-weight',
        #     dest='min_weight',
        #     default=1,
        #     type=int,
        #     help='Smallest permitted count of co-mentioning authors (default: 1)'
        # )



    def parse(self, args=None):
        return self.parser.parse_args(args)


def add_nodes(g, *nodes):
    for n in nodes:
        if n not in g:
            g.add_node(n, label=n)


def add_weighted_edge(g, u, v, weight_property='weight'):
    if g.has_edge(u, v):
        g[u][v][weight_property] += 1.0
    else:
        g.add_edge(u, v)
        g[u][v][weight_property] = 1.0


def safe_mode(l):
    try:
        return statistics.mode(l)
    except statistics.StatisticsError:
        first = 0
        label = 0
        return Counter(l).most_common()[first][label]


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

    users_file    = opts.users_file
    hashtags_file = opts.ht_file
    tweets_file   = opts.tweets_file
    out_file      = opts.out_file
    # to_ignore  = opts.ignore_hashtags.split(',')
    # min_weight = opts.min_weight
    dry_run       = opts.dry_run
    propagate_labels = opts.label_prop

    log('Users:     %s' % users_file)
    log('Hashtags:  %s' % hashtags_file)
    log('Tweets:    %s' % tweets_file)
    log('Out GraphML: %s' % out_file)
    # log('Ignore:      %s' % ','.join(to_ignore))
    # log('Min weight:  %d' % min_weight)
    log('Dry run:     %s' % dry_run)
    log('Propagate labels: %s' % propagate_labels)

    # record the hashtag uses
    users_hashtags = {}  # user_id : map(hashtags:counts)
    tweet_count = 0
    with open(tweets_file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            tweet_count += 1
            if DEBUG and tweet_count %  100 == 0: eprint('.', end='')
            if DEBUG and tweet_count % 5000 == 0: eprint(' %10d' % tweet_count)

            tweet = json.loads(line)

            user_id = tweet['user']['id_str']
            hashtags = list(set(lowered_hashtags_from(tweet)))

            #
            # Ignore RTs and quotes, as they allow users to be assigned a preferred
            # hashtag that is not present in the hashtag graph (so they end up UNASSIGNED)
            #
            # if 'retweeted_status' in tweet and tweet['retweeted_status']:
            #     hashtags = list(set(hashtags + lowered_hashtags_from(tweet['retweeted_status'])))
            # if 'quoted_status' in tweet and tweet['quoted_status']:
            #     hashtags = list(set(hashtags + lowered_hashtags_from(tweet['quoted_status'])))

            if user_id not in users_hashtags:
                users_hashtags[user_id] = dict([(ht, 1) for ht in hashtags])
            else:
                for ht in hashtags:
                    if ht in users_hashtags[user_id]:
                        users_hashtags[user_id][ht] += 1
                    else:
                        users_hashtags[user_id][ht] = 1

    log('')
    log('Tweets: %d' % tweet_count)
    log('Users: %d' % len(users_hashtags))

    # read graph files
    u_g  = nx.read_graphml(users_file)
    ht_g = nx.read_graphml(hashtags_file)

    # look for communities (Louvain): { hashtag : cluster_id }
    partition = community_louvain.best_partition(ht_g)
    sorted_hashtags = sorted(list(partition.keys()))

    # find users' preferred/predominant hashtags
    users_preferred_hashtag = {}
    for user in users_hashtags:
        hashtag_counts = users_hashtags[user]
        if len(hashtag_counts) == 0:
            users_preferred_hashtag[user] = ''
            continue
        max_count = max(hashtag_counts.values())
        for ht in sorted_hashtags:
            if ht in hashtag_counts and hashtag_counts[ht] == max_count:
                users_preferred_hashtag[user] = ht
                continue
        for ht in sorted(hashtag_counts.keys()):  # keep key order consistent
            if hashtag_counts[ht] == max_count:
                users_preferred_hashtag[user] = ht
                break

    UNASSIGNED = max(set(partition.values())) + 1
    unassigned_count = 0
    valid_users = 0
    valid_hts = 0
    for u, d in u_g.nodes(data=True):
        if u in users_preferred_hashtag: valid_users += 1
        pref_ht = users_preferred_hashtag[u] if u in users_preferred_hashtag else ''
        if pref_ht in partition: valid_hts += 1
        cluster_id = (partition[pref_ht] if pref_ht in partition else UNASSIGNED) * 1.0
        if cluster_id == UNASSIGNED:
            unassigned_count += 1
        d['initially_unassigned'] = cluster_id == UNASSIGNED
        d['hashtag_cluster_id'] = cluster_id
    log('valid users: %d' % valid_users)
    log('valid hashtags: %d' % valid_hts)

    if propagate_labels:
        nodes_changed_last_time = 0
        unassigned_nodes = [n for n, d in u_g.nodes(data=True) if d['hashtag_cluster_id'] == UNASSIGNED]
        while nodes_changed_last_time != len(unassigned_nodes):
            nodes_changed_last_time = len(unassigned_nodes)
            log('Unassigned nodes: %d' % nodes_changed_last_time)
            # assign cluster IDs to nodes with neighbours with cluster IDs
            for n in unassigned_nodes:
                cluster_ids = nx.get_node_attributes(u_g, 'hashtag_cluster_id')
                neighbour_labels = [cluster_ids[n2] for n2 in u_g[n] if cluster_ids[n2] != UNASSIGNED]
                if len(neighbour_labels):
                    mode = safe_mode(neighbour_labels)
                    u_g.nodes[n]['hashtag_cluster_id'] = mode

            unassigned_nodes = [n for n, d in u_g.nodes(data=True) if d['hashtag_cluster_id'] == UNASSIGNED]

        unassigned_count = len(unassigned_nodes)

    nx.write_graphml(u_g, out_file)

    print('DONE - Hashtag Graph[file=%s,nodes=%d,edges=%d,ht_clusters=%d,unassigned=%d(%.2f)]' % (
        out_file, len(u_g), len(u_g.edges()), len(set(partition.values())), unassigned_count,
        (unassigned_count / len(u_g)) * 100.0
    ))
