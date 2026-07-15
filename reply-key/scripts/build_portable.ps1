param(
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if ([string]::IsNullOrWhiteSpace($Python)) {
    $Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
}
$Python = [System.IO.Path]::GetFullPath($Python)
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python 3.11 environment not found: $Python"
}

Push-Location $ProjectRoot
try {
    $Version = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($LASTEXITCODE -ne 0 -or $Version.Trim() -ne "3.11") {
        throw "ReplyKey must be built with Python 3.11. Found: $Version"
    }

    & $Python (Join-Path $ProjectRoot "scripts\build_icon.py")
    if ($LASTEXITCODE -ne 0) { throw "Icon build failed." }

    & $Python -m PyInstaller --noconfirm --clean (Join-Path $ProjectRoot "ReplyKey.spec")
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

    $PortableDir = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "dist\ReplyKey"))
    $ZipPath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "dist\ReplyKey-portable.zip"))
    $ExpectedDistRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "dist"))
    if (-not $PortableDir.StartsWith($ExpectedDistRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unexpected portable output path: $PortableDir"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $PortableDir "ReplyKey.exe") -PathType Leaf)) {
        throw "ReplyKey.exe was not produced."
    }
    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }
    Compress-Archive -LiteralPath $PortableDir -DestinationPath $ZipPath -CompressionLevel Optimal

    Write-Host "Portable directory: $PortableDir"
    Write-Host "Portable ZIP:       $ZipPath"
}
finally {
    Pop-Location
}

