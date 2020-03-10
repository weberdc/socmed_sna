@echo off

rem set CALC_BIN=C:\Users\derek\Documents\development\election-watch\twitter\network_extraction
set CALC_BIN=%~dp0
set CALC=%CALC_BIN%\compare_communities.py

set G1=%1
set G2=%2
set OPTS=%3 %4 %5 %6 %7 %8 %9

if "%G1%" == "" set G1=graphs\rapid
if "%G2%" == "" set G2=graphs\twarc

python %CALC% -f1 %G1%-replies.graphml  -f2 %G2%-replies.graphml  %OPTS%
python %CALC% -f1 %G1%-mentions.graphml -f2 %G2%-mentions.graphml %OPTS%
python %CALC% -f1 %G1%-retweets.graphml -f2 %G2%-retweets.graphml %OPTS%


echo Done
