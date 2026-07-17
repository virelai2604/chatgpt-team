<#
  pull_openai_docs.ps1  —  corrected OpenAI docs pull/update (pull + mirror + VERIFY parity)

  Purpose : refresh the local durable mirror of the repo's docs from reference/openai/.
  Scope   : PULL and MIRROR and VERIFY only. Does NOT index/re-index/embed/mutate
            SQLite/Chroma. Indexing is a SEPARATELY AUTHORIZED step.

  ----------------------------------------------------------------------------------
  DESTINATION DECISION (documented per review)
  ----------------------------------------------------------------------------------
  The established canonical docs-summaries store is a FLAT directory holding the 17
  summary files directly:
        <MirrorRoot>\01_OpenAI_Docs_Summaries\   (Option A)
  This script therefore defaults to Option A and mirrors the repo's
        reference/openai/01_OpenAI_Docs_Summaries\
  (the 15 numbered summaries + README + manifest.jsonl) FLAT into that directory,
  matching the recorded layout.

  It does NOT dump the whole reference/openai/ tree into a nested
  ...\01_OpenAI_Docs_Summaries\reference\openai\ folder (the earlier behavior, which
  silently changed the durable layout). To ALSO mirror the broader reference/openai/
  tree (agents-sdk/, apps-sdk/, cookbook/, node-sdk/, workspace-agents/, ...), pass
  -MirrorFullReferenceTree; it goes to a clearly separate sibling dir and is verified
  the same way. The two corpora are kept distinct on purpose.

  ----------------------------------------------------------------------------------
  VERIFICATION (exact, per review)
  ----------------------------------------------------------------------------------
  - Builds relPath -> SHA-256 maps for BOTH source and destination.
  - MISSING  : in source, absent/mismatched in dest  -> reported, script FAILS.
  - STALE    : in dest, not in source                -> reported; NOT deleted unless
               -Purge is explicitly supplied.
  - Parity is proven by hash equality on matching relative paths, not by file count.

  BOM note (corrected): `Set-Content -Encoding UTF8` behavior is VERSION-DEPENDENT:
  Windows PowerShell 5.1 emits a UTF-8 BOM; PowerShell 7+ defaults to BOM-less UTF-8.
  The earlier config corruption came from 5.1's BOM. This script sidesteps the whole
  issue by writing generated text via [IO.File]::WriteAllText(..., UTF8Encoding($false))
  which is BOM-free on every version.

  No secrets, tokens, or env values. Edit the paths for your machine.
#>

