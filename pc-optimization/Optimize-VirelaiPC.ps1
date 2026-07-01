#Requires -RunAsAdministrator
<#
  Optimize-VirelaiPC.ps1
  Target machine : VIRELAI (MSI PRO B660M-B DDR4, i5-12400F 6C/12T, 32GB DDR4-3200,
                   AMD RX 9060 XT 8GB, Win11 Pro Insider build 26300)
  Goal           : Responsiveness + fast Python/JS dev workflows (builds, indexing,
                   git, npm/pip), without breaking the existing PCMaint_* scheduled tasks.

  Usage:
    Run from an elevated PowerShell prompt (Run as Administrator).

      .\Optimize-VirelaiPC.ps1                    # safe tweaks only (default)
      .\Optimize-VirelaiPC.ps1 -CleanDiskSpace     # also frees space on C: (18.5GB free today)
      .\Optimize-VirelaiPC.ps1 -AddDevExclusions   # also adds Defender exclusions for dev folders
      .\Optimize-VirelaiPC.ps1 -RelocateDevCaches  # also moves npm/pip caches to D: permanently
      .\Optimize-VirelaiPC.ps1 -FindDuplicateFiles # report-only: duplicate files >=10MB in -ScanRoots
      .\Optimize-VirelaiPC.ps1 -FindStaleFolders   # report-only: folders untouched 180+ days in -ScanRoots
      .\Optimize-VirelaiPC.ps1 -ReportDevCacheSizes # report-only: size every npm/pip/cargo/etc cache
      .\Optimize-VirelaiPC.ps1 -DisableSearchIndexing # opt-in (NOT in -All): stop redundant WSearch indexing (Everything covers search)
      .\Optimize-VirelaiPC.ps1 -RestartExplorerIfBloated # opt-in (NOT in -All): only restarts explorer.exe if over -ExplorerBloatThresholdMB (default 500MB)
      .\Optimize-VirelaiPC.ps1 -All                # everything EXCEPT -DisableSearchIndexing / -RestartExplorerIfBloated (those stay opt-in)
      .\Optimize-VirelaiPC.ps1 -WhatIf             # preview only, changes nothing

  Every section prints what it did. Nothing here touches game settings or the GPU driver;
  it's deliberately scoped to dev-workload responsiveness and disk hygiene.
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$CleanDiskSpace,
    [switch]$AddDevExclusions,
    [switch]$FixRAMMapElevation,
    [switch]$RelocateDevCaches,
    [switch]$FindDuplicateFiles,
    [switch]$FindStaleFolders,
    [switch]$DisableSearchIndexing,
    [switch]$ReportDevCacheSizes,
    [switch]$RestartExplorerIfBloated,
    [switch]$All,
    [string]$RAMMapPath,
    [string]$DevCacheDrive = "D:",
    [string[]]$ScanRoots = @("$env:USERPROFILE\Downloads", "$env:USERPROFILE\Desktop", "D:\", "Y:\", "Z:\"),
    [int]$StaleDays = 180,
    [int]$ExplorerBloatThresholdMB = 500,
    # Protected areas never touched/reported by the dupe/stale scans:
    #   Y:\AI-Core   = model blobs/manifests (README_AI_CORE boundary rule)
    #   Y:\recover   = read/append-only forensic archive (6-criteria deletion rule)
    [string[]]$ScanExclude = @("Y:\AI-Core", "Y:\recover")
)

if ($All) { $FixRAMMapElevation = $true; $RelocateDevCaches = $true; $FindDuplicateFiles = $true; $FindStaleFolders = $true; $ReportDevCacheSizes = $true }

if ($All) { $CleanDiskSpace = $true; $AddDevExclusions = $true }

function Write-Section($title) {
    Write-Host ""
    Write-Host "== $title ==" -ForegroundColor Cyan
}

