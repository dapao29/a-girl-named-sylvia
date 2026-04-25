Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\sylvia_skill"

' Start claude (normal window)
WshShell.Run "cmd /c D:\sylvia_skill\start-silent.bat", 1, False

' Wait for prompt to render
WScript.Sleep 8000

' Fire Enter via Win32 PostMessage (reliable, no focus needed)
WshShell.Run "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""D:\sylvia_skill\press-enter.ps1""", 0, True

' Give bun time to spawn then minimize the window
WScript.Sleep 5000
On Error Resume Next
titles = Array("claude", "Claude", "Sylvia-Backend", "Claude Code")
For Each t In titles
  If WshShell.AppActivate(t) Then
    WScript.Sleep 300
    WshShell.SendKeys "% n"
    Exit For
  End If
Next
