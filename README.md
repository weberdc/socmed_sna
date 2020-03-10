# Network extraction

Tools for extracting information and constructing and analysing networks from
Twitter data (JSON). Some of these are \*nix shell scripts, some are Windows
batch files, some are python scripts. Mostly tested on Windows running cygwin.

## Code

### Requirements

 - cygwin or bash for shell scripts
 - DOS command prompt for batch files
 - Python:

   - matplotlib 3.0.3
   - networkx 2.2
   - numpy 1.16.2
   - python 3.7.2
   - scipy 1.2.1
   - scikit-learn 0.21.2
   - via pip 19.0.3:

     - python-louvain 0.13
     - twarc 1.6.3

### Scripts

- `basic_tweet_corpus_stats.py file1.json file2.json ... filen.json` produces a table of stats (including a LaTeX mode)
- `compare_centralities.py` calculates centrality values for two graphs for one of four centrality types (degree, betweenness, closeness and eigenvector) and outputs the top matching x nodes to a file as well as printing out Kendall Tau and Spearman similarity values (tau and rho respectively, each with p-values).
- `compare_centralities.bat` runs `compare_centralities.py` for mentions and replies and each of the four centrality types, using the JSON of the tweets, and the CSV files generated by `extract_all_separately.sh`
- `compare_centralities_longitudinally_from_tweets.py` runs a specified centrality comparison for the top x members of a particular network type built from interactions in two provided corpora - these comparisons are done overall and also over each window of specified length and the resulting Kendall Tau and Spearman's coefficients are reported, so one can see how the corpora correspond over time - this is invoked by the convenience script `run_A_vs_B_longitudinal_centrality_comparisons.sh`.
- `plot_centrality_comparisons.py` generates scatter plots for two-columned CSVs of ranked lists of values
- `centralities.py` calculates the four centrality types for a given GraphML file
- `csv_to_weighted_digraph.py` builds a GraphML file using specified columns from a CSV file - a directed weighted graph with labeled edges is created. Creates graphs for retweets, mentions, replies and quotes.
- `build_jsocnet_graphs.bat` creates directed weighted graphs of users from CSVs generated by `extract_all_separately.sh` using `csv_to_weighted_digraph.py`
- `run_hashtag_wordcount.sh` shell script that reads tweets from stdin (JSON) and outputs the wordcount of occurring lower-cased hashtags in CSV format (hashtag, count, decreasing). Use this to figure out which hashtags are widespread.
- `run_lang_wordcount.sh` shell script that reads tweets from stdin (JSON) and outputs the wordcount of `lang` property values drawn from the tweets in CSV format (language code, count, decreasing). Use this to figure out which languages are widespread. Use the `-u` option to consider user languages rather than tweet languages.
- `build_hashtag_co-mention_graph.py` creates a weighted graph of hashtags, linked when they are mentioned by the same user (thinking of adding when they are mentioned in the same tweet) - works directly from tweets. Visualise the results in Visone, colour and size the edges by weight, colour the nodes by Louvain clustering, and Bob's your uncle. Stress min. layout appears to be the best.
- `extract_tweets_by_authors.sh` filters out tweets authored by the given IDs from a corpus of tweets (in JSON) to extract a subset from the corpus.
- `combine_wc_csvs.py` creates a single table from multiple key/value CSVs where the left column is the union of all keys discovered and each column includes the values (or 0) for each given CSV file - basically a way to combine word count lists to making pie charts in Excel easier
- `extract_all_separately.sh` invokes `extract_hashtags.sh`, `extract_mentions.sh`, `extract_quotes.sh`, `extract_replies.sh`, `extract_retweets.sh` and `extract_urls.sh` on a given tweet corpus (JSON), generating CSVs of the extracted information, which can then be used in tools like Visone.
- `plot_per_time_metrics.py` plots four different plots of activity over time seen in a given tweet corpus (JSON) and CSV files generated by `extract_all_separately.sh`.
- `plot_ranked_items.py` creates a scatterplot of the rankings of common elements in the columns of a two-columned CSV (with an optional header and arguments for chart labels). An option is provided to choose Mehwish Nasim's algorithm for plotting the points. E.g. `python plot_ranked_items.py -f comparisons/rapid_twarc-centrality-comparisons.csv -l "RAPID,Twarc" --header -a NASIM -o myscatterplot.png`


## Usage

