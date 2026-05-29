@echo off
cd /d "%~dp0"
py -m venv .venv 2>nul
call .venv\Scripts\activate.bat
pip install -r requirements.txt
py -c "from backend.database import init_db; init_db()"
echo Open http://127.0.0.1:8080
uvicorn backend.main:app --reload --port 8080
