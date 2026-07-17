@echo off
REM ============================================================
REM  Ghost Agent - Windows run
REM  Runs the Telegram agent. Use "main" to run the CLI instead.
REM ============================================================
setlocal

if not exist "ghost_env\Scripts\activate.bat" (
    echo [-] Virtual environment not found. Run: scripts\setup_windows.bat
    exit /b 1
)

call ghost_env\Scripts\activate.bat

REM Optional: set BROWSER_CHANNEL=chrome to use installed Google Chrome
REM set BROWSER_CHANNEL=chrome
REM set HEADLESS=false

if "%1"=="main" (
    python main.py
) else (
    python telegram_agent.py
)
endlocal