Given a few corpora of tweets, e.g. a.json, b.json, and c.json, you can use the
scripts above in the following way (`$NET_BIN` refers to the directory in which the scripts reside):

 1. `python basic_tweet_corpus_stats.py --latex --labels "A,B,C" a.json b.json c.json`
    will generate a LaTeX formatted table of stats for each corpus, with the
    column titles provided by the `--labels` option.
 2. `shell: cat a.json | $NET_BIN/run_lang_wordcount.sh > a_lang_wc.csv` counts the `lang` property values in tweets in `a.json`.
 3. `shell: cat a.json | $NET_BIN/run_lang_wordcount.sh -u > a_user_lang_wc.csv` counts the `lang` property values in users in `a.json`.
 4. `shell: cat a.json | $NET_BIN/run_hashtag_wordcount.sh > a_hashtag_wc.csv` counts the hashtags (lowercase) in tweets in `a.json`.
 5. `shell: extract_all_separately.sh a.json` will generate CSVs for several different
    interactions: `a-mentions.csv`, `a-replies.csv`, ...
 6. `python plot_per_time_metrics.py -f a --label A --window 60 --y-limits auto-auto-1000-1500 -o charts  --out-filebase A_outfile_prefix`
    will create a single figure with four plots using `a` as the basename for
    the JSON and CSV files to use and `A_outfile_prefix` as the prefix for the
    output file. The `y-limits` option can be used to specify the y-limit of 
    each of the four charts to facilitate comparison between different datasets
    (i.e., give them all the same y-range). The window size is specified in 
    minutes (i.e., 60 is one hour).
 7. `python plot_tweet_counts.py -l "RAPID,Twarc" --tweets -t "Election Day" -v rapid-k.json twarc.json -o ..\images\nswelec-rapid_twarc-tweet_counts-60m.png -w 60 --tz-fix -600`
 7. `cat tweets.json | run_hashtag_wordcount.sh > hashtag_counts.csv` then look at which hashtags occur most often and may clutter any hashtag graph - ignore these in the next step. 
 8. `python build_hashtag_co-mention_graph.py --min-width 1 -v -i tweets.json -o hashtag_co-mentions.graphml --ignore "hashtag1,hashtag2,hashtag3"` -- this will build a network and tell you how big it is. If you use the option `--dry-run` you can see the size of the graph without writing it out.
 9. `DOS: build_jsocnet_graphs.bat a graphs` will create `graphs/a-mentions.graphml`,
    `graphs/a-replies.graphml`, `graphs/a-retweets.graphml`, and
    `graphs/a-quotes.graphml`
10. `DOS: compare_centralities.bat 500 graphs\\a graphs\\b comparisons\\ab 2> nul` will
    compare at least the top 500 ranked nodes of each graph, constrained to only
    those nodes common to both graphs. The `graphs\\a` and `graphs\\b` are
    prefixes for the mentions, replies, quotes and retweets GraphML files in the
    `graphs` folder. The `comparisons\\ab` option provides a prefix for the
    CSV output of the comparisons, each written to its own two-column file, which
    can be used in the next step. The `2> nul` bit is to redirect errors that
    pollute the output CSV
11. `python compare_centralities_longitudinally_from_tweets.py -f1 corpus1.json -f2 corpus2.json -t RETWEET -c DEGREE -w 60 | pbcopy` will compare corpus1.json and corpus2.json overall and broken down into hourlong periods (a window of 60 minutes), or use `run_A_vs_B_longitudinal_centrality_comparisons.sh corpus1.json corpus2.json comparisons`
12. `DOS:plot_each_centrality_comparison.bat comparisons\\ab charts\\ab "A scores,B scores"`
    will generate scatter plots for each interaction and centrality combination
    in the files in `graphs` starting with `ab` and the results will be written
    to the `charts` folder. Use the option `--algorithm NASIM` to use Mehwish Nasim's plot algorithm.
13. `python plot_centrality_comparisons.py -f comparisons/ab -l "A,B" -t "A vs B centralities compared" --header -o charts/ab-centralities_compared-scatterplots.png`
    creates a multi-scatterplot based on the mention and reply centrality
    comparison across the four centrality types. Other examples:

    - `(jsocnet) C:\Users\derek\Documents\PhD\local_analysis\jsocnet\nswelec>python %NET_BIN%\plot_centrality_comparisons.py -f comparisons\twarc_tweepy -l "Twarc,Tweepy" -t "Twarc vs Tweepy centralities compared" --header -o charts\twarc_tweepy-centrality_compared-scatterplots.png`
    - `(jsocnet) C:\Users\derek\Documents\PhD\local_analysis\jsocnet\nswelec>python %NET_BIN%\plot_centrality_comparisons.py -f comparisons\twarc_tweepy -l "Twarc,Tweepy" -t "Twarc vs Tweepy centralities compared" --header -o charts\twarc_tweepy-centrality_compared-scatterplots-nasim.png -a NASIM`
    - `(jsocnet) C:\Users\derek\Documents\PhD\local_analysis\jsocnet\nswelec>python %NET_BIN%\plot_centrality_comparisons.py -f comparisons\twarc_tweepy -l "Twarc,Tweepy" -t "Twarc vs Tweepy centralities compared" --header -o charts\twarc_tweepy-centrality_compared-scatterplots-nasim-grey.png -a NASIM -g`
    - `(jsocnet) C:\Users\derek\Documents\PhD\local_analysis\jsocnet\nswelec>python %NET_BIN%\plot_centrality_comparisons.py -f comparisons\twarc_tweepy -l "Twarc,Tweepy" -t "Twarc vs Tweepy centralities compared" --header -o charts\twarc_tweepy-centrality_compared-scatterplots-grey.png -g`
