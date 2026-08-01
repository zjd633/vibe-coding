[CmdletBinding()]
param([switch]$Help)

if ($Help) {
    Write-Output 'Usage: .\scripts\setup.ps1  # create backend/.venv, install dependencies, initialize/seed DB, install frontend packages'
    exit 0
}

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
function Invoke-NativeChecked([string]$Stage, [string]$FilePath, [string[]]$Arguments) {
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Stage failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}
function Require-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { throw "$Name was not found. $Hint" }
}
Require-Command python 'Install Python 3.11+ and ensure python is on PATH.'
Require-Command node 'Install Node.js 20+ and reopen PowerShell.'
Require-Command npm 'Install Node.js/npm and reopen PowerShell.'
$compiler = if ($env:OJ_GPP_PATH) { $env:OJ_GPP_PATH } else { 'E:\mingw64\bin\g++.exe' }
if (-not (Test-Path -LiteralPath $compiler -PathType Leaf)) { throw "g++ was not found at '$compiler'. Install MinGW-w64 or set OJ_GPP_PATH to g++.exe." }

$backend = Join-Path $root 'backend'
$venv = Join-Path $backend '.venv'
if (-not (Test-Path -LiteralPath $venv)) { Invoke-NativeChecked 'create backend virtual environment' 'python' @('-m', 'venv', $venv) }
$python = Join-Path $venv 'Scripts\python.exe'
Invoke-NativeChecked 'upgrade pip' $python @('-m', 'pip', 'install', '--upgrade', 'pip')
Invoke-NativeChecked 'install backend requirements' $python @('-m', 'pip', 'install', '-r', (Join-Path $backend 'requirements.txt'))
Push-Location $backend
try { Invoke-NativeChecked 'initialize and seed database' $python @('-m', 'app.seed') } finally { Pop-Location }
Push-Location (Join-Path $root 'frontend')
try { Invoke-NativeChecked 'install frontend dependencies' 'npm.cmd' @('ci') } finally { Pop-Location }
Write-Output 'Setup complete. Run .\scripts\dev.ps1 to start the local demo.'
