# Copyright (c) 2026 Oracle and/or its affiliates.
# SPDX-License-Identifier: UPL-1.0

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$backendPort = $env:BACKEND_PORT
if (-not $backendPort) {
  $backendPort = "8002"
}

$frontendPort = $env:FRONTEND_PORT
if (-not $frontendPort) {
  $frontendPort = "5173"
}

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  Write-Host "Python virtual environment was not found. Run .\setup.ps1 first."
  exit 1
}

if (-not (Test-Path ".\node_modules")) {
  Write-Host "Node dependencies were not found. Run .\setup.ps1 first."
  exit 1
}

$env:VITE_API_PROXY_TARGET = "http://localhost:$backendPort"

Write-Host "Starting FastAPI backend on http://127.0.0.1:$backendPort"
$backendProcess = Start-Process `
  -FilePath $python `
  -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", $backendPort) `
  -WorkingDirectory $PSScriptRoot `
  -WindowStyle Hidden `
  -PassThru

Write-Host "Starting Vite frontend on http://127.0.0.1:$frontendPort"
Write-Host "Press Ctrl+C to stop both dev servers."

try {
  npm.cmd run dev -- --host 127.0.0.1 --port $frontendPort
} finally {
  if ($backendProcess -and -not $backendProcess.HasExited) {
    Write-Host "Stopping FastAPI backend..."
    Stop-Process -Id $backendProcess.Id -Force
  }
}
