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

function Set-EnvVar([string]$FilePath, [string]$Key, [string]$Value) {
  if (-not (Test-Path $FilePath)) {
    New-Item -ItemType File -Force -Path $FilePath | Out-Null
  }

  $content = Get-Content $FilePath -Raw
  $pattern = "(?m)^$Key=.*$"
  if ($content -match $pattern) {
    $content = [Regex]::Replace($content, $pattern, "$Key=$Value")
  } else {
    if ($content.Length -gt 0 -and -not $content.EndsWith("`n")) {
      $content += "`n"
    }
    $content += "$Key=$Value`n"
  }
  Set-Content -Path $FilePath -Value $content
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

Step "Syncing API token" {
  $tokenPath = Join-Path $repoRoot ".repomesh\token"
  if (-not (Test-Path $tokenPath)) {
    throw "Token file not found at $tokenPath"
  }
  $token = (Get-Content $tokenPath -Raw).Trim()
  $envPath = Join-Path $repoRoot "infra\docker\.env"
  Set-EnvVar -FilePath $envPath -Key "REPO_MESH_LOCAL_TOKEN" -Value $token
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
