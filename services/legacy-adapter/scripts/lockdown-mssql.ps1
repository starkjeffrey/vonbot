# Windows Firewall Lockdown Script for Legacy MSSQL Server
#
# This script configures Windows Firewall to ONLY allow your VPS to access
# the legacy MSSQL server, blocking all other internet traffic.
#
# CRITICAL SECURITY: This protects your sa/123456 MSSQL server by ensuring
# only your secure VPS can connect to it.
#
# Usage:
#   1. Open PowerShell as Administrator on the Windows 11 machine
#   2. Run: .\lockdown-mssql.ps1 -VpsIP "YOUR_VPS_IP" -MssqlPort 14433
#
# Example:
#   .\lockdown-mssql.ps1 -VpsIP "203.0.113.50" -MssqlPort 14433

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsIP,

    [Parameter(Mandatory=$false)]
    [int]$MssqlPort = 1433,

    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

# Require Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🔒 MSSQL Server Firewall Lockdown Script" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Validate IP address format
if ($VpsIP -notmatch '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
    Write-Host "❌ ERROR: Invalid IP address format: $VpsIP" -ForegroundColor Red
    Write-Host "Expected format: 203.0.113.50" -ForegroundColor Yellow
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  VPS IP Address: $VpsIP" -ForegroundColor White
Write-Host "  MSSQL Port: $MssqlPort" -ForegroundColor White
Write-Host "  Dry Run: $($DryRun.IsPresent)" -ForegroundColor White
Write-Host ""

if ($DryRun) {
    Write-Host "🧪 DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Function to execute or simulate command
function Invoke-FirewallCommand {
    param([string]$Description, [scriptblock]$Command)

    Write-Host "  $Description..." -NoNewline

    if ($DryRun) {
        Write-Host " [DRY RUN]" -ForegroundColor Yellow
        return
    }

    try {
        & $Command
        Write-Host " ✅" -ForegroundColor Green
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        Write-Host "    Error: $_" -ForegroundColor Red
        throw
    }
}

Write-Host "Step 1: Removing old firewall rules..." -ForegroundColor Cyan

# Remove existing rules (if any)
Invoke-FirewallCommand "Removing old 'MSSQL Legacy Access' rules" {
    Get-NetFirewallRule -DisplayName "MSSQL Legacy Access*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
}

Write-Host ""
Write-Host "Step 2: Creating new firewall rules..." -ForegroundColor Cyan

# Rule 1: Allow ONLY VPS IP
Invoke-FirewallCommand "Allow connections from VPS ($VpsIP)" {
    New-NetFirewallRule `
        -DisplayName "MSSQL Legacy Access - VPS Only" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $MssqlPort `
        -RemoteAddress $VpsIP `
        -Action Allow `
        -Profile Any `
        -Enabled True `
        -Description "Allow legacy adapter service on VPS to access MSSQL. Created by lockdown-mssql.ps1"
}

# Rule 2: Block all other connections to this port
Invoke-FirewallCommand "Block all other connections to port $MssqlPort" {
    New-NetFirewallRule `
        -DisplayName "MSSQL Legacy Access - Block Others" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $MssqlPort `
        -Action Block `
        -Profile Any `
        -Enabled True `
        -Priority 1 `
        -Description "Block all non-VPS connections to MSSQL port. Created by lockdown-mssql.ps1"
}

Write-Host ""
Write-Host "Step 3: Verifying firewall rules..." -ForegroundColor Cyan

if (-not $DryRun) {
    $rules = Get-NetFirewallRule -DisplayName "MSSQL Legacy Access*" |
        Select-Object DisplayName, Enabled, Direction, Action

    Write-Host ""
    Write-Host "Current firewall rules:" -ForegroundColor Green
    $rules | Format-Table -AutoSize

    # Test port binding
    Write-Host ""
    Write-Host "Step 4: Testing port binding..." -ForegroundColor Cyan

    $listening = Get-NetTCPConnection -LocalPort $MssqlPort -State Listen -ErrorAction SilentlyContinue
    if ($listening) {
        Write-Host "  ✅ MSSQL is listening on port $MssqlPort" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  WARNING: No service is listening on port $MssqlPort" -ForegroundColor Yellow
        Write-Host "  Make sure MSSQL Server is running and configured for port $MssqlPort" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Firewall lockdown complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if (-not $DryRun) {
    Write-Host "Security Status:" -ForegroundColor Green
    Write-Host "  ✅ MSSQL port $MssqlPort is now protected" -ForegroundColor White
    Write-Host "  ✅ Only VPS IP $VpsIP can connect" -ForegroundColor White
    Write-Host "  ✅ All other connection attempts will be blocked" -ForegroundColor White
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Test connection from VPS: telnet $env:COMPUTERNAME $MssqlPort" -ForegroundColor White
    Write-Host "  2. Verify blocking from other IP (should fail)" -ForegroundColor White
    Write-Host "  3. Deploy legacy adapter service on VPS" -ForegroundColor White
    Write-Host ""
    Write-Host "To remove these rules later:" -ForegroundColor Yellow
    Write-Host "  Get-NetFirewallRule -DisplayName 'MSSQL Legacy Access*' | Remove-NetFirewallRule" -ForegroundColor White
} else {
    Write-Host "🧪 Dry run completed successfully" -ForegroundColor Yellow
    Write-Host "Run without -DryRun parameter to apply changes" -ForegroundColor Yellow
}

Write-Host ""
