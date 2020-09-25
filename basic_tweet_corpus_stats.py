#!/usr/bin/env python3

from __future__ import print_function
from argparse import ArgumentParser
# from collections import Counter
from copy import deepcopy


import gzip
import json
import ntpath  # https://stackoverflow.com/a/8384788
import os
import statistics
import sys


class Options:
    def __init__(self):
        self.usage = 'basic_tweet_corpora_stats.py [options] tweets1.json [tweets2.json ...]'
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
            '-l', '--labels',
            dest='labels',
            default=None,
            help='Labels to use instead of filenames, separated by commas (default: filenames)'
        )
        self.parser.add_argument(
            '--latex',
            action='store_true',
            default=False,
            dest='latex',
            help='Format output as LaTeX booktabs (default: False)'
        )
        self.parser.add_argument(
            'i_files', metavar='i_file', type=str, nargs='*',
            help='A file of tweets to consider'
        )


    def parse(self, args=None):
        return self.parser.parse_args(args)


def extract_filename(filepath, default_name='UNKNOWN.txt'):
    if not filepath:
        return default_name

    head, tail = ntpath.split(filepath)
    filename = tail or ntpath.basename(head)
    return os.path.splitext(filename)[0]


def read_tweets(file=None):
    """Gets the lines from the given file or stdin if it's None or '' or '-'."""
    if file and file != '-':
        lines = []
        count = 0
        try:
            f = gzip.open(file, 'rt') if file[-1] in 'Zz' else open(file, 'r', encoding='utf-8')
            for l in f:
                lines.append(json.loads(l.strip()))
                count += 1
                if count % 1000 == 0:
                    eprint('.', flush=True, end='')
                if count % 50000 == 0:
                    eprint('%10d' % count, flush=True)
        finally:
            f.close()
        eprint('\n%d' % count)
        return lines
        # with open(file, 'r', encoding='utf-8') as f:
        #     return [l.strip() for l in f.readlines()]
    else:
        return [json.loads(l.strip()) for l in sys.stdin]


def lowered_hashtags_from(tweet):
    def extract_lower_hts(entities):
        return [ht['text'].lower() for ht in entities]
    ht_entities = tweet['entities']['hashtags']
    if 'extended_tweet' in tweet and tweet['extended_tweet']:
        ht_entities = tweet['extended_tweet']['entities']['hashtags']
    return extract_lower_hts(ht_entities)


def expanded_urls_from(tweet):
    url_entities = tweet['entities']['urls']
    if 'extended_tweet' in tweet and tweet['extended_tweet']:
        url_entities = tweet['extended_tweet']['entities']['urls']
    return [u['expanded_url'] for u in url_entities if u['expanded_url']] # skip ''


def mentioned_ids_from(tweet, desired_field='id_str'):
    def extract_mention_ids(entities):
        return [m[desired_field] for m in entities]
    m_entities = tweet['entities']['user_mentions']
    if 'extended_tweet' in tweet and tweet['extended_tweet']:
        m_entities = tweet['extended_tweet']['entities']['user_mentions']
    return extract_mention_ids(m_entities)


def flatten(list_of_lists):
    """Takes a list of lists and turns it into a list of the sub-elements"""
    return [item for sublist in list_of_lists for item in sublist]


def safe_random_mode(values):
    return get_most_used(values, 1)
    # if not len(values): return None
    # counts = [(v,values.count(v)) for v in set(values)]
    # counts.sort(key=lambda t: t[1], reverse=True)
    # return counts[0][0]


def get_most_used(values, rank=1):
    if len(set(values)) < rank: return None
    counts = [(v, values.count(v)) for v in set(values)]
    counts.sort(key=lambda t: t[1], reverse=True)
    return counts[rank-1][0]


def analyse(tf):
    tweets = read_tweets(tf) #[json.loads(l) for l in read_lines(tf)]

    def select(f):
        return list(filter(f, tweets))

    res = {}

    res['tweet_count'] = len(tweets)
    all_authors = [t['user']['id_str'] for t in tweets]
    res['author_count'] = len(set(all_authors))
    res['retweet_count'] = len(select(lambda t: 'retweeted_status' in t))
    res['quote_count'] = len(select(lambda t: 'quoted_status' in t and t['quoted_status'] and ('retweeted_status' not in t or not t['retweeted_status'])))
    res['reply_count'] = len(select(lambda t: 'in_reply_to_status_id_str' in t and t['in_reply_to_status_id_str']))
    res['tweets_with_hashtags'] = len(select(lambda t: len(t['entities']['hashtags'])))
    res['tweets_with_urls'] = len(select(lambda t: len(t['entities']['urls'])))

    res['most_prolific_author'] = safe_random_mode(all_authors)
    res['most_prolific_author_tweet_count'] = all_authors.count(res['most_prolific_author'])

    all_rts = [t['retweeted_status']['id_str'] for t in tweets if 'retweeted_status' in t and t['retweeted_status']]
    res['most_retweeted_tweet'] = safe_random_mode(all_rts)
    res['most_retweeted_tweet_count'] = all_rts.count(res['most_retweeted_tweet'])

    all_replies = [t['in_reply_to_status_id_str'] for t in tweets if 'in_reply_to_status_id_str' in t and t['in_reply_to_status_id_str']]
    res['most_replied_to_tweet'] = safe_random_mode(all_replies)
    res['most_replied_to_tweet_count'] = all_replies.count(res['most_replied_to_tweet'])

    all_mentions_unflattened = [mentioned_ids_from(t) for t in tweets]
    all_mentions = flatten(all_mentions_unflattened)
    res['tweets_with_mentions'] = len(list(filter(lambda ms: len(ms), all_mentions_unflattened)))
    res['most_mentioned_author'] = safe_random_mode(all_mentions)
    res['most_mentioned_author_count'] = all_mentions.count(res['most_mentioned_author'])

    all_hashtags = flatten([lowered_hashtags_from(t) for t in tweets])
    res['hashtag_uses'] = len(all_hashtags)
    res['unique_hashtags'] = len(set(all_hashtags))
    res['most_used_hashtag'] = safe_random_mode(all_hashtags)
    res['most_used_hashtag_count'] = all_hashtags.count(res['most_used_hashtag'])
    res['next_most_used_hashtag'] = get_most_used(all_hashtags, 2)
    res['next_most_used_hashtag_count'] = all_hashtags.count(res['next_most_used_hashtag'])

    all_urls = flatten([expanded_urls_from(t) for t in tweets])
    res['url_uses'] = len(all_urls)
    res['unique_urls'] = len(set(all_urls))
    res['most_used_url'] = safe_random_mode(all_urls)
    res['most_used_url_count'] = all_urls.count(res['most_used_url'])

    # res['filename'] = extract_filename(tf)

    return res


