Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "F:\Users\rival\kasir-app"
WshShell.Run "cmd /c jalan.bat", 0, False
