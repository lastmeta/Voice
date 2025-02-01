@echo off
cd /d C:\[BOTZ]\X_cerberus

REM Check if virtual environment exists, create if it doesn't
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Update pip within the virtual environment
python -m pip install --upgrade pip

REM Install/update requirements
pip install -r requirements.txt

REM Run the main script
python main.py

REM Keep the window open
cmd /k