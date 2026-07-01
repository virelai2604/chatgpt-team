# PC Optimization — VIRELAI (BIFL gold baseline)

Scripts and power-plan baseline for the **VIRELAI** workstation, tuned for
responsiveness on Python/JS dev + local-AI (WSL `knowledge_bifl`) workloads.

Target machine: MSI PRO B660M-B DDR4 · i5-12400F (6C/12T) · 32GB DDR4-3200 ·
AMD RX 9060 XT 8GB · Windows 11 Pro Insider (build 26300). Desktop, always on AC.

## Scripts

| File | Purpose |
|---|---|
| `Optimize-VirelaiPC.ps1` | Main optimizer. Switch-gated, safe-by-default. Power plan (never downgrades a custom/Ultimate plan), disk cleanup (preview + confirm), Defender exclusions for dev + AI-Core, npm/pip cache relocation, dupe/stale-folder reports, SSD-vs-HDD bottleneck check, shadow-copy space report, RAMMap task fix, conditional Explorer restart. Run elevated; add `-WhatIf` to preview. |
| `Restore-RXUltimate.ps1` | Rebuilds the "RX 9060 XT Ultimate" power plan from verified values — recreates it if missing, applies all 34 tuned settings, keeps processor attributes unhidden, activates + backs up. Idempotent. |
| `Setup-VirelaiAutomation.ps1` | Installs the recurring maintenance as silently-elevated (S4U) scheduled tasks — no UAC prompts. Tasks: `PCMaint_EnsureRXPlan` (re-activates the RX plan at logon, guarding against Insider resets), `PCMaint_RAMMap_EmptyStandby` (hourly), `PCMaint_ExplorerHealthCheck` (hourly, restarts Explorer only if bloated), `PCMaint_LowDiskAlert` (6h). Deliberately omits FlushDNS and the blind Explorer-restart timer. `-Remove` uninstalls; `-WhatIf` previews. |
| `Unhide-And-DumpProc.ps1` | One-time helper: unhides all 95 processor power settings, then dumps both the RX plan and stock Ultimate processor subgroups for comparison. |

Usage examples:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\Optimize-VirelaiPC.ps1 -All -WhatIf   # preview everything
.\Optimize-VirelaiPC.ps1 -All           # apply
.\RestoreRXUltimate.ps1                 # restore the tuned power plan
```

## power-baseline/

Snapshot of the active, tuned **RX 9060 XT Ultimate** power plan
(GUID `99999999-9999-9999-9999-999999999999`). Three recovery paths:

| File | Restore path |
|---|---|
| `rx_active.pow` | Instant: `powercfg /import rx_active.pow` then `powercfg /setactive <guid>` |
| `rx_active_full.txt` | Human-readable full plan (all subgroups) — manual reference |
| `rx_active_subprocessor.txt` | Full processor subgroup (all 95 settings, unhidden) |

If the `.pow` and scripts are both lost, `Restore-RXUltimate.ps1` rebuilds the
plan from scratch.

## Why the RX plan beats stock Ultimate Performance

The tune holds max clocks under load while still allowing deep idle when truly
idle (smarter than stock Ultimate, which disables idle):

| Setting | RX 9060 XT Ultimate | Stock Ultimate |
|---|---|---|
| Minimum processor state (AC) | **100%** | 30% |
| Energy Perf Preference (EPP) | **5** | 20 |
| Boost mode | **Aggressive** | Enabled |
| Perf increase threshold | **30%** | 40% |
| Core parking min cores | 4% | 50% |
| Turn off hard disk | **Never** | after 10 min |

Ranking: **RX plan > stock Ultimate > High Performance > Balanced**.
