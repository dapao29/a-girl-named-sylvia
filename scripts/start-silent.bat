@echo off
cd /d D:\sylvia_skill

REM Auto-detect latest claude-code version
set CLAUDE_DIR=%APPDATA%\Claude\claude-code
set LATEST=
for /f "delims=" %%V in ('dir /b /a:d /o:-n "%CLAUDE_DIR%" 2^>nul') do (
    if not defined LATEST set LATEST=%%V
)

if "%LATEST%"=="" (
    echo [%DATE% %TIME%] ERROR: claude-code not found >> D:\sylvia_skill\claude.log
    exit /b 1
)

set CLAUDE_EXE=%CLAUDE_DIR%\%LATEST%\claude.exe

echo [%DATE% %TIME%] Starting claude %LATEST% >> D:\sylvia_skill\claude.log

"%CLAUDE_EXE%" --dangerously-load-development-channels "plugin:weixin@cc-weixin" >> D:\sylvia_skill\claude.log 2>&1
