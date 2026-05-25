<#
    memanto-skills Demo Recording Script for Windows
    =================================================
    
    How to record:
    1. Press Win+G to open Xbox Game Bar
    2. Click the Record button (or press Win+Alt+R to start/stop)
    3. Run this script in PowerShell
    4. Stop recording when done
    
    The demo shows two separate terminal sessions proving
    cross-session memory works.
#>

if (-not $env:MOORCHEH_API_KEY) {
    Write-Host "ERROR: Set MOORCHEH_API_KEY first:" -ForegroundColor Red
    Write-Host "`$env:MOORCHEH_API_KEY=`"your_key_here`"" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      memanto-skills Cross-Session Demo        ║" -ForegroundColor Cyan
Write-Host "║  Step 1: Store an architecture decision       ║" -ForegroundColor Cyan
Write-Host "║  Step 2: Verify it persists in fresh terminal ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "TIME: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor White
Write-Host "SESSION 1: Storing a decision in Memanto" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

Start-Sleep -Seconds 1

Write-Host ">>> memanto-skills status" -ForegroundColor Magenta
memanto-skills status
Write-Host ""
Start-Sleep -Seconds 2

Write-Host ">>> Storing architecture decisions via memanto-skills extract" -ForegroundColor Magenta
Write-Host ""
memanto-skills extract --type transcript "Session: /grill-with-docs
Decisions:
- Chose SWR over React Query for data fetching (lighter, built-in cache invalidation)
Preferences:
- Prefer named exports over default exports
- Use functional components with hooks
Codebase facts:
- API base URL is /api/v1"
Write-Host ""
Start-Sleep -Seconds 2

Write-Host ">>> memanto-skills status (verifying storage)" -ForegroundColor Magenta
memanto-skills status
Write-Host ""
Start-Sleep -Seconds 3

Clear-Host

Write-Host ""
Write-Host "═══ FRESH TERMINAL — new PowerShell window ═══" -ForegroundColor Cyan
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "TIME: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor White
Write-Host "SESSION 2: Context automatically injected" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

Start-Sleep -Seconds 2

Write-Host ">>> memanto-skills inject --task 'Implement data fetching with SWR'" -ForegroundColor Magenta
Write-Host ""
Write-Host "NO MANUAL REPROMPTING NEEDED:" -ForegroundColor Yellow
Write-Host "Agent automatically recalls past decisions from Memanto:" -ForegroundColor Yellow
Write-Host ""
memanto-skills inject --task "Implement data fetching with SWR"
Write-Host ""
Start-Sleep -Seconds 3

memanto-skills status
Write-Host ""

Write-Host ""
Write-Host "✓ Cross-session memory verified!" -ForegroundColor Green
Write-Host "Architecture decision survived across fresh terminal sessions." -ForegroundColor Green
Write-Host ""
Write-Host "#moorcheh-ai" -ForegroundColor Cyan
