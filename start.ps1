$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "python"
$Bundled = "C:\Users\Linsa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (Test-Path $Bundled) { $Python = $Bundled }
& $Python (Join-Path $Root "scripts\kb_server.py")