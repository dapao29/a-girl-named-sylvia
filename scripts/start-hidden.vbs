Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\sylvia_skill"
WshShell.Run "cmd /c D:\sylvia_skill\start-silent.bat", 0, False
