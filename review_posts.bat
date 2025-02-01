@echo off
cd /d C:\[BOTZ]\X_cerberus

REM Activate virtual environment
call venv\Scripts\activate

REM Run the tweet review script
python review_tweets.py

REM Keep the window open
pause