def to_label(key):
    return {
        'tweet_count':          'Tweets',
        'retweet_count':        'Retweets',
        'quote_count':          'Quotes',
        'reply_count':          'Replies',
        'tweets_with_hashtags': 'Tweets with hashtags',
        'tweets_with_urls':     'Tweets with URLs',
        'author_count':         'Accounts',
        'most_prolific_author': 'Most prolific account',
        'most_prolific_author_tweet_count': 'Tweets by most prolific account',
        'most_retweeted_tweet': 'Most retweeted tweet',
        'most_retweeted_tweet_count': 'Most retweeted tweet count',
        'most_replied_to_tweet': 'Most replied to tweet',
        'most_replied_to_tweet_count': 'Most replied to tweet count',
        'tweets_with_mentions': 'Tweets with mentions',
        'most_mentioned_author': 'Most mentioned account',
        'most_mentioned_author_count': 'Mentions of most mentioned account',
        'hashtag_uses':          'Hashtag uses',
        'unique_hashtags':       'Unique hashtags',
        'most_used_hashtag':     'Most used hashtag',
        'most_used_hashtag_count': 'Most used hashtag count',
        'next_most_used_hashtag': 'Next most used hashtag',
        'next_most_used_hashtag_count': 'Uses of next most used hashtag',
        'url_uses':              'URL uses',
        'unique_urls':           'Unique URLs',
        'most_used_url':         'Most used URL',
        'most_used_url_count':   'Uses of most used URL'
    }[key]


def print_header(latex, labels):
    if latex:
        columns_format_str = 'l' + ('r' * len(labels))
        column_titles = ' & '.join(['Property'] + labels)
        print("""\\begin{table}[ht]
\\centering
\\begin{tabular}{%s}
    \\toprule
    %s \\\\
    \\midrule""" % (columns_format_str, column_titles))
    else:
        print(','.join(['Property'] + labels))


def print_body(latex, results):
    def clean(s):
        # return to_label(s)
        return s if '_' not in str(s) else s.replace('_', '\\_')
    keys = list(results[0][1].keys())  # keep key order consistent
    column_widths = calc_column_widths(results)
    if latex:
        for k in keys:
            # k_str = k if '_' not in k else k.replace('_', '\\_')
            for i in range(len(results)):
                first = i == 0
                last  = i == len(results) - 1
                res = results[i][1]
                if first: print('    %s & ' % to_label(k), end='') # print header?
                if k.endswith('_url'):
                    print('\\url{%s}' % clean(res[k]), end='')         # print value
                else:
                    print('%s' % clean(res[k]), end='')         # print value
                if not last: print(' & ', end='')    # not last? print comma
                else: print(' \\\\')                   # last? print newline
    else:
        for k in keys:
            for i in range(len(results)):
                first = i == 0
                last  = i == len(results) - 1
                res = results[i][1]
                if first: print('%s,' % to_label(k), end='')  # print header?
                print('%s' % res[k], end='')        # print value
                if not last: print(',', end='')     # not last? print comma
                else: print('')                     # last? print newline


def print_footer(latex):
    if latex:
        print("""    \\bottomrule
\\end{tabular}
\\caption{A Table}
\\label{tab:a_table}
\\end{table}
""")


def clean_labels(labels):
    """ Escape any LaTeX-unfriendly characters """
    for i in range(len(labels)):
        l = labels[i]
        while '%' in l or '&' in l or '_' in l:
            l = l.replace('&', '\\&')
            l = l.replace('%', '\\%')
            l = l.replace('_', '\\_')
        labels[i] = l


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

    labels  = opts.labels.split(',') if opts.labels else [extract_filename(tf) for tf in opts.i_files]
    if opts.latex:
        clean_labels(labels)
    results = [] # [(extract_filename(tf), analyse(tf)) for tf in opts.i_files]
    for tf in opts.i_files:
        log('Inspecting %s' % tf)
        fn = extract_filename(tf)
        analysis = analyse(tf)
        results.append( (fn, analysis) )


    print_header(opts.latex, labels)
    print_body(opts.latex, results)
    print_footer(opts.latex)

    # print(','.join(['Property'] + labels))
    # keys = list(results[0][1].keys())  # keep key order consistent
    # for k in keys:
    #     for i in range(len(results)):
    #         first = i == 0
    #         last  = i == len(results) - 1
    #         res = results[i][1]
    #         if first: print('%s,' % k, end='')  # print header?
    #         print('%s' % res[k], end='')        # print value
    #         if not last: print(',', end='')     # not last? print comma
    #         else: print('')                     # last? print newline
