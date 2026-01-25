' TaskMancer 靜默啟動器
' 雙擊此檔案即可啟動服務，完全無視窗

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """d:\Dev\TaskMancer\TaskMancer.bat""", 0, False

' 等待 3 秒後開啟瀏覽器
WScript.Sleep 3000
WshShell.Run "http://localhost:5173"
