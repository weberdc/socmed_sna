# Data

The `data` folder holds files with the IDs of tweets collected in parallel and used in a study examining the effect of variations in data collection. The files have the structure `<activity>_<phase>-<tool>-tweet_ids.txt`, where activity refers to a particular collection activity, phase refers to which phase of a multiphase exercise the dataset refers to, and tool refers to which social media collection tool was used.

The only activity in this instance refers to the Australian Broadcasting Corporation's (ABC's) Q&A commentary panel programme; there were two phases to this activity: part 1 and part 2; and the tools used were `twarc` and `RAPID` (`rapid_e` when the expansion was used).

The Q&A datasets were collected during the following times:

- Part 1: UTC 2018-11-08 09:00 to 13:00
- Part 2: UTC 2018-11-08 19:00 to 2018-11-09 10:00

The filter terms used were `qanda` (no '\#', to also get mentions of `@qanda`) and two terms which relate to the name of one of the Q&A panelists (and are withheld to comply with ethics protocols. 
