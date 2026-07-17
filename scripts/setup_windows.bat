@echo off
REM ============================================================
REM  Ghost Agent - Windows setup
REM  Creates a virtual environment and installs dependencies
REM ============================================================
setlocal

where python >nul 2>&1
if errorlevel 1 (
    echo [-] Python was not found on PATH. Install Python 3.10+ from https://python.org
    exit /b 1
)

echo [*] Creating virtual environment...
python -m venv ghost_env
if errorlevel 1 (
    echo [-] Failed to create the virtual environment.
    exit /b 1
)

echo [*] Upgrading pip...
call ghost_env\Scripts\activate.bat
python -m pip install --upgrade pip

echo [*] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [-] Failed to install Python dependencies.
    exit /b 1
)

echo [*] Installing Playwright Chromium browser...
playwright install chromium
if errorlevel 1 (
    echo [-] Playwright browser install failed.
    exit /b 1
)

if not exist ".env" (
    echo [*] Creating .env from .env.example ...
    copy .env.example .env >nul
    echo [!] Edit .env and add your TELEGRAM_BOT_TOKEN before running the agent.
)

echo.
echo [+] Setup complete. Run: scripts\run_windows.bat
endlocal
