<#
Start a long-running Python job of this project as an independent Windows process.

The process is created through WMI (Win32_Process.Create), so it does not belong to the terminal, editor or assistant
session that started it: closing that session, or the session hitting a usage limit, does not stop it. It stops only
when it finishes, fails, or the computer sleeps, restarts or shuts down. Output goes to logs\<Name>.log; the process
id is written to logs\<Name>.pid.

Usage (from the project root, in PowerShell):
  powershell -ExecutionPolicy Bypass -File scripts\run_detached.ps1 -Name wayback "scripts\archive_wayback.py --only-used 04_working\wayback_targets_20261110.csv"
  powershell -ExecutionPolicy Bypass -File scripts\run_detached.ps1 -Name rebuild "-c ""import subprocess; subprocess.run(['bash','scripts/rebuild_all.sh'])"""
Check progress:  powershell -ExecutionPolicy Bypass -File scripts\job_status.ps1
Stop a job:      Stop-Process -Id (Get-Content logs\<Name>.pid)
#>
param(
  [Parameter(Mandatory = $true)][string]$Name,
  [Parameter(Mandatory = $true)][string]$PyArgs
)
$root = Split-Path -Parent $PSScriptRoot
$logs = Join-Path $root "logs"
New-Item -ItemType Directory -Force $logs | Out-Null
$log = Join-Path $logs "$Name.log"
$python = (Get-Command python -ErrorAction Stop).Source
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
Add-Content -Path $log -Value "`n=== $stamp start: python $PyArgs" -Encoding utf8
$cmd = "cmd.exe /c set PYTHONIOENCODING=utf-8&& set PYTHONUNBUFFERED=1&& `"$python`" $PyArgs >> `"$log`" 2>&1"
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $root }
if ($r.ReturnValue -ne 0) { throw "Could not start the job (WMI return value $($r.ReturnValue))." }
Set-Content -Path (Join-Path $logs "$Name.pid") -Value $r.ProcessId -Encoding ascii
"Started '$Name' as process $($r.ProcessId). Log: $log"
