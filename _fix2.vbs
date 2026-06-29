Dim oShell
Set oShell = CreateObject("WScript.Shell")

' Kill WerFault (error dialogs) and old CMD windows
oShell.Run "taskkill /f /im werfault.exe /t", 0, False
WScript.Sleep 500
oShell.Run "taskkill /f /im cmd.exe /t", 0, False
WScript.Sleep 2000

' Run fix_pg_auth.py in hidden CMD (no window), wait for completion
Dim sDir
sDir = "D:\_claude-project\agent-wiki"
oShell.Run "cmd /c cd /d """ & sDir & """ && uv run python _fix_pg_auth.py > _fix_pg_log.txt 2>&1", 0, True

' Now run _run_py.bat in a visible window
oShell.Run "cmd /k """ & sDir & "\_run_py.bat""", 1, False

WScript.Quit
