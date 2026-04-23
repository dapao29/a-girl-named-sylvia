@echo off
echo === Sylvia 后台服务状态 ===
echo.
tasklist /FI "IMAGENAME eq claude.exe" | find "claude.exe" >nul
if %ERRORLEVEL%==0 (
    echo [运行中] Claude CLI
    tasklist /FI "IMAGENAME eq claude.exe" | findstr claude.exe
) else (
    echo [未运行] Claude CLI
)
echo.
tasklist /FI "IMAGENAME eq bun.exe" | find "bun.exe" >nul
if %ERRORLEVEL%==0 (
    echo [运行中] cc-weixin (bun)
) else (
    echo [未运行] cc-weixin (bun)
)
echo.
echo 日志文件: D:\sylvia_skill\claude.log
pause
