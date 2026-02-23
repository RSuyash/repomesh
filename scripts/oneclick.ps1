param(
  [string]$TargetRepoPath = ""
)

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

function ConvertFrom-JsonSafe([string]$Text) {
  if ([string]::IsNullOrWhiteSpace($Text)) {
    return $null
  }

  try {
    return ($Text | ConvertFrom-Json)
  } catch {
    $start = $Text.IndexOf("{")
    $end = $Text.LastIndexOf("}")
    if ($start -ge 0 -and $end -gt $start) {
      $slice = $Text.Substring($start, $end - $start + 1)
      try {
        return ($slice | ConvertFrom-Json)
      } catch {
        return $null
      }
    }
    return $null
  }
}

function Invoke-Api([string]$Method, [string]$Path, [object]$Body = $null) {
  if (-not $script:token) {
    throw "API token is not initialized."
  }
  $headers = @{ "x-repomesh-token" = $script:token }
  $uri = "http://localhost:8787$Path"
  if ($null -eq $Body) {
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
  }
  $json = ($Body | ConvertTo-Json -Depth 20 -Compress)
  return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -ContentType "application/json" -Body $json
}

function Invoke-McpTool([string]$ToolName, [hashtable]$Arguments = @{}) {
  $payload = @{
    jsonrpc = "2.0"
    id = [guid]::NewGuid().ToString()
    method = "tool.call"
    params = @{
      name = $ToolName
      arguments = $Arguments
    }
  }
  $response = Invoke-Api -Method "POST" -Path "/mcp/http" -Body $payload
  if ($response.PSObject.Properties.Name -contains "error") {
    throw "MCP tool '$ToolName' failed: $($response.error | ConvertTo-Json -Depth 10 -Compress)"
  }
  return $response.result
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
  $script:token = (Get-Content $tokenPath -Raw).Trim()
  $envPath = Join-Path $repoRoot "infra\docker\.env"
  Set-EnvVar -FilePath $envPath -Key "REPO_MESH_LOCAL_TOKEN" -Value $script:token

  $resolvedTarget = $TargetRepoPath
  if ([string]::IsNullOrWhiteSpace($resolvedTarget)) {
    $resolvedTarget = $repoRoot
  }
  if (-not (Test-Path $resolvedTarget)) {
    throw "Target repo path not found: $resolvedTarget"
  }
  $resolvedTarget = (Resolve-Path $resolvedTarget).Path

  Set-EnvVar -FilePath $envPath -Key "TARGET_REPO_HOST_PATH" -Value $resolvedTarget
  Set-EnvVar -FilePath $envPath -Key "ADAPTER_WORKSPACE_ROOT" -Value "/workspace/target-repo"
  Write-Host "Target repo mounted from: $resolvedTarget" -ForegroundColor DarkCyan
}

Step "Generating MCP JSON config" {
  Run "node" @("apps/cli/dist/index.js", "mcp", "--write", "--client", "qwen")
}

Step "Starting services" {
  Run "node" @("apps/cli/dist/index.js", "up")
}

Step "Health check" {
  $maxAttempts = 30
  for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    $raw = node apps/cli/dist/index.js doctor 2>&1 | Out-String
    $status = ConvertFrom-JsonSafe $raw
    $apiHealthy = $false
    if ($null -ne $status -and $status.PSObject.Properties.Name -contains "api_health") {
      $apiHealthy = ($status.api_health -eq $true)
    }

    if ($apiHealthy) {
      Write-Host ($raw | Out-String)
      return
    }
    Start-Sleep -Seconds 2
  }
  throw "API health check did not become ready in time."
}

Step "MCP connection details" {
  Run "node" @("apps/cli/dist/index.js", "mcp")
}

Step "Founder MCP smoke test" {
  $toolsResponse = Invoke-Api -Method "GET" -Path "/mcp/tools"
  $tools = @($toolsResponse.tools)
  $requiredTools = @(
    "orchestrator.status",
    "adapter.execute",
    "adapter.status",
    "file.skeleton",
    "file.symbol_logic",
    "file.search_replace",
    "summarizer.tick",
    "summarizer.status"
  )
  $missing = @($requiredTools | Where-Object { $tools -notcontains $_ })
  if ($missing.Count -gt 0) {
    throw "Missing required MCP tools: $($missing -join ', ')"
  }

  $agentName = "oneclick-founder-agent-$([guid]::NewGuid().ToString().Substring(0,8))"
  $agent = Invoke-Api -Method "POST" -Path "/v1/agents/register" -Body @{
    name = $agentName
    type = "cli"
    capabilities = @{
      execute = $true
      model_tiers = @("small", "frontier")
      adapter_profiles = @("generic-shell")
    }
  }

  $task = Invoke-Api -Method "POST" -Path "/v1/tasks" -Body @{
    goal = "Oneclick founder E2E validation"
    description = "Validate assign + execute + summarize flow."
    scope = @{
      command = "python -c ""from pathlib import Path; Path('repomesh_smoke.py').write_text('def smoke():`n    return 42`n', encoding='utf-8'); print('oneclick-ok')"""
      cwd = "."
    }
    priority = 5
  }

  Invoke-Api -Method "POST" -Path "/v1/tasks/$($task.id)/claim" -Body @{
    agent_id = $agent.id
    resource_key = "task://$($task.id)"
    lease_ttl = 120
  } | Out-Null

  $execution = Invoke-McpTool -ToolName "adapter.execute" -Arguments @{
    agent_id = $agent.id
    task_id = $task.id
    max_tasks = 1
  }

  $assignedTasks = Invoke-Api -Method "GET" -Path "/v1/tasks?assignee=$($agent.id)"
  $finalTask = @($assignedTasks | Where-Object { $_.id -eq $task.id })[0]
  if ($null -eq $finalTask -or $finalTask.status -ne "completed") {
    throw "Founder smoke test failed: task did not complete."
  }

  $skeleton = Invoke-McpTool -ToolName "file.skeleton" -Arguments @{
    file_path = "repomesh_smoke.py"
  }
  if (@($skeleton.symbols).Count -eq 0 -or @($skeleton.symbols | Where-Object { $_.name -eq "smoke" }).Count -eq 0) {
    throw "Founder smoke test failed: file.skeleton returned no symbols."
  }

  $summary = Invoke-McpTool -ToolName "summarizer.tick" -Arguments @{
    max_tasks = 20
  }

  Write-Host ("Founder smoke test passed. " +
    "agent_id={0} task_id={1} executed={2} summaries={3}" -f `
      $agent.id, $task.id, @($execution.executed).Count, $summary.count) -ForegroundColor Green
}

Write-Host "`nRepoMesh is ready." -ForegroundColor Green
Write-Host "Next: run 'node apps/cli/dist/index.js status' to view service status."
