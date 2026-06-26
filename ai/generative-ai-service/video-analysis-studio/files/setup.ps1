# Copyright (c) 2026 Oracle and/or its affiliates.
# SPDX-License-Identifier: UPL-1.0

param(
  [switch]$SkipNodeInstall
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Test-Command($Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-Command "uv")) {
  Write-Host "Installing uv..."
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = "$env:USERPROFILE\.local\bin;$env:APPDATA\uv\bin;$env:Path"
}

if (-not (Test-Path ".\.venv")) {
  Write-Host "Creating Python virtual environment..."
  uv venv .venv
}

Write-Host "Installing Python dependencies..."
uv pip install -r requirements.txt

if (-not (Test-Path ".\.env") -and (Test-Path ".\.env.example")) {
  Write-Host "Creating local .env from .env.example..."
  Copy-Item ".\.env.example" ".\.env"
}

if (-not $SkipNodeInstall) {
  if (-not (Test-Path ".\node_modules")) {
    Write-Host ""
    Write-Host "Node dependencies are not installed."
    Write-Host "If your network requires VPN or proxy access for npm, enable it before continuing."
    Write-Host "Otherwise npm package downloads can time out or fail."
    $answer = Read-Host "Run npm install now? [y/N]"
    if ($answer -match "^(y|yes)$") {
      npm.cmd install
    } else {
      Write-Host "Skipped npm install. Run it later after enabling network access if needed."
    }
  } else {
    Write-Host "Node dependencies already installed."
  }
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Run the app with: .\start.ps1"
