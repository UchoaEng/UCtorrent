param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Ambiente virtual nao encontrado em .venv. Crie com: py -3.11 -m venv .venv"
}

& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar pip." }
& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias do app." }
& $Python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias de build." }

$ModeArgs = @("--onedir")
if ($OneFile) {
    $ModeArgs = @("--onefile")
}

$PyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", "UCtorrent",
    "--icon", "uctorrent\app\assets\uctorrent-logo.png",
    "--add-data", "uctorrent\app\assets;uctorrent\app\assets",
    "--add-data", "uctorrent\web;uctorrent\web",
    "--collect-all", "PySide6",
    "--collect-all", "uvicorn",
    "--collect-all", "fastapi",
    "--collect-all", "pydantic",
    "--collect-all", "sqlalchemy",
    "--collect-all", "feedparser",
    "--hidden-import", "libtorrent",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.protocols.websockets.auto"
) + $ModeArgs + @("uctorrent\main.py")

& $Python @PyInstallerArgs
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou ao gerar o executavel." }

Write-Host ""
Write-Host "Build concluido."
if ($OneFile) {
    Write-Host "Executavel: $Root\dist\UCtorrent.exe"
} else {
    Write-Host "Executavel: $Root\dist\UCtorrent\UCtorrent.exe"
}
