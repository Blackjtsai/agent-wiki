Dim oShell
Set oShell = CreateObject("WScript.Shell")
oShell.Run "cmd /k ""D:\_claude-project\agent-wiki\_fix_pg.bat""", 1, False
WScript.Quit
