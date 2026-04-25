@echo off
cd /d D:\sylvia_skill

for /f "delims=" %%V in ('powershell -NoProfile -ExecutionPolicy Bypass -File "D:\sylvia_skill\find-latest-claude.ps1"') do set LATEST=%%V

if "%LATEST%"=="" (
    echo [%DATE% %TIME%] ERROR: claude-code not found >> D:\sylvia_skill\claude.log
    exit /b 1
)

set CLAUDE_EXE=%APPDATA%\Claude\claude-code\%LATEST%\claude.exe

echo [%DATE% %TIME%] Starting claude %LATEST% minimized >> D:\sylvia_skill\claude.log

REM Use start /MIN to keep TTY but minimize the window
REM Tee stderr to a debug log for diagnostics
start "Sylvia-Backend" /MIN cmd /c ""%CLAUDE_EXE%" --dangerously-load-development-channels "plugin:weixin@cc-weixin" 2>> D:\sylvia_skill\logs\sylvia_stderr.log"
