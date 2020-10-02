#!/bin/sh

#
# Invokes all the extract_*.sh scripts on the file of tweets provided
# as a command line argument.
#
# Usage: ./exract_all_separately.sh [-z] file_of_tweets.json
#
# Author: Derek Weber
# Date: 2018-12-04
#

FN_ARG=$1

CAT=cat
if [[ "${FN_ARG: -1}" == "z" ]]; then
    CAT=zcat
    FN_ARG=$2
    echo "Tweets compressed; using zcat..."
fi

# Props to https://stackoverflow.com/a/246128/390018 for this bit
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# And to https://stackoverflow.com/a/965072/390018 for this bit
FILEPATH="${FN_ARG%.*}"
while [[ "$FILEPATH" =~ .*\..* ]]; do
    FILEPATH="${FILEPATH%.*}"
done

echo "Extracting all interesting bits to similarly named CSVs from ${FN_ARG}"
echo "Using file base: ${FILEPATH}"

echo "- Extracting retweets"
$CAT "${FN_ARG}" | $DIR/extract_retweets.sh -h > "${FILEPATH}-retweets.csv"

echo "- Extracting quotes"
$CAT "${FN_ARG}" | $DIR/extract_quotes.sh   -h > "${FILEPATH}-quotes.csv"

echo "- Extracting mentions"
$CAT "${FN_ARG}" | $DIR/extract_mentions.sh -h > "${FILEPATH}-mentions.csv"

echo "- Extracting replies"
$CAT "${FN_ARG}" | $DIR/extract_replies.sh  -h > "${FILEPATH}-replies.csv"

echo "- Extracting hashtags"
$CAT "${FN_ARG}" | $DIR/extract_hashtags.sh -h > "${FILEPATH}-hashtags.csv"

echo "- Extracting URLs"
$CAT "${FN_ARG}" | $DIR/extract_urls.sh     -h > "${FILEPATH}-urls.csv"

echo "Done"
