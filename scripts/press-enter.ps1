# Press Enter on Sylvia claude via Win32 PostMessage

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class PressKey {
    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
    public const int VK_RETURN = 0x0D;
}
"@

$sylvia = Get-Process claude -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*AppData\Roaming\Claude\claude-code*"
} | Sort-Object StartTime -Descending | Select-Object -First 1

if (-not $sylvia) { Write-Host "NO_SYLVIA"; exit 1 }

Write-Host "Sylvia PID: $($sylvia.Id)"
Write-Host "MainWindowHandle: $($sylvia.MainWindowHandle)"

# Also find the cmd wrapper launched by VBS
$cmds = Get-Process cmd -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowHandle -ne 0
}

$targets = @()
if ($sylvia.MainWindowHandle -ne 0) { $targets += $sylvia.MainWindowHandle }
foreach ($c in $cmds) { $targets += $c.MainWindowHandle }

Write-Host "Targets: $($targets.Count) window(s)"

# Press Enter 3 times, 1 second apart
for ($i = 0; $i -lt 3; $i++) {
    foreach ($h in $targets) {
        [void][PressKey]::PostMessage($h, [PressKey]::WM_KEYDOWN, [IntPtr][PressKey]::VK_RETURN, [IntPtr]::Zero)
        Start-Sleep -Milliseconds 50
        [void][PressKey]::PostMessage($h, [PressKey]::WM_KEYUP, [IntPtr][PressKey]::VK_RETURN, [IntPtr]::Zero)
    }
    Start-Sleep -Seconds 1
}

Write-Host "Done"
