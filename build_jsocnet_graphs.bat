@echo off

rem Use with:
rem > build_jsocnet_graphs.bat <csv-base-name> <out-dir>
rem

rem set INIT_DIR=%cd%
set BAT_DIR=%~dp0

set FN_BASE=%1
set OUT_DIR=%2

python %BAT_DIR%\csv_to_weighted_digraph.py --csvfile %FN_BASE%-retweets.csv --header --src-col 1 --tgt-col 2 --kind-col 4 --out-file %OUT_DIR%\%FN_BASE%-retweets.graphml
python %BAT_DIR%\csv_to_weighted_digraph.py --csvfile %FN_BASE%-mentions.csv --header --src-col 1 --tgt-col 2 --kind-col 4 --out-file %OUT_DIR%\%FN_BASE%-mentions.graphml
python %BAT_DIR%\csv_to_weighted_digraph.py --csvfile %FN_BASE%-replies.csv  --header --src-col 1 --tgt-col 2 --kind-col 4 --out-file %OUT_DIR%\%FN_BASE%-replies.graphml
python %BAT_DIR%\csv_to_weighted_digraph.py --csvfile %FN_BASE%-quotes.csv   --header --src-col 1 --tgt-col 2 --kind-col 4 --out-file %OUT_DIR%\%FN_BASE%-quotes.graphml
 