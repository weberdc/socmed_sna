# Data

The `data` folder holds files with the IDs of tweets collected as part of a number of studies. To make use of these IDs, the tweets will need to be 'hydrated' from the IDs (e.g., using a tool like [Twarc](https://github.com/DocNow/twarc#hydrate))

## Dataset Descriptions

**Q&A 2018 November**

This set of files consists of several collections, each consisting of two files of tweets (i.e., their IDs) collected simultaneously (the zip files contain the IDs of tweets collected in parallel, while the gzip files are individual sets of tweets). The focus of these collections was an episode of the Australian Broadcasting Corporation's (ABC's) Q&A commentary panel programme, including 4 hours on the night of the broadcast (Part 1) and 15 hours of the following day (Part 2). Two tools were used for most of the collection: [RAPID](https://link.springer.com/chapter/10.1007/978-3-030-10997-4_44) and [Twarc](https://github.com/DocNow/twarc). [Tweepy](https://www.tweepy.org/) was used for the Election Day collection activity. RAPID has an expansion feature that allows the filter keyword set to be dynamically expanded to incorporate new popular terms and remove disused ones, in order to more accurately track the discussion of interest. `RAPID-E` denotes the expanded RAPID dataset, while `RAPID` refers to `RAPID-E` filtered back to only tweets including the original keywords, and `Twarc` denotes the Twarc collection. Both RAPID and Twarc provide ways to access Twitter's free tweet streams.

The Q&A datasets were collected during the following times:

- Part 1: UTC 2018-11-08 09:00 to 13:00
- Part 2: UTC 2018-11-08 19:00 to 2018-11-09 10:00

The filter terms used were `qanda` (no '\#', to also get mentions of `@qanda`) and two terms which relate to the name of one of the Q&A panelists (and are withheld to comply with ethics protocol H-2018-045 approved by the University of Adelaide's human research and ethics committee, but can be provided on request).

- `qanda_part1-rapid_e-tweet_ids.txt.gz`: Part 1, RAPID-E
- `qanda_part1-rapid-tweet_ids.txt.gz`: Part 1, RAPID
- `qanda_part1-twarc-tweet_ids.txt.gz`: Part 1, Twarc
- `qanda_part2-rapid_e-tweet_ids.txt.gz`: Part 2, RAPID-E
- `qanda_part2-rapid-tweet_ids.txt.gz`: Part 2, RAPID
- `qanda_part2-twarc-tweet_ids.txt.gz`: Part 2, Twarc

These datasets were used in the following publications:

- Weber, D., Nasim, M., Mitchell, L., and Falzon, L., "A method to evaluate the reliability of social media data for social network analysis.", In _The 2020 IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining_, _ASONAM_, Leiden, The Netherlands, 7-10 December, 2020, accepted. ([arXiv:2010.08717](https://arxiv.org/abs/2010.08717))

- Weber, D. and Neumann, F. 2021, "Exploring the effect of streamed social media data variations on social network analysis", _Journal of Social Network Analysis and Mining_, submitted. ([arXiv:2103.03424](https://arxiv.org/abs/2103.03424))

**Other datasets**

Other datasets included here are:

- `afl-tweet_ids.zip`: AFL tweet IDs collected by RAPID and Twarc using the term `afl` over the period 2019-03-22 to 2019-03-25.
- `afl2-tweet_ids.zip`: AFL tweet IDs for two parallel datasets collected by RAPID  using the term `afl` over the period 2019-04-03 to 2019-03-09.
- `electionday-tweet_ids.zip`: Tweet IDs collected by Twarc, RAPID and Tweepy, collected for 24 on the 23 of March, 2019.


**ArsonEmergency**

This study examined polarisation and misinformation during Australia's Black Summer bushfires (2019-2020) and all data was collected with Twarc.

- `ArsonEmergency-20191231-20200117-tweet_ids.txt.gz`: Twitter activity including 'ArsonEmergency' 2019-12-31 to 2020-01-17
- `AustraliaFire-20191231-20200117-tweet_ids.txt.gz`: Twitter activity including 'AustraliaFire' 2019-12-31 to 2020-01-17
- `brexit-20191231-20200117-tweet_ids.txt.gz`: Twitter activity on `\#brexit` 2019-12-31 to 2020-01-17

These datasets were used in the following publications:

- Weber, D., Nasim, M., Falzon, L., and Mitchell, L., "\#ArsonEmergency and Australia's "Black Summer": Polarisation and misinformation on social media.", In _Disinformation in Open Online Media_, _MISDOOM_, Leiden, The Netherlands, 26-27 October, 2020, pp. 159-173. URL: https://doi.org/10.1007/978-3-030-61841-4_11 ([arXiv:2004.00742](https://arxiv.org/abs/2004.00742))
