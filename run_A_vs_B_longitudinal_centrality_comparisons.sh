#!/bin/sh

# Runs various centrality comparisons for different network types for two tweet corpora

A=$1        # corpus A
B=$2        # corpus B
OUT_DIR=$3  # where to write results

[ ! -d "${OUT_DIR}" ] && mkdir -p "${OUT_DIR}"  # create OUT_DIR if it's missing

SCRIPT_HOME=/Users/derek/Documents/development/election-watch/twitter/network_extraction
if [ ! -z "$4" ]; then
    SCRIPT_HOME=$4
fi
COMPARE=$SCRIPT_HOME/compare_centralities_longitudinally_from_tweets.py

echo Script: $COMPARE

echo Running straight longitudinal
OPTS="-w 60 -x 1000 -v"

time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t RETWEET -c DEGREE      $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tRT_cDEG_w60_x1000.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t MENTION -c DEGREE      $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tMEN_cDEG_w60_x1000.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t MENTION -c BETWEENNESS $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tMEN_cBET_w60_x1000.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t MENTION -c CLOSENESS   $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tMEN_cCLO_w60_x1000.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t REPLY   -c DEGREE      $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tREP_cDEG_w60_x1000.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t REPLY   -c BETWEENNESS $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tREP_cBET_w60_x1000.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t REPLY   -c CLOSENESS   $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tREP_cCLO_w60_x1000.csv"

echo Running cumulative longitudinal
OPTS="-w 60 -x 1000 --cumulative -v"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t RETWEET -c DEGREE      $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tRT_cDEG_w60_x1000_cum.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t MENTION -c DEGREE      $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tMEN_cDEG_w60_x1000_cum.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t MENTION -c BETWEENNESS $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tMEN_cBET_w60_x1000_cum.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t MENTION -c CLOSENESS   $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tMEN_cCLO_w60_x1000_cum.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t REPLY   -c DEGREE      $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tREP_cDEG_w60_x1000_cum.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t REPLY   -c BETWEENNESS $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tREP_cBET_w60_x1000_cum.csv"
time $COMPARE -f1 "${A}.json" -f2 "${B}.json" -t REPLY   -c CLOSENESS   $OPTS > "${OUT_DIR}/${A}_${B}_long-comp_tREP_cCLO_w60_x1000_cum.csv"

echo Done
