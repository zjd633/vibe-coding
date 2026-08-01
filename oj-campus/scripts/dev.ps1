[CmdletBinding()]
param([switch]$Help)

if ($Help) {
    Write-Output 'Usage: .\scripts\dev.ps1  # start API (8000), worker and Vite (5173); Ctrl+C stops all child processes'
    exit 0
}

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not (Test-Path -LiteralPath $python)) { throw 'backend/.venv is missing. Run .\scripts\setup.ps1 first.' }
if (-not $npm) { throw 'npm.cmd is missing. Run .\scripts\setup.ps1 after installing Node.js.' }
if (-not (Test-Path -LiteralPath (Join-Path $frontend 'node_modules'))) { throw 'frontend/node_modules is missing. Run .\scripts\setup.ps1 first.' }

function Stop-ProcessTree([int]$ProcessId) {
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) { Stop-ProcessTree -ProcessId $child.ProcessId }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Start-Component([string]$Name, [string]$WorkingDirectory, [string]$FilePath, [string[]]$Arguments) {
    # Start-Process children inherit OJ_DATABASE_URL without modifying this script's environment.
    $process = Start-Process -FilePath $FilePath -WorkingDirectory $WorkingDirectory -ArgumentList $Arguments -WindowStyle Hidden -PassThru
    return [pscustomobject]@{ Name = $Name; Process = $process }
}

function Test-Components($Components) {
    foreach ($component in $Components) {
        $component.Process.Refresh()
        if ($component.Process.HasExited) {
            throw "$($component.Name) has exited with code $($component.Process.ExitCode)."
        }
    }
}

$components = @()
try {
    $components += Start-Component 'API' $backend $python @('-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8000')
    $components += Start-Component 'Worker' $backend $python @('-m', 'app.worker')
    $components += Start-Component 'Vite' $frontend $npm @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173')
    Start-Sleep -Seconds 1
    Test-Components $components
    Write-Output 'OJ Campus is running at http://127.0.0.1:5173 (API http://127.0.0.1:8000). Press Ctrl+C to stop it.'
    while ($true) {
        Test-Components $components
        Start-Sleep -Seconds 1
    }
} finally {
    foreach ($component in $components) {
        if ($component -and -not $component.Process.HasExited) { Stop-ProcessTree -ProcessId $component.Process.Id }
    }
}
