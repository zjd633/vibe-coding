[CmdletBinding()]
param([switch]$E2E, [switch]$Help)

if ($Help) {
    Write-Output 'Usage: .\scripts\test.ps1 [-E2E]  # backend pytest, frontend unit tests/build, optional Playwright E2E'
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
$python = Join-Path $root 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'backend/.venv is missing. Run .\scripts\setup.ps1 first.' }
Push-Location $root
try { Invoke-NativeChecked 'backend pytest' $python @('-m', 'pytest', 'backend\tests') } finally { Pop-Location }
Push-Location (Join-Path $root 'frontend')
try {
    Invoke-NativeChecked 'frontend unit tests' 'npm.cmd' @('test')
    Invoke-NativeChecked 'frontend typecheck' 'npm.cmd' @('run', 'typecheck')
    Invoke-NativeChecked 'frontend production build' 'npm.cmd' @('run', 'build')
    if ($E2E) { Invoke-NativeChecked 'Playwright E2E' 'npx.cmd' @('playwright', 'test') }
} finally { Pop-Location }
