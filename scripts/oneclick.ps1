Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Step([string]$Name, [scriptblock]$Action) {
  Write-Host "`n==> $Name" -ForegroundColor Cyan
  & $Action
}

function Ensure-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command '$Name' not found in PATH."
  }
}

function Run([string]$File, [string[]]$Arguments = @()) {
  & $File @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed: $File $($Arguments -join ' ')"
  }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "RepoMesh one-click setup starting..." -ForegroundColor Green
Write-Host "Repository: $repoRoot"

Step "Checking prerequisites" {
  Ensure-Command "node"
  Ensure-Command "pnpm"
  Ensure-Command "docker"
}

Step "Checking Docker daemon" {
  & cmd /c "docker info >nul 2>nul"
  if ($LASTEXITCODE -ne 0) {
    throw "Docker daemon is not running. Start Docker Desktop and rerun one-click setup."
  }
}

Step "Installing Node workspace dependencies" {
  Run "pnpm" @("install", "--frozen-lockfile=false")
}

Step "Building workspace" {
  Run "pnpm" @("build")
}

Step "Initializing RepoMesh config" {
  Run "node" @("apps/cli/dist/index.js", "init")
}

Step "Starting services" {
  Run "node" @("apps/cli/dist/index.js", "up")
}

Step "Health check" {
  Run "node" @("apps/cli/dist/index.js", "doctor")
}

Step "MCP connection details" {
  Run "node" @("apps/cli/dist/index.js", "mcp")
}

Write-Host "`nRepoMesh is ready." -ForegroundColor Green
Write-Host "Next: run 'node apps/cli/dist/index.js status' to view service status."
