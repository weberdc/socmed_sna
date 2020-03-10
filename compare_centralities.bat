@echo off

rem set CALC_BIN=C:\Users\derek\Documents\development\election-watch\twitter\network_extraction
set CALC_BIN=%~dp0
set CALC=%CALC_BIN%\compare_centralities.py

set TOPX=%1
set G1=%2
set G2=%3
set OUT_PREFIX=%4
set EXTRA_ARGS=%5 %6 %7 %8 %9

rem if "%G1%" == "" set G1=graphs\twarc
rem if "%G2%" == "" set G2=graphs\rapid


echo MENTIONS - %G1% %G2%
echo Interaction,Centrality,top_x,in_common,tau,tau_p-value,rho,rho_p-value
echo|set /p="MENTION,DEGREE,"
python %CALC% -x %TOPX% -f1 %G1%-mentions.graphml -f2 %G2%-mentions.graphml -t DEGREE      -o %OUT_PREFIX%-mentions-DEGREE.csv %EXTRA_ARGS%
echo|set /p="MENTION,BETWEENNESS,"
python %CALC% -x %TOPX% -f1 %G1%-mentions.graphml -f2 %G2%-mentions.graphml -t BETWEENNESS -o %OUT_PREFIX%-mentions-BETWEENNESS.csv %EXTRA_ARGS%
echo|set /p="MENTION,CLOSENESS,"
python %CALC% -x %TOPX% -f1 %G1%-mentions.graphml -f2 %G2%-mentions.graphml -t CLOSENESS   -o %OUT_PREFIX%-mentions-CLOSENESS.csv %EXTRA_ARGS%
echo|set /p="MENTION,EIGENVECTOR,"
python %CALC% -x %TOPX% -f1 %G1%-mentions.graphml -f2 %G2%-mentions.graphml -t EIGENVECTOR -o %OUT_PREFIX%-mentions-EIGENVECTOR.csv %EXTRA_ARGS%

rem echo
rem echo QUOTES - Twarc RAPID
rem echo Interaction,Centrality,top_x,in_common,tau,p-value
rem python %CALC% -x %TOPX% -f1 %G1%-quotes.graphml -f2 %G2%-quotes.graphml -t DEGREE -h
rem python %CALC% -x %TOPX% -f1 %G1%-quotes.graphml -f2 %G2%-quotes.graphml -t BETWEENNESS
rem python %CALC% -x %TOPX% -f1 %G1%-quotes.graphml -f2 %G2%-quotes.graphml -t CLOSENESS
rem python %CALC% -x %TOPX% -f1 %G1%-quotes.graphml -f2 %G2%-quotes.graphml -t EIGENVECTOR

echo ""
echo REPLIES - %G1% %G2%
echo Interaction,Centrality,top_x,in_common,tau,tau_p-value,rho,rho_p-value
echo|set /p="REPLY,DEGREE,"
python %CALC% -x %TOPX% -f1 %G1%-replies.graphml -f2 %G2%-replies.graphml -t DEGREE      -o %OUT_PREFIX%-replies-DEGREE.csv %EXTRA_ARGS%
echo|set /p="REPLY,BETWEENNESS,"
python %CALC% -x %TOPX% -f1 %G1%-replies.graphml -f2 %G2%-replies.graphml -t BETWEENNESS -o %OUT_PREFIX%-replies-BETWEENNESS.csv %EXTRA_ARGS%
echo|set /p="REPLY,CLOSENESS,"
python %CALC% -x %TOPX% -f1 %G1%-replies.graphml -f2 %G2%-replies.graphml -t CLOSENESS   -o %OUT_PREFIX%-replies-CLOSENESS.csv %EXTRA_ARGS%
echo|set /p="REPLY,EIGENVECTOR,"
python %CALC% -x %TOPX% -f1 %G1%-replies.graphml -f2 %G2%-replies.graphml -t EIGENVECTOR -o %OUT_PREFIX%-replies-EIGENVECTOR.csv %EXTRA_ARGS%

echo ""
echo Done
