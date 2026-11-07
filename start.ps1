param([int]$Port = 8000, [switch]$Marketplaces)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command failed (exit $LASTEXITCODE)." }
}

foreach ($dependency in @('uv', 'pnpm')) {
    if (-not (Get-Command $dependency -ErrorAction SilentlyContinue)) {
        throw "Install $dependency first. See README.md for setup."
    }
}

$syncArguments = @('sync', '--frozen')
if ($Marketplaces) { $syncArguments += @('--extra', 'marketplaces') }
Invoke-Checked 'uv' $syncArguments
Invoke-Checked 'pnpm' @('--dir', 'frontend', 'install', '--frozen-lockfile')
Invoke-Checked 'pnpm' @('--dir', 'frontend', 'build')
Write-Host "Style Max: http://127.0.0.1:$Port" -ForegroundColor Green
Invoke-Checked 'uv' @('run', '--no-sync', 'uvicorn', 'stylemax.app:app', '--host', '127.0.0.1', '--port', "$Port")
