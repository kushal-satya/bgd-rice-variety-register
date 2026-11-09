<#
Show the long-running jobs started with scripts\run_detached.ps1: whether each is still running and the last lines of
its log. Usage (from the project root): powershell -ExecutionPolicy Bypass -File scripts\job_status.ps1
#>
$root = Split-Path -Parent $PSScriptRoot
Get-ChildItem (Join-Path $root "logs") -Filter *.pid | ForEach-Object {
  $name = $_.BaseName
  $procId = [int](Get-Content $_.FullName)
  $alive = $null -ne (Get-CimInstance Win32_Process -Filter "ProcessId = $procId" -ErrorAction SilentlyContinue)
  $state = if ($alive) { "running" } else { "finished or stopped" }
  "--- $name (process $procId): $state"
  $log = Join-Path $root "logs\$name.log"
  if (Test-Path $log) { Get-Content $log -Tail 4 }
}
