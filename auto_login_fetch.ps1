#!/usr/bin/env pwsh
<#
.SYNOPSIS
Automated X Session Login & Twitter Fetch
Checks if authenticated session exists. If not, opens login page, waits for completion, then fetches recent posts.

.USAGE
powershell -ExecutionPolicy Bypass -File auto_login_fetch.ps1
#>

$API_URL = "http://localhost:5050"
$MAX_WAIT = 300  # 5 minutes timeout for login

function Check-Session {
    Write-Host "🔍 Checking X session status..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/x-session/status" -UseBasicParsing -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        return $data.has_session
    } catch {
        Write-Host "❌ Error checking session: $_" -ForegroundColor Red
        return $false
    }
}

function Start-Login {
    Write-Host "🔓 No session found. Starting X login..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/x-session/login" -UseBasicParsing -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        
        Write-Host "✓ Login initiating..." -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Instructions:" -ForegroundColor Cyan
        foreach ($instruction in $data.instructions) {
            Write-Host "   $instruction" -ForegroundColor Gray
        }
        Write-Host ""
        
        # Open browser
        Start-Process "$API_URL/x-session/login"
        Write-Host "🌐 Browser window should open in a moment..." -ForegroundColor Cyan
        
        return $true
    } catch {
        Write-Host "❌ Error starting login: $_" -ForegroundColor Red
        return $false
    }
}

function Wait-For-Session {
    param(
        [int]$TimeoutSeconds = 300
    )
    
    Write-Host ""
    Write-Host "⏳ Waiting for session... (max $TimeoutSeconds seconds)" -ForegroundColor Cyan
    
    $startTime = Get-Date
    $checkInterval = 5  # Check every 5 seconds
    
    while ($true) {
        $elapsed = (Get-Date) - $startTime
        
        if ($elapsed.TotalSeconds -gt $TimeoutSeconds) {
            Write-Host "⏱️  Timeout: Session not created within $TimeoutSeconds seconds" -ForegroundColor Red
            return $false
        }
        
        if (Check-Session) {
            $seconds = [int]$elapsed.TotalSeconds
            Write-Host "✅ Session created successfully (took $seconds seconds)" -ForegroundColor Green
            return $true
        }
        
        # Show progress every 15 seconds
        if ([int]$elapsed.TotalSeconds % 15 -eq 0) {
            Write-Host "   Still waiting... ($([int]$elapsed.TotalSeconds)s elapsed)" -ForegroundColor Gray
        }
        
        Start-Sleep -Seconds $checkInterval
    }
}

function Trigger-Twitter-Fetch {
    Write-Host ""
    Write-Host "🐦 Triggering Twitter fetch..." -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/trigger-twitter" -UseBasicParsing -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        
        Write-Host "✓ $($data.status)" -ForegroundColor Green
        Write-Host "   Time: $($data.time)" -ForegroundColor Gray
        
        # Wait a bit for fetch to start
        Start-Sleep -Seconds 3
        
        Write-Host ""
        Write-Host "📊 Waiting for fetch to complete..." -ForegroundColor Cyan
        Start-Sleep -Seconds 120  # Wait 2 minutes for fetch
        
        Write-Host "✅ Fetch should be complete!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎉 Dashboard can now display recent April 2026 posts!" -ForegroundColor Green
        
        return $true
    } catch {
        Write-Host "❌ Error triggering fetch: $_" -ForegroundColor Red
        return $false
    }
}

# ============ MAIN FLOW ============

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   X Session Auto-Login & Twitter Fetch" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check session
$hasSession = Check-Session

if ($hasSession) {
    Write-Host "✅ Session already exists! Skipping login." -ForegroundColor Green
} else {
    # Step 2: No session, start login
    $loginStarted = Start-Login
    if (-not $loginStarted) {
        Write-Host ""
        Write-Host "Failed to start login. Please try manually:" -ForegroundColor Red
        Write-Host "  Visit: http://localhost:5050/x-session/login" -ForegroundColor Yellow
        exit 1
    }
    
    # Step 3: Wait for session to be created
    $sessionCreated = Wait-For-Session -TimeoutSeconds $MAX_WAIT
    if (-not $sessionCreated) {
        Write-Host ""
        Write-Host "⚠️  Session was not created in time. Please try again or login manually." -ForegroundColor Yellow
        exit 1
    }
}

# Step 4: Trigger Twitter fetch
$fetchTriggered = Trigger-Twitter-Fetch
if (-not $fetchTriggered) {
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   ✅ Process Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open dashboard: http://localhost:5173" -ForegroundColor Gray
Write-Host "  2. Refresh to see recent April 2026 X posts" -ForegroundColor Gray
Write-Host "  3. Posts will auto-update every 15 minutes" -ForegroundColor Gray
Write-Host ""
