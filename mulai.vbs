Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\parfum\kasir-app"
WshShell.Run "cmd /c jalan.bat", 0, False
