@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv 2>nul || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --disable-pip-version-check -r backend\requirements.txt
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8420"
echo.
echo ZH-1 is starting at http://127.0.0.1:8420
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8420
endlocal
