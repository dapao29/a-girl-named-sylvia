@echo off
echo 正在停止Sylvia后台服务...
taskkill /F /IM claude.exe 2>nul
taskkill /F /IM bun.exe /FI "COMMANDLINE eq *cc-weixin*" 2>nul
echo 已停止
pause
