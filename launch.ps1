# Launch Claude Dock on Windows.
# Right-click → Run with PowerShell, or: powershell -ExecutionPolicy Bypass -File launch.ps1
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
pip install -q -r "$dir\requirements.txt"
$py = if (Get-Command pythonw -ErrorAction SilentlyContinue) { "pythonw" } else { "python" }
Start-Process $py -ArgumentList "`"$dir\dock.py`""
