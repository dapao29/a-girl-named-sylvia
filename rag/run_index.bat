@echo off
REM 一键启动 BGE-M3 全量索引（CPU，2-3 小时）
REM 输出到 build.log，可在另一窗口 tail -f 查看进度

cd /d D:\sylvia_skill\rag
set PY313=C:\Users\zzh19\AppData\Local\Programs\Python\Python313\python.exe
set PYTHONUNBUFFERED=1

echo [%DATE% %TIME%] Starting BGE-M3 full index of 116K corpus on CPU > build.log
"%PY313%" build_index.py >> build.log 2>&1
echo [%DATE% %TIME%] Done >> build.log
