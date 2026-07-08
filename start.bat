@echo off
setlocal
set ROOT=%~dp0
set PYTHON=python
if exist "C:\Users\Linsa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set PYTHON=C:\Users\Linsa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
"%PYTHON%" "%ROOT%scripts\kb_server.py"
endlocal