param(
    [string]$Executable = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if ([string]::IsNullOrWhiteSpace($Executable)) {
    $Executable = Join-Path $ProjectRoot "dist\ReplyKey\ReplyKey.exe"
}
$Executable = [System.IO.Path]::GetFullPath($Executable)
$ExpectedDistRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "dist"))
if (-not $Executable.StartsWith($ExpectedDistRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Smoke test only accepts an executable under this project's dist directory."
}
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
    throw "Executable not found: $Executable"
}
if (Get-Process -Name "ReplyKey" -ErrorAction SilentlyContinue) {
    throw "A ReplyKey process is already running. Exit it before the smoke test."
}

$TempRoot = [System.IO.Path]::GetFullPath($env:TEMP)
$SmokeAppData = [System.IO.Path]::GetFullPath((Join-Path $TempRoot ("ReplyKeySmoke-" + [guid]::NewGuid().ToString("N"))))
if (-not $SmokeAppData.StartsWith($TempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unexpected smoke-test APPDATA path."
}
New-Item -ItemType Directory -Path $SmokeAppData | Out-Null
$PreviousAppData = $env:APPDATA
$First = $null
$Second = $null
try {
    $env:APPDATA = $SmokeAppData
    $First = Start-Process -FilePath $Executable -ArgumentList "--background" -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 3
    $First.Refresh()
    if ($First.HasExited) {
        throw "First portable instance exited unexpectedly with code $($First.ExitCode)."
    }

    $Second = Start-Process -FilePath $Executable -ArgumentList "--background" -WindowStyle Hidden -PassThru
    if (-not $Second.WaitForExit(5000)) {
        throw "Second instance did not exit after notifying the primary instance."
    }
    $First.Refresh()
    if ($First.HasExited) {
        throw "Primary instance exited during the single-instance check."
    }
    Write-Host "Portable smoke test passed: startup and single-instance behavior are healthy."
}
finally {
    if ($Second -and -not $Second.HasExited) {
        Stop-Process -Id $Second.Id -Force -ErrorAction SilentlyContinue
    }
    if ($First -and -not $First.HasExited) {
        Stop-Process -Id $First.Id -Force -ErrorAction SilentlyContinue
        $First.WaitForExit(3000) | Out-Null
    }
    $env:APPDATA = $PreviousAppData
    if (
        (Test-Path -LiteralPath $SmokeAppData) -and
        $SmokeAppData.StartsWith($TempRoot, [System.StringComparison]::OrdinalIgnoreCase)
    ) {
        Remove-Item -LiteralPath $SmokeAppData -Recurse -Force
    }
}
