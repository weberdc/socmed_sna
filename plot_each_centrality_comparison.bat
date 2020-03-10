@echo off

rem set CALC_BIN=C:\Users\derek\Documents\development\election-watch\twitter\network_extraction
set CALC_BIN=%~dp0
set CALC=%CALC_BIN%\plot_ranked_items.py

set IN_PREFIX=%1
set OUT_PREFIX=%2
set LABELS=%3

set INT=mentions
set CENT=BETWEENNESS
python %CALC% -f %IN_PREFIX%-%INT%-%CENT%.csv -o %OUT_PREFIX%-%INT%-%CENT%_scatterplot.png --header -l %LABELS% -t "Ranked %INT% by %CENT% centrality" --batch-mode
set CENT=DEGREE
python %CALC% -f %IN_PREFIX%-%INT%-%CENT%.csv -o %OUT_PREFIX%-%INT%-%CENT%_scatterplot.png --header -l %LABELS% -t "Ranked %INT% by %CENT% centrality" --batch-mode
set CENT=CLOSENESS
python %CALC% -f %IN_PREFIX%-%INT%-%CENT%.csv -o %OUT_PREFIX%-%INT%-%CENT%_scatterplot.png --header -l %LABELS% -t "Ranked %INT% by %CENT% centrality" --batch-mode
set CENT=EIGENVECTOR
python %CALC% -f %IN_PREFIX%-%INT%-%CENT%.csv -o %OUT_PREFIX%-%INT%-%CENT%_scatterplot.png --header -l %LABELS% -t "Ranked %INT% by %CENT% centrality" --batch-mode

set INT=replies
set CENT=BETWEENNESS
python %CALC% -f %IN_PREFIX%-%INT%-%CENT%.csv -o %OUT_PREFIX%-%INT%-%CENT%_scatterplot.png --header -l %LABELS% -t "Ranked %INT% by %CENT% centrality" --batch-mode
set CENT=DEGREE
python %CALC% -f %IN_PREFIX%-%INT%-%CENT%.csv -o %OUT_PREFIX%-%INT%-%CENT%_scatterplot.png --header -l %LABELS% -t "Ranked %INT% by %CENT% centrality" --batch-mode
set CENT=CLOSENESS
python %CALC% -f %IN_PREFIX%-%INT%-%CENT%.csv -o %OUT_PREFIX%-%INT%-%CENT%_scatterplot.png --header -l %LABELS% -t "Ranked %INT% by %CENT% centrality" --batch-mode
set CENT=EIGENVECTOR
python %CALC% -f %IN_PREFIX%-%INT%-%CENT%.csv -o %OUT_PREFIX%-%INT%-%CENT%_scatterplot.png --header -l %LABELS% -t "Ranked %INT% by %CENT% centrality" --batch-mode

echo Done
