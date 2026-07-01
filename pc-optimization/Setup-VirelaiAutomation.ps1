#Requires -RunAsAdministrator
<#
  Setup-VirelaiAutomation.ps1
  Installs the maintenance automation for VIRELAI as silently-elevated
  scheduled tasks (LogonType S4U + RunLevel Highest = no UAC prompts, ever).

  Deliberately does NOT recreate PCMaint_FlushDNS or the blind 3h
  PCMaint_RestartExplorer — those were removed on purpose (flushing DNS on a
  timer fights your own cache; Explorer only needs restarting when it actually
  bloats). Everything here is need-based, not cargo-cult.

  Tasks installed:
    PCMaint_EnsureRXPlan        at logon      re-activates the RX 9060 XT Ultimate
                                              power plan (guards against Insider
                                              updates silently resetting it)
    PCMaint_RAMMap_EmptyStandby every 1h      RAMMap -Et: empties the standby list
                                              so big model loads have headroom
    PCMaint_ExplorerHealthCheck every 1h      restarts explorer.exe ONLY if its
                                              working set is over the threshold
    PCMaint_LowDiskAlert        every 6h      warns when C: drops below 10% free

  Usage (elevated):
    .\Setup-VirelaiAutomation.ps1                 # install / refresh all tasks
    .\Setup-VirelaiAutomation.ps1 -Remove         # uninstall all PCMaint_ tasks
    .\Setup-VirelaiAutomation.ps1 -WhatIf         # preview, change nothing
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$Remove,
    [string]$RxPlanGuid = "99999999-9999-9999-9999-999999999999",
    [string]$RAMMapPath,
    [int]$ExplorerBloatThresholdMB = 500,
    [int]$LowDiskPercent = 10
)

function Write-Section($t) { Write-Host ""; Write-Host "== $t ==" -ForegroundColor Cyan }

# Indefinite hourly/6-hourly repetition. Use a large finite duration (10 years)
# instead of TimeSpan::MaxValue — MaxValue trips the "incorrectly formatted" XML
# bug on some builds; 10y is effectively forever and always serializes cleanly.
$forever = New-TimeSpan -Days 3650

# --- Uninstall path -------------------------------------------------------
if ($Remove) {
    Write-Section "Removing all PCMaint_* automation"
    Get-ScheduledTask -TaskName 'PCMaint_*' -ErrorAction SilentlyContinue | ForEach-Object {
        if ($PSCmdlet.ShouldProcess($_.TaskName, "Unregister")) {
            Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false
            Write-Host "Removed $($_.TaskName)"
        }
    }
    Write-Host "Done." -ForegroundColor Green
    return
}

# Every task uses this: run as the current user, silently elevated, no UAC.
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

function Register-Maint($name, $action, $trigger, $desc) {
    if ($PSCmdlet.ShouldProcess($name, "Register (S4U, silent-elevated)")) {
        Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger `
            -Principal $principal -Settings $settings -Description $desc -Force | Out-Null
        Write-Host "Installed $name" -ForegroundColor Green
    }
}

# --- 1) Keep the RX power plan active (Insider-reset guard) ----------------
Write-Section "PCMaint_EnsureRXPlan (at logon)"
$a = New-ScheduledTaskAction -Execute "powercfg.exe" -Argument "/setactive $RxPlanGuid"
$t = New-ScheduledTaskTrigger -AtLogOn
Register-Maint "PCMaint_EnsureRXPlan" $a $t "Re-activate RX 9060 XT Ultimate power plan at logon (guards against Insider resets)."

# --- 2) RAMMap empty-standby, hourly ---------------------------------------
Write-Section "PCMaint_RAMMap_EmptyStandby (every 1h)"
if (-not $RAMMapPath) {
    $glob = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\Microsoft.Sysinternals.RAMMap_*\RAMMap64.exe"
    $RAMMapPath = Get-ChildItem $glob -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
    if (-not $RAMMapPath) {
        $RAMMapPath = Get-ChildItem @("C:\", "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Downloads") `
            -Filter RAMMap64.exe -Recurse -Depth 4 -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
    }
}
if ($RAMMapPath -and (Test-Path $RAMMapPath)) {
    Write-Host "Using RAMMap64.exe: $RAMMapPath"
    $a = New-ScheduledTaskAction -Execute $RAMMapPath -Argument "-Et"
    $t = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration $forever
    Register-Maint "PCMaint_RAMMap_EmptyStandby" $a $t "RAMMap -Et: empty standby list hourly (silent S4U)."
} else {
    Write-Host "RAMMap64.exe not found — skipping this task. Install it (winget install Microsoft.Sysinternals.RAMMap) or pass -RAMMapPath, then re-run." -ForegroundColor Yellow
}

# --- 3) Conditional Explorer restart, hourly -------------------------------
Write-Section "PCMaint_ExplorerHealthCheck (every 1h)"
# Inline PS: restart explorer ONLY if its working set exceeds the threshold.
$explorerCmd = @"
`$p = Get-Process explorer -EA SilentlyContinue | Sort-Object WorkingSet64 -Descending | Select-Object -First 1
if (`$p -and (`$p.WorkingSet64/1MB) -gt $ExplorerBloatThresholdMB) { Stop-Process -Name explorer -Force; Start-Sleep 1; if (-not (Get-Process explorer -EA SilentlyContinue)) { Start-Process explorer.exe } }
"@
$enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($explorerCmd))
$a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -EncodedCommand $enc"
$t = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration $forever
Register-Maint "PCMaint_ExplorerHealthCheck" $a $t "Restart explorer.exe only if working set > $ExplorerBloatThresholdMB MB."

# --- 4) Low-disk alert, every 6h -------------------------------------------
Write-Section "PCMaint_LowDiskAlert (every 6h)"
$diskCmd = @"
`$d = Get-PSDrive C; `$pct = `$d.Free/(`$d.Free+`$d.Used)*100
if (`$pct -lt $LowDiskPercent) { msg * ('C: low on space: ' + [math]::Round(`$pct,1) + '% free') }
"@
$enc2 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($diskCmd))
$a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -EncodedCommand $enc2"
$t = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6) -RepetitionDuration $forever
Register-Maint "PCMaint_LowDiskAlert" $a $t "Warn when C: drops below $LowDiskPercent% free."

# --- Summary ---------------------------------------------------------------
Write-Section "Installed automation"
Get-ScheduledTask -TaskName 'PCMaint_*' -ErrorAction SilentlyContinue |
    Select-Object TaskName, State | Format-Table -AutoSize | Out-String | Write-Host
Write-Host "All tasks run silently-elevated (S4U) — no UAC prompts. Remove anytime with -Remove." -ForegroundColor Green