param(
    [string]$RepoRoot   = "<WINDOWS_PROJECT_ROOT>\repo\chatgpt-team",
    [string]$MirrorRoot = "<WINDOWS_PROJECT_ROOT>",
    # Option A source: the summaries subfolder in the repo.
    [string]$SummariesSubPath = "reference\openai\01_OpenAI_Docs_Summaries",
    # Also mirror the full reference/openai/ tree to a separate sibling dir.
    [switch]$MirrorFullReferenceTree,
    # Delete stale destination files. OFF by default (report-and-stop instead).
    [switch]$Purge
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $enc = New-Object System.Text.UTF8Encoding($false)   # $false = no BOM (all PS versions)
    [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

function Get-RelHashMap([string]$Root) {
    $map = @{}
    if (-not (Test-Path -LiteralPath $Root)) { return $map }
    $base = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\','/')
    foreach ($f in Get-ChildItem -LiteralPath $Root -Recurse -File) {
        $rel = $f.FullName.Substring($base.Length).TrimStart('\','/') -replace '\\','/'
        $map[$rel] = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    }
    return $map
}

# Returns $true if dest is an exact superset-verified mirror of source (no missing/mismatch).
function Verify-Parity([string]$Label, [string]$Source, [string]$Dest, [bool]$DoPurge) {
    Write-Host "--- verify parity: $Label ---" -ForegroundColor Cyan
    $src = Get-RelHashMap $Source
    $dst = Get-RelHashMap $Dest

    $missing = @()   # in source, absent or hash-mismatched in dest
    foreach ($rel in $src.Keys) {
        if (-not $dst.ContainsKey($rel)) { $missing += "MISSING  $rel" }
        elseif ($dst[$rel] -ne $src[$rel]) { $missing += "MISMATCH $rel" }
    }
    $stale = @()     # in dest, not in source
    foreach ($rel in $dst.Keys) {
        if (-not $src.ContainsKey($rel)) { $stale += $rel }
    }

    Write-Host ("source files: {0} ; dest files: {1}" -f $src.Count, $dst.Count)
    if ($missing.Count) {
        Write-Host "FAIL: source files missing/mismatched in destination:" -ForegroundColor Red
        $missing | ForEach-Object { Write-Host "  $_" }
        throw "$Label parity failed: $($missing.Count) missing/mismatched."
    }
    if ($stale.Count) {
        Write-Host "STALE destination files (not in source):" -ForegroundColor Yellow
        $stale | ForEach-Object { Write-Host "  STALE  $_" }
        if ($DoPurge) {
            foreach ($rel in $stale) {
                $p = Join-Path $Dest ($rel -replace '/','\')
                Remove-Item -LiteralPath $p -Force
                Write-Host "  PURGED $rel"
            }
        } else {
            throw "$Label has $($stale.Count) stale dest file(s). Re-run with -Purge to remove, or clean manually. Stopping (no auto-delete)."
        }
    }
    Write-Host "OK: exact relative-path + SHA-256 parity." -ForegroundColor Green
    return $src
}

Write-Host "=== 0. Preconditions ===" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
Set-Location -LiteralPath $RepoRoot
if (git status --porcelain) { throw "Working tree is dirty. Commit/stash before pulling. Aborting (no mutation)." }

Write-Host "=== 1. Fast-forward pull ===" -ForegroundColor Cyan
git switch main
git pull --ff-only origin main
$headSha = (git rev-parse HEAD).Trim()
Write-Host "main @ $headSha"

# --- Option A: summaries -> flat 01_OpenAI_Docs_Summaries ---
$srcSummaries = Join-Path $RepoRoot $SummariesSubPath
$dstSummaries = Join-Path $MirrorRoot "01_OpenAI_Docs_Summaries"
if (-not (Test-Path -LiteralPath $srcSummaries)) { throw "Summaries source not found: $srcSummaries" }

Write-Host "=== 2. Mirror summaries (flat, structure-preserving, no auto-purge) ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $dstSummaries -Force | Out-Null
robocopy $srcSummaries $dstSummaries /E /XO /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy (summaries) failed (exit $LASTEXITCODE)." }
$global:LASTEXITCODE = 0

Write-Host "=== 3. Verify summaries parity ===" -ForegroundColor Cyan
$srcMap = Verify-Parity -Label "summaries" -Source $srcSummaries -Dest $dstSummaries -DoPurge:$Purge

# --- Optional: full reference/openai tree -> separate sibling dir ---
if ($MirrorFullReferenceTree) {
    $srcFull = Join-Path $RepoRoot "reference\openai"
    # TRUE sibling of 01_OpenAI_Docs_Summaries (NOT nested inside it), so the summaries
    # parity walk never sees these files as "stale". Keeps the two corpora separate.
    $dstFull = Join-Path $MirrorRoot "reference_openai_full"
    Write-Host "=== 2b. Mirror full reference/openai tree (separate sibling dir) ===" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $dstFull -Force | Out-Null
    robocopy $srcFull $dstFull /E /XO /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy (full tree) failed (exit $LASTEXITCODE)." }
    $global:LASTEXITCODE = 0
    Verify-Parity -Label "reference-openai-full" -Source $srcFull -Dest $dstFull -DoPurge:$Purge | Out-Null
}

Write-Host "=== 4. BOM-free SHA-256 inventory (provenance) ===" -ForegroundColor Cyan
$lines = foreach ($rel in ($srcMap.Keys | Sort-Object)) { "{0}  {1}" -f $srcMap[$rel], $rel }
$inventory = ($lines -join "`n") + "`n"
$invPath = Join-Path $MirrorRoot ("reference_openai_summaries_inventory_{0}.sha256.txt" -f $headSha.Substring(0,7))
Write-Utf8NoBom -Path $invPath -Content $inventory
Write-Host "inventory: $invPath (UTF-8, no BOM)"

Write-Host "`n=== DONE (pull + mirror + verified parity) ===" -ForegroundColor Green
Write-Host "Destination = Option A (flat 01_OpenAI_Docs_Summaries). NOTHING indexed/embedded/mutated."
Write-Host "Indexing remains a SEPARATE, explicitly-authorized step."