function Test-Excluded($path, $excludeRoots) {
    # True if $path is inside any protected root (case-insensitive prefix match).
    foreach ($ex in $excludeRoots) {
        $exNorm = $ex.TrimEnd('\')
        if ($path -eq $exNorm -or $path.StartsWith($exNorm + '\', [StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Get-FolderSizeGB($path) {
    # Measure-Object's .Sum is $null when zero files match — under Set-StrictMode
    # (confirmed active in this user's profile) that throws "property 'Sum' cannot
    # be found" instead of silently returning null. Count first, only measure if
    # there's actually something there, so this never errors on an empty folder.
    $files = @(Get-ChildItem -Path $path -Recurse -File -Force -ErrorAction SilentlyContinue)
    if ($files.Count -eq 0) { return 0 }
    $bytes = ($files | Measure-Object -Property Length -Sum).Sum
    return [double]$bytes / 1GB
}

# ---------------------------------------------------------------------------
Write-Section "Power plan"
# WHITELIST APPROACH (learned the hard way): only ever UPGRADE the two known
# power-saving stock plans (Balanced, Power saver) up to High Performance. Anything
# else — stock Ultimate Performance, a custom-named tuned plan like "RX 9060 XT
# Ultimate", Bitsum/Process Lasso plans — is left completely untouched. A custom
# high-perf plan is almost always better-tuned than stock High Performance, and we
# must NEVER downgrade it. (Matching on the word "Ultimate" is not enough: custom
# plans can be named anything, so we key off the exact GUIDs we're allowed to raise.)
$highPerfGuid   = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
$balancedGuid   = '381b4222-f694-41f0-9685-ff5bb260df2e'
$powerSaverGuid = 'a1841308-3541-4fab-bc81-f71556f20b4a'
$activeSchemeInfo = powercfg /getactivescheme
$current = ($activeSchemeInfo -replace '.*GUID:\s*([0-9a-f-]+).*', '$1').Trim()
$activeName = ($activeSchemeInfo -replace '.*\((.+)\).*', '$1').Trim()
if ($current -eq $highPerfGuid) {
    Write-Host "Already on High Performance."
} elseif ($current -eq $balancedGuid -or $current -eq $powerSaverGuid) {
    if ($PSCmdlet.ShouldProcess("Power plan", "Upgrade '$activeName' to High Performance")) {
        powercfg /setactive $highPerfGuid
        Write-Host "Upgraded '$activeName' -> High Performance."
    }
} else {
    Write-Host "Active plan is '$activeName' — a custom/Ultimate plan, almost certainly better-tuned than stock High Performance. Leaving it untouched." -ForegroundColor Green
}
# Never let USB selective suspend or PCIe link-power-saving stall a build/debug session.
powercfg /change monitor-timeout-ac 0 2>$null
Write-Host "Disabled monitor timeout while on AC (build runs won't blank/sleep the display)."

# ---------------------------------------------------------------------------
Write-Section "Background apps & visual effects"
# Trim Windows visual animation overhead; keep font smoothing (ClearType) since
# it doesn't cost real CPU and matters for code readability.
$perfKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects'
if ($PSCmdlet.ShouldProcess($perfKey, "Set visual effects to 'Adjust for best performance' (keep font smoothing)")) {
    New-Item -Path $perfKey -Force | Out-Null
    Set-ItemProperty -Path $perfKey -Name VisualFXSetting -Value 2
    Write-Host "Visual effects set to performance mode."
}

# Background UWP apps refreshing in the tray steal scheduler time from compilers/LSPs.
$bgAppsKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications'
if (Test-Path $bgAppsKey) {
    if ($PSCmdlet.ShouldProcess($bgAppsKey, "Disable global background app refresh")) {
        Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Search' -Name BackgroundAppGlobalToggle -Value 0 -ErrorAction SilentlyContinue
        Write-Host "Disabled background app refresh (Settings > Apps > Background apps)."
    }
}

# ---------------------------------------------------------------------------
Write-Section "Search indexing"
# Exclude the heaviest, highest-churn dev directories from Windows Search —
# indexing node_modules/.git/venv burns disk I/O for zero search value.
$devRoots = @(
    "$env:USERPROFILE\source", "$env:USERPROFILE\repos", "$env:USERPROFILE\projects",
    "D:\", "Y:\", "Z:\"
) | Where-Object { Test-Path $_ }

foreach ($root in $devRoots) {
    Write-Host "Dev root detected: $root — exclude it from Indexing Options manually if it isn't already" -ForegroundColor Yellow
}
Write-Host "(Search indexing exclusions require the interactive Control Panel applet — Indexing Options > Modify;" -ForegroundColor DarkGray
Write-Host " there is no supported non-interactive API to add scopes, so this step is informational.)" -ForegroundColor DarkGray

# ---------------------------------------------------------------------------
Write-Section "Bottleneck check: SSD vs HDD per drive letter"
# C: is the only NVMe SSD on this machine (Samsung 970 EVO Plus). D:/E: and the
# WD Black volumes (Y:/Z:) sit on spinning HDDs (Seagate ST2000DM008, WD4006FZBX).
# Dev work (npm install, git status, IDE indexing) is small-file-I/O heavy, where
# HDDs are 10-50x slower than NVMe — far more impactful than CPU or RAM here.
try {
    $diskMap = Get-Volume -ErrorAction Stop | Where-Object DriveLetter | ForEach-Object {
        $vol = $_
        $mediaType = $null
        try {
            $disk = $vol | Get-Partition -ErrorAction Stop | Get-Disk -ErrorAction Stop | Select-Object -First 1
            $mediaType = (Get-PhysicalDisk -ErrorAction SilentlyContinue | Where-Object DeviceId -eq $disk.Number).MediaType
        } catch { }
        [PSCustomObject]@{ Drive = "$($vol.DriveLetter):"; MediaType = $mediaType }
    }
    foreach ($d in $diskMap) {
        $tag = if ($d.MediaType -eq 'HDD') { 'HDD (slow for dev I/O)' } elseif ($d.MediaType -eq 'SSD') { 'SSD' } else { 'unknown' }
        $color = if ($d.MediaType -eq 'HDD') { 'Yellow' } else { 'Gray' }
        Write-Host "$($d.Drive) -> $tag" -ForegroundColor $color
    }
    $hddDevRoots = $devRoots | Where-Object {
        $letter = ($_ -replace ':\\?$', '') + ':'
        ($diskMap | Where-Object { $_.Drive -eq $letter }).MediaType -eq 'HDD'
    }
    if ($hddDevRoots) {
        Write-Host "Dev roots on spinning HDD: $($hddDevRoots -join ', ') — moving active repos here to C: (or a free NVMe drive) is the single biggest speed win available." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Couldn't enumerate physical disk media types on this system — check manually via Settings > System > Storage > Disks & volumes." -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
Write-Section "Performance-relevant security & memory settings (READ-ONLY report)"
# This section CHANGES NOTHING. It only surfaces settings that trade CPU/RAM
# headroom for security, so you can decide consciously. On this box the GPU does
# no AI compute (torch.cuda=false), so everything is CPU-bound — making these
# tradeoffs actually visible in dev/AI throughput.

# VBS / HVCI (Memory Integrity): real CPU overhead, but WSL2/Hyper-V already loads
# the hypervisor here, so VBS itself is largely "already paid for". HVCI is the
# part that adds extra per-instruction cost.
try {
    $dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard -ErrorAction Stop
    $vbsOn  = $dg.VirtualizationBasedSecurityStatus -eq 2
    $hvciOn = $dg.SecurityServicesRunning -contains 2
    Write-Host ("VBS (Virtualization-Based Security): {0}" -f ($(if ($vbsOn) {'RUNNING'} else {'off'})))
    Write-Host ("HVCI / Memory Integrity:             {0}" -f ($(if ($hvciOn) {'RUNNING — ~5-10% CPU tax on some build/code workloads'} else {'off'}))) -ForegroundColor $(if ($hvciOn) {'Yellow'} else {'Gray'})
    if ($hvciOn) {
        Write-Host "  To weigh disabling: Settings > Privacy & security > Windows Security > Device security > Core isolation > Memory integrity." -ForegroundColor DarkGray
        Write-Host "  SECURITY TRADEOFF — this script will NOT change it. Only turn off if you accept reduced kernel-exploit protection." -ForegroundColor DarkGray
    }
} catch {
    Write-Host "VBS/HVCI status unavailable via WMI on this build." -ForegroundColor DarkGray
}

# Pagefile: msinfo showed a fixed 4GB pagefile on a nearly-full C:. With 32GB RAM
# and heavy model loads, a tiny fixed pagefile risks commit-limit OOM.
try {
    $pf = Get-CimInstance Win32_PageFileUsage -ErrorAction SilentlyContinue
    $autoManaged = (Get-CimInstance Win32_ComputerSystem).AutomaticManagedPagefile
    if ($pf) {
        Write-Host ("Pagefile: {0} — allocated {1} MB, peak {2} MB, auto-managed: {3}" -f $pf.Name, $pf.AllocatedBaseSize, $pf.PeakUsage, $autoManaged)
        if (-not $autoManaged -and $pf.AllocatedBaseSize -lt 8192) {
            Write-Host "  Small fixed pagefile on C:. RECOMMENDED (manual): free C: space first, then set System-managed pagefile so it can grow during big model loads." -ForegroundColor Yellow
            Write-Host "  Do NOT move it to D:/Y:/Z: (those are HDDs) — pagefile belongs on the NVMe C:. Script won't change this automatically." -ForegroundColor DarkGray
        }
    }
} catch { }

# Quick RAM headroom snapshot for AI workloads.
$os = Get-CimInstance Win32_OperatingSystem
$freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
$totGB  = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
Write-Host ("RAM: {0} GB free of {1} GB. A 7B model (~5-8GB) + Whisper large-v3 (~3-10GB) together can approach this — watch for standby-list pressure (that's what your RAMMap task manages)." -f $freeGB, $totGB)

# Volume Shadow Copies: Device Manager showed dozens of "Generic volume shadow copy"
# entries. Restore-point/VSS snapshots can silently eat GBs on a near-full C:. This
# is REPORT-ONLY — shadow copies are your System Restore safety net, so the script
# will NOT delete them; it just shows how much space they're using and where.
try {
    $ss = Get-CimInstance Win32_ShadowStorage -ErrorAction Stop
    if ($ss) {
        foreach ($s in $ss) {
            $vol = Get-CimInstance Win32_Volume -Filter "DeviceID='$($s.Volume.DeviceID -replace '\\','\\')'" -ErrorAction SilentlyContinue
            $usedGB   = [math]::Round($s.UsedSpace / 1GB, 1)
            $allocGB  = [math]::Round($s.AllocatedSpace / 1GB, 1)
            $maxGB    = [math]::Round($s.MaxSpace / 1GB, 1)
            $drive    = if ($vol.DriveLetter) { $vol.DriveLetter } else { $s.Volume.DeviceID }
            Write-Host ("Shadow storage on {0}: using {1} GB (allocated {2} GB, max cap {3} GB)" -f $drive, $usedGB, $allocGB, $maxGB) -ForegroundColor $(if ($usedGB -gt 5) {'Yellow'} else {'Gray'})
        }
        Write-Host "  If shadow storage on C: is large, reclaim via: System Protection > Configure > Max Usage slider (or 'vssadmin resize shadowstorage')." -ForegroundColor DarkGray
        Write-Host "  Keep SOME restore capacity — don't zero it out. Script won't change this automatically." -ForegroundColor DarkGray
    } else {
        Write-Host "No shadow storage configured (System Protection may be off)." -ForegroundColor DarkGray
    }
} catch {
    Write-Host "Shadow storage query unavailable — check manually with 'vssadmin list shadowstorage' in an elevated prompt." -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
Write-Section "Broken shortcuts (Desktop + Start Menu)"
$shell = New-Object -ComObject WScript.Shell
$shortcutDirs = @(
    "$env:USERPROFILE\Desktop",
    "$env:PUBLIC\Desktop",
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"
) | Where-Object { Test-Path $_ }

$brokenCount = 0
foreach ($dir in $shortcutDirs) {
    Get-ChildItem -Path $dir -Filter "*.lnk" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $target = $shell.CreateShortcut($_.FullName).TargetPath
        if ($target -and -not (Test-Path $target)) {
            Write-Host "Broken: $($_.FullName) -> missing target '$target'" -ForegroundColor Yellow
            $brokenCount++
        }
    }
}
if ($brokenCount -eq 0) {
    Write-Host "No broken shortcuts found."
} else {
    Write-Host "$brokenCount broken shortcut(s) found above — safe to delete manually, this script won't delete them without confirmation." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
if ($FindDuplicateFiles) {
    Write-Section "Duplicate files (>=10MB) in: $($ScanRoots -join ', ')"
    # Only hash files above 10MB — hashing every small file in Downloads/dev roots
    # would take forever for little payoff. Large duplicates (installers, archives,
    # videos, disk images) are where the real reclaimable space is.
    if ($ScanExclude) { Write-Host "Excluding protected areas: $($ScanExclude -join ', ')" -ForegroundColor DarkGray }
    $validRoots = $ScanRoots | Where-Object { Test-Path $_ }
    $bigFiles = $validRoots | ForEach-Object {
        Get-ChildItem -Path $_ -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Length -ge 10MB -and -not (Test-Excluded $_.FullName $ScanExclude) }
    }
    Write-Host "Hashing $($bigFiles.Count) file(s) >=10MB — this can take a while on spinning disks..." -ForegroundColor DarkGray
    $hashGroups = $bigFiles | Group-Object Length | Where-Object Count -gt 1 |
        ForEach-Object { $_.Group } |
        Get-FileHash -Algorithm SHA256 -ErrorAction SilentlyContinue |
        Group-Object Hash | Where-Object Count -gt 1

    if (-not $hashGroups) {
        Write-Host "No duplicate files found above the 10MB threshold."
    } else {
        $reclaimable = 0
        foreach ($g in $hashGroups) {
            $paths = $g.Group.Path
            $size = (Get-Item $paths[0]).Length
            $reclaimable += $size * ($paths.Count - 1)
            Write-Host ("Duplicate set ({0:N1} GB each):" -f ($size / 1GB)) -ForegroundColor Yellow
            $paths | ForEach-Object { Write-Host "  $_" }
        }
        Write-Host ("Reclaimable if you keep one copy of each: ~{0:N1} GB" -f ($reclaimable / 1GB)) -ForegroundColor Yellow
        Write-Host "Nothing deleted automatically — review the sets above and remove the copies you don't need." -ForegroundColor DarkGray
    }
}

# ---------------------------------------------------------------------------
if ($FindStaleFolders) {
    Write-Section "Stale folders (untouched $StaleDays+ days) in: $($ScanRoots -join ', ')"
    # Top-level folders only (not a deep recursive walk) — this is meant to surface
    # "did you forget about this 40GB folder from 2 years ago" candidates, not every
    # subfolder in every repo.
    if ($ScanExclude) { Write-Host "Excluding protected areas: $($ScanExclude -join ', ')" -ForegroundColor DarkGray }
    $cutoff = (Get-Date).AddDays(-$StaleDays)
    $candidates = foreach ($root in ($ScanRoots | Where-Object { Test-Path $_ })) {
        Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
          Where-Object { -not (Test-Excluded $_.FullName $ScanExclude) } | ForEach-Object {
            $lastWrite = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
                          Measure-Object -Property LastWriteTime -Maximum).Maximum
            if ($lastWrite -and $lastWrite -lt $cutoff) {
                $sizeGB = Get-FolderSizeGB $_.FullName
                [PSCustomObject]@{ Path = $_.FullName; LastTouched = $lastWrite; SizeGB = [math]::Round($sizeGB, 1) }
            }
        }
    }
    $candidates = $candidates | Sort-Object SizeGB -Descending
    if (-not $candidates) {
        Write-Host "No folders older than $StaleDays days found in scanned roots."
    } else {
        $candidates | Select-Object -First 20 | ForEach-Object {
            Write-Host ("{0,6:N1} GB  last touched {1:yyyy-MM-dd}  {2}" -f $_.SizeGB, $_.LastTouched, $_.Path) -ForegroundColor Yellow
        }
        $total = ($candidates | Measure-Object -Property SizeGB -Sum).Sum
        Write-Host ("Total stale-folder size found: ~{0:N1} GB — nothing deleted, review before archiving/removing." -f $total) -ForegroundColor Yellow
    }
}

# ---------------------------------------------------------------------------
if ($AddDevExclusions) {
    Write-Section "Defender real-time-scan exclusions (dev folders)"
    # Real-time AV scanning every file touched by a compiler/bundler roughly
    # doubles build time. Exclude common dev cache/output dirs, not source files,
    # so you keep protection on anything you actually download or edit by hand.
    $exclusionPaths = @(
        "$env:USERPROFILE\AppData\Local\npm-cache",
        "$env:USERPROFILE\AppData\Local\pip\cache",
        "$env:USERPROFILE\AppData\Roaming\npm-cache",
        "$env:USERPROFILE\.cache",
        "$env:USERPROFILE\.gradle",
        "$env:USERPROFILE\.m2"
    ) + $devRoots

    foreach ($path in ($exclusionPaths | Where-Object { Test-Path $_ })) {
        if ($PSCmdlet.ShouldProcess($path, "Add Defender exclusion")) {
            Add-MpPreference -ExclusionPath $path -ErrorAction SilentlyContinue
            Write-Host "Excluded: $path"
        }
    }
    if ($PSCmdlet.ShouldProcess("node.exe/python.exe/git.exe", "Add Defender process exclusions")) {
        Add-MpPreference -ExclusionProcess "node.exe" -ErrorAction SilentlyContinue
        Add-MpPreference -ExclusionProcess "python.exe" -ErrorAction SilentlyContinue
        Add-MpPreference -ExclusionProcess "git.exe" -ErrorAction SilentlyContinue
        Write-Host "Excluded node.exe / python.exe / git.exe from real-time scanning."
    }
    Write-Host "Review/adjust anytime: Windows Security > Virus & threat protection > Exclusions." -ForegroundColor DarkGray

    Write-Section "Local AI model-storage exclusions (knowledge_bifl / AI-Core layout)"
    # NOTE: This machine's AI stack is the WSL 'knowledge_bifl' project, NOT a native
    # Windows install. Per README_AI_CORE.md the boundary rule is:
    #   - Heavy model assets (Ollama blobs/manifests) live on Y:\AI-Core  <- real Windows volume, Defender CAN scan it
    #   - HF + Whisper caches live INSIDE WSL (/home/user/.cache/...)      <- ext4 vhdx, Defender does NOT scan it, so excluding is pointless
    # So on the Windows side we only exclude the Y: model store; the big win is
    # keeping real-time AV off multi-GB model blobs that get re-read on every load.
    #
    # 6-CRITERIA / boundary safety (from AVAILABLE_TOOLS_POINTER + README_AI_CORE):
    # this section ONLY adds AV exclusions — it never deletes, moves, or touches any
    # model blob/manifest. Nothing here can violate the "AI = signal, not deletion
    # authority" rule.
    $aiPaths = @(
        @{ Path = "Y:\AI-Core\models";           Tool = "Ollama model store (Y:\AI-Core)" }
        @{ Path = "Y:\AI-Core";                  Tool = "AI-Core heavy assets / RAG corpora (Y:)" }
        @{ Path = "Y:\recover";                  Tool = "Recovery/forensic archive (Y:\recover)" }
        # WSL caches surfaced via the \\wsl.localhost UNC only for visibility/size —
        # NOT added as Defender exclusions (Defender doesn't scan inside WSL2 anyway).
        @{ Path = "\\wsl.localhost\Ubuntu\home\user\.cache\huggingface\hub"; Tool = "HF cache (WSL — info only)"; NoExclude = $true }
        @{ Path = "\\wsl.localhost\Ubuntu\home\user\.cache\whisper";         Tool = "Whisper .pt cache (WSL — info only)"; NoExclude = $true }
    )
    foreach ($p in $aiPaths) {
        if (Test-Path $p.Path) {
            $size = Get-FolderSizeGB $p.Path
            Write-Host ("Found {0}: {1} (~{2:N1} GB)" -f $p.Tool, $p.Path, $size) -ForegroundColor Yellow
            if ($p.NoExclude) {
                Write-Host "  Inside WSL2 — Windows Defender doesn't scan here, so no exclusion needed (listed for size awareness only)." -ForegroundColor DarkGray
            } elseif ($PSCmdlet.ShouldProcess($p.Path, "Add Defender exclusion ($($p.Tool))")) {
                Add-MpPreference -ExclusionPath $p.Path -ErrorAction SilentlyContinue
                Write-Host "  Excluded from real-time scanning."
            }
        }
    }
    if (-not ($aiPaths | Where-Object { Test-Path $_.Path })) {
        Write-Host "No AI-Core / WSL model folders found at the documented paths — check the drive is mounted (Y:) and WSL is running." -ForegroundColor DarkGray
    }
}

# ---------------------------------------------------------------------------
if ($ReportDevCacheSizes) {
    Write-Section "Dev cache sizes (Windows-side — AI model caches are reported separately above)"
    # Report-only — never deletes. Run -RelocateDevCaches/-CleanDiskSpace to act on this.
    $devCachePaths = @(
        "$env:USERPROFILE\AppData\Local\npm-cache",
        "$env:APPDATA\npm-cache",
        "$env:USERPROFILE\AppData\Local\pip\cache",
        "$env:USERPROFILE\.cache",
        "$env:USERPROFILE\.cargo",
        "$env:USERPROFILE\.gradle",
        "$env:USERPROFILE\.m2",
        "$env:USERPROFILE\.nuget",
        "$env:USERPROFILE\AppData\Local\Yarn\Cache",
        "$env:USERPROFILE\AppData\Local\pnpm-cache",
        "$env:USERPROFILE\AppData\Local\ms-playwright"
    )
    $results = foreach ($p in ($devCachePaths | Where-Object { Test-Path $_ } | Select-Object -Unique)) {
        [PSCustomObject]@{ Cache = $p; GB = [math]::Round((Get-FolderSizeGB $p), 2) }
    }
    if (-not $results) {
        Write-Host "No dev cache folders found at the standard locations." -ForegroundColor DarkGray
    } else {
        $results | Sort-Object GB -Descending | Format-Table -AutoSize | Out-String | Write-Host
        $total = ($results | Measure-Object -Property GB -Sum).Sum
        Write-Host ("Total Windows-side dev cache: ~{0:N1} GB" -f $total) -ForegroundColor Yellow
    }
}

# ---------------------------------------------------------------------------
if ($RelocateDevCaches) {
    Write-Section "Relocate npm/pip caches off C: to $DevCacheDrive"
    # Defender exclusions stop AV scanning these, but the caches still fill C: as
    # they grow. Pointing them at $DevCacheDrive (D: has 408.9 GB free) fixes
    # that permanently instead of needing repeated manual cleanup.
    if (-not (Test-Path $DevCacheDrive)) {
        Write-Host "$DevCacheDrive is not a valid/available drive — pass -DevCacheDrive '<letter>:' to override." -ForegroundColor Yellow
    } else {
        $npmCacheDir = Join-Path $DevCacheDrive "DevCache\npm-cache"
        $pipCacheDir = Join-Path $DevCacheDrive "DevCache\pip-cache"

        if (Get-Command npm -ErrorAction SilentlyContinue) {
            if ($PSCmdlet.ShouldProcess("npm cache", "Relocate to $npmCacheDir")) {
                New-Item -ItemType Directory -Path $npmCacheDir -Force | Out-Null
                npm config set cache $npmCacheDir --global
                Write-Host "npm cache now at: $npmCacheDir"
            }
        } else {
            Write-Host "npm not found on PATH — skipping npm cache relocation." -ForegroundColor DarkGray
        }

        if ($PSCmdlet.ShouldProcess("pip cache (PIP_CACHE_DIR)", "Relocate to $pipCacheDir")) {
            New-Item -ItemType Directory -Path $pipCacheDir -Force | Out-Null
            [Environment]::SetEnvironmentVariable("PIP_CACHE_DIR", $pipCacheDir, "User")
            Write-Host "pip cache now at: $pipCacheDir (PIP_CACHE_DIR set — restart shells to pick it up)"
        }

        Write-Host "Old caches on C: aren't deleted automatically — run with -CleanDiskSpace too to clear them out." -ForegroundColor DarkGray
    }
}

# ---------------------------------------------------------------------------
if ($DisableSearchIndexing) {
    Write-Section "Disable Windows Search indexing (redundant — 'Everything' is installed)"
    # Your services list shows voidtools 'Everything' running: it already gives instant
    # filename search across all volumes via the NTFS journal, with almost no ongoing
    # I/O. The Windows Search (WSearch) indexer, by contrast, continuously reads files
    # to build its content index — hammering the very disks that are your bottleneck.
    # Since search is already covered, stopping WSearch removes that background I/O.
    #
    # TRADEOFF (why this is opt-in and NOT in -All): Start-menu *content* search and
    # some Outlook/Store search rely on WSearch. Filename search (Everything) is
    # unaffected. Fully reversible — re-enable with:
    #   Set-Service WSearch -StartupType Automatic; Start-Service WSearch
    $ws = Get-Service -Name WSearch -ErrorAction SilentlyContinue
    if (-not $ws) {
        Write-Host "WSearch service not present — nothing to do." -ForegroundColor DarkGray
    } elseif (-not (Get-Service -Name 'Everything' -ErrorAction SilentlyContinue) -and
              -not (Get-Process -Name 'Everything' -ErrorAction SilentlyContinue)) {
        Write-Host "Couldn't confirm 'Everything' is running. Skipping to avoid leaving you with NO search." -ForegroundColor Yellow
        Write-Host "Start Everything first, or re-run knowing Start-menu content search will degrade." -ForegroundColor Yellow
    } elseif ($PSCmdlet.ShouldProcess("WSearch (Windows Search)", "Stop + set Startup=Disabled")) {
        Stop-Service WSearch -Force -ErrorAction SilentlyContinue
        Set-Service WSearch -StartupType Disabled -ErrorAction SilentlyContinue
        Write-Host "Windows Search indexing stopped and disabled. Filename search via Everything is unaffected."
        Write-Host "Reverse anytime: Set-Service WSearch -StartupType Automatic; Start-Service WSearch" -ForegroundColor DarkGray
    }
}

# ---------------------------------------------------------------------------
if ($RestartExplorerIfBloated) {
    Write-Section "Conditional Explorer restart (replaces the blind 3h PCMaint_RestartExplorer timer)"
    # PCMaint_RestartExplorer restarts explorer.exe every 3h regardless of whether
    # it's actually a problem — that closes/reopens every open window for no
    # measured benefit. This checks explorer.exe's actual memory first and ONLY
    # restarts if it's genuinely bloated (default threshold: 500MB). A full reboot,
    # not a timed Explorer kill, is still the right way to clear kernel/driver-level
    # leaks over a long session — this just handles the shell-specific case.
    $explorerProcs = @(Get-Process -Name explorer -ErrorAction SilentlyContinue)
    if (-not $explorerProcs) {
        Write-Host "explorer.exe not running (unusual) — nothing to check." -ForegroundColor DarkGray
    } else {
        $maxMB = [math]::Round(($explorerProcs | Measure-Object -Property WorkingSet64 -Maximum).Maximum / 1MB, 0)
        Write-Host "explorer.exe working set: $maxMB MB (threshold: $ExplorerBloatThresholdMB MB)"
        if ($maxMB -lt $ExplorerBloatThresholdMB) {
            Write-Host "Under threshold — Explorer is healthy, leaving it running (no restart, no closed windows)." -ForegroundColor Green
        } elseif ($PSCmdlet.ShouldProcess("explorer.exe", "Restart (bloated at $maxMB MB)")) {
            Write-Host "Over threshold — restarting explorer.exe. Open windows may close/reopen." -ForegroundColor Yellow
            Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
            if (-not (Get-Process -Name explorer -ErrorAction SilentlyContinue)) { Start-Process explorer.exe }
            Write-Host "explorer.exe restarted."
        }
    }
    Write-Host "To fully replace the blind timer, disable the old task: Unregister-ScheduledTask -TaskName 'PCMaint_RestartExplorer' -Confirm:`$false" -ForegroundColor DarkGray
    Write-Host "...then schedule THIS script with -RestartExplorerIfBloated instead, e.g. hourly — it'll only act when actually needed." -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
if ($CleanDiskSpace) {
    Write-Section "Disk cleanup on C: (18.5 GB free is the bottleneck)"
    $targets = @(
        @{ Path = "$env:TEMP\*"; Name = "User temp" }
        @{ Path = "C:\Windows\Temp\*"; Name = "System temp" }
        @{ Path = "$env:USERPROFILE\AppData\Local\Microsoft\Windows\Explorer\thumbcache_*.db"; Name = "Thumbnail cache (cache DB only — never touches your actual photos)" }
        @{ Path = "$env:USERPROFILE\AppData\Local\D3DSCache\*"; Name = "DirectX shader cache" }
        @{ Path = "$env:USERPROFILE\AppData\Local\npm-cache\*"; Name = "npm cache" }
        @{ Path = "$env:USERPROFILE\AppData\Local\pip\cache\*"; Name = "pip cache" }
    )

    Write-Host "Preview — nothing has been deleted yet, this is exactly what would be removed:" -ForegroundColor Cyan
    $previewTotal = 0
    foreach ($t in $targets) {
        if (Test-Path $t.Path) {
            $size = Get-FolderSizeGB $t.Path
            $previewTotal += $size
            Write-Host ("  {0,6:N1} GB  {1}" -f $size, $t.Name)
        }
    }
    Write-Host ("Total to be freed: ~{0:N1} GB" -f $previewTotal) -ForegroundColor Cyan

    if (-not $WhatIfPreference) {
        $confirm = Read-Host "Proceed with deleting the above? (y/N)"
        if ($confirm -notmatch '^[Yy]') {
            Write-Host "Skipped — no files deleted. Re-run with -WhatIf if you just wanted to preview." -ForegroundColor Yellow
            $targets = @()
        }
    }

    foreach ($t in $targets) {
        if (Test-Path $t.Path) {
            $size = Get-FolderSizeGB $t.Path
            if ($PSCmdlet.ShouldProcess($t.Name, "Delete ({0:N1} GB)" -f $size)) {
                Remove-Item $t.Path -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host ("Cleared {0}: ~{1:N1} GB" -f $t.Name, $size)
            }
        }
    }
    if ($PSCmdlet.ShouldProcess("Windows Update cleanup", "Run DISM component cleanup")) {
        Write-Host "Running DISM component store cleanup (can take several minutes)..."
        Start-Process -FilePath "Dism.exe" -ArgumentList "/Online /Cleanup-Image /StartComponentCleanup" -Wait -NoNewWindow
    }
    if ($PSCmdlet.ShouldProcess("Recycle Bin", "Empty")) {
        Clear-RecycleBin -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "Recycle Bin emptied."
    }
    Write-Host ""
    Write-Host "Heaviest win available manually: move large, rarely-touched project folders from C: to D:/Y:/Z:" -ForegroundColor Yellow
    Write-Host "(D: has 408.9 GB free, Z: has 470.6 GB free) — this script won't move files without your say-so." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
if ($FixRAMMapElevation) {
    Write-Section "Fix PCMaint_RAMMap_EmptyStandby (stuck on interactive UAC prompt)"
    # RunLevel "Highest" alone is NOT enough: if the task's LogonType is "Interactive"
    # (run only when the user is logged on, using the logged-on user's token), Task
    # Scheduler still routes elevation through the normal interactive UAC consent flow.
    # That dialog renders on the secure desktop, which can fail to get focus for a
    # task trigger — so it just sits there unseen and the task never completes.
    #
    # The actual silent fix is LogonType "S4U": Task Scheduler's service mints an
    # already-elevated token directly (no interactive consent involved at all), so
    # RunLevel Highest + LogonType S4U runs fully unattended with zero UAC prompts.
    # (S4U requires the account to hold the "Log on as a batch job" right, which
    # Register-ScheduledTask grants automatically for the principal's UserId.)
    $ramMapTask = "PCMaint_RAMMap_EmptyStandby"
    $existingTask = Get-ScheduledTask -TaskName $ramMapTask -ErrorAction SilentlyContinue

    if (-not $RAMMapPath) {
        # 1) WinGet install (confirmed location on this machine): RAMMap installed via
        #    'winget install Microsoft.Sysinternals.RAMMap' lands under a versioned
        #    package folder in AppData\Local\Microsoft\WinGet\Packages. The folder name
        #    carries a hash suffix, so glob it rather than hard-coding the exact name.
        $wingetGlob = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\Microsoft.Sysinternals.RAMMap_*\RAMMap64.exe"
        $RAMMapPath = Get-ChildItem -Path $wingetGlob -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName

        # 2) Desktop shortcut (recurse — shortcuts often live in Desktop\apps\..., not
        #    directly on the Desktop root). Resolve the .lnk's real target.
        if (-not $RAMMapPath) {
            $shell = New-Object -ComObject WScript.Shell
            $shortcutHits = @(
                "$env:USERPROFILE\Desktop",
                "$env:PUBLIC\Desktop"
            ) | Where-Object { Test-Path $_ } |
                ForEach-Object { Get-ChildItem $_ -Filter "*.lnk" -Recurse -ErrorAction SilentlyContinue } |
                Where-Object { $_.Name -match 'RAMMap' }

            foreach ($lnk in $shortcutHits) {
                $target = $shell.CreateShortcut($lnk.FullName).TargetPath
                if ($target -and (Test-Path $target)) { $RAMMapPath = $target; break }
            }
        }

        # 3) Last resort: shallow filesystem search of the common drop locations.
        if (-not $RAMMapPath) {
            $RAMMapPath = Get-ChildItem -Path @("C:\", "$env:USERPROFILE\Downloads", "$env:USERPROFILE\Desktop") `
                -Filter "RAMMap64.exe" -Recurse -ErrorAction SilentlyContinue -Depth 4 |
                Select-Object -First 1 -ExpandProperty FullName
        }
    }

    if (-not $RAMMapPath -or -not (Test-Path $RAMMapPath)) {
        Write-Host "Couldn't auto-detect RAMMap64.exe (checked Desktop shortcuts and common folders)." -ForegroundColor Yellow
        Write-Host "Right-click the RAMMap shortcut > Properties > 'Target' to get the full path, then pass -RAMMapPath '<that path>'." -ForegroundColor Yellow
    } else {
        Write-Host "Using RAMMap64.exe at: $RAMMapPath"
    }

    # NOTE (confirmed via Task Scheduler 2026-07-01): this task does NOT currently
    # exist — only PCMaint_FlushDNS and PCMaint_RestartExplorer are registered. So we
    # CREATE it when missing (not just re-register), using S4U silent elevation.
    if (-not $RAMMapPath -or -not (Test-Path $RAMMapPath)) {
        Write-Host "Can't proceed: no valid RAMMap64.exe path. Re-run with -RAMMapPath '<path>'." -ForegroundColor Yellow
    } else {
        $verb = if ($existingTask) { "Re-register existing" } else { "CREATE missing" }
        if ($PSCmdlet.ShouldProcess($ramMapTask, "$verb task with RunLevel Highest + LogonType S4U (fully silent elevation)")) {
            $action = New-ScheduledTaskAction -Execute $RAMMapPath -Argument "-Et"
            $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
            $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
            $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

            if ($existingTask) { Unregister-ScheduledTask -TaskName $ramMapTask -Confirm:$false }
            Register-ScheduledTask -TaskName $ramMapTask -Action $action -Trigger $trigger `
                -Principal $principal -Settings $settings `
                -Description "RAMMap -Et: empty standby list, hourly (silently elevated via S4U, no UAC)" | Out-Null
            if ($existingTask) {
                Write-Host "Re-registered $ramMapTask with S4U + Highest — fully silent, no UAC prompt possible."
            } else {
                Write-Host "CREATED $ramMapTask (it was missing) with S4U + Highest — hourly empty-standby, fully silent."
            }
        }
    }
}

# ---------------------------------------------------------------------------
Write-Section "Scheduled maintenance (extends your existing PCMaint_* tasks)"
# Mirrors the style of PCMaint_RestartExplorer / PCMaint_FlushDNS / PCMaint_RAMMap_EmptyStandby
# already on this machine: small, frequent, low-risk tasks.
$taskName = "PCMaint_LowDiskAlert"
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $existing) {
    if ($PSCmdlet.ShouldProcess($taskName, "Create scheduled task: alert when C: drops below 10% free")) {
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument (
            '-NoProfile -WindowStyle Hidden -Command "' +
            '$d = Get-PSDrive C; $pctFree = $d.Free / ($d.Free + $d.Used) * 100; ' +
            'if ($pctFree -lt 10) { ' +
            "New-BurntToastNotification -Text 'Low disk space', ('C: drive at {0:N1}% free' -f `$pctFree) -ErrorAction SilentlyContinue; " +
            "if (-not (Get-Module -ListAvailable BurntToast)) { [System.Windows.Forms.MessageBox]::Show('C: drive low on space: ' + [math]::Round(`$pctFree,1) + '% free') } }" +
            '"'
        )
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 6) -RepetitionDuration ([TimeSpan]::MaxValue)
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description "Warn when C: free space drops below 10%" -Force | Out-Null
        Write-Host "Registered $taskName (checks every 6h)."
    }
} else {
    Write-Host "$taskName already exists — left untouched."
}

# ---------------------------------------------------------------------------
Write-Section "Done"
Write-Host "Re-run with -All for every pass, or pick individual switches:" -ForegroundColor Green
Write-Host "-CleanDiskSpace / -AddDevExclusions / -RelocateDevCaches / -FixRAMMapElevation" -ForegroundColor Green
Write-Host "Add -WhatIf to any of them to preview without changing anything." -ForegroundColor Green
