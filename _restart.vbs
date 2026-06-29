Dim oShell
Set oShell = CreateObject("WScript.Shell")

' Kill all stuck CMD processes
oShell.Run "taskkill /f /im cmd.exe /t", 0, False
WScript.Sleep 2000

' Start fresh: run _run_py.bat in a new visible CMD window
Dim sDir
sDir = "D:\_claude-project\agent-wiki"
oShell.Run "cmd /k """ & sDir & "\_run_py.bat""", 1, False

WScript.Quit
