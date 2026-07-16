<#
  pull_openai_docs.ps1  —  corrected OpenAI docs pull/update (pull + mirror + verify ONLY)

  Purpose : refresh the local durable mirror of the repo's reference/openai/ tree.
  Scope   : PULL and MIRROR and VERIFY only.  This script does NOT index, re-index,
            embed, or mutate SQLite/Chroma.  Indexing is a SEPARATELY AUTHORIZED step.

  Fixes vs. the earlier version:
    - BOM fix : all generated text (inventory/manifest) is written UTF-8 *without* BOM
                via [System.IO.File]::WriteAllText(..., UTF8Encoding($false)).
                (Set-Content -Encoding UTF8 emits a BOM, which breaks strict JSON/JSONL
                 parsers and previously corrupted a config the tooling read.)
    - Folder fix : mirror preserves the reference/openai/ subfolder structure exactly
                   (agents-sdk/, apps-sdk/, cookbook/, node-sdk/, workspace-agents/, ...).
    - Safety : --ff-only pull; refuses to run with a dirty working tree; verifies file
               counts before/after; writes a BOM-free SHA-256 inventory for provenance.

  Edit the two paths below for your machine. No secrets, no tokens, no env values.
#>

param(
    # Local clone of virelai2604/chatgpt-team
    [string]$RepoRoot   = "<WINDOWS_PROJECT_ROOT>\repo\chatgpt-team",
    # Durable mirror destination (docs summaries store)
    [string]$MirrorRoot = "<WINDOWS_PROJECT_ROOT>\01_OpenAI_Docs_Summaries",
    # Prints a reminder that indexing is a separate authorized step. Does NOT index.
    [switch]$AllowIndexReminder
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $enc = New-Object System.Text.UTF8Encoding($false)   # $false = no BOM
    [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

$Source = Join-Path $RepoRoot "reference\openai"
$Dest   = Join-Path $MirrorRoot "reference\openai"

Write-Host "=== 0. Preconditions ===" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
if (-not (Test-Path -LiteralPath $Source))   { throw "Source not found: $Source" }

Set-Location -LiteralPath $RepoRoot
$dirty = git status --porcelain
if ($dirty) { throw "Working tree is dirty. Commit/stash before pulling. Aborting (no mutation)." }

Write-Host "=== 1. Fast-forward pull (no merge commits) ===" -ForegroundColor Cyan
git switch main
git pull --ff-only origin main
$headSha = (git rev-parse HEAD).Trim()
Write-Host "main @ $headSha"

Write-Host "=== 2. Count source files (pre-mirror) ===" -ForegroundColor Cyan
$srcFiles = Get-ChildItem -LiteralPath $Source -Recurse -File
Write-Host ("source files: {0}" -f $srcFiles.Count)

Write-Host "=== 3. Mirror (structure-preserving, no purge) ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $Dest -Force | Out-Null
# /E = subdirs incl. empty ; /XO = skip older (idempotent) ; NO /PURGE so nothing outside scope is deleted
robocopy $Source $Dest /E /XO /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy reported a failure (exit $LASTEXITCODE)." }
$global:LASTEXITCODE = 0   # robocopy 0-7 == success; reset for downstream checks

Write-Host "=== 4. Verify mirror parity ===" -ForegroundColor Cyan
$dstFiles = Get-ChildItem -LiteralPath $Dest -Recurse -File
Write-Host ("mirror files: {0}" -f $dstFiles.Count)
if ($dstFiles.Count -lt $srcFiles.Count) {
    throw "Mirror has fewer files than source ($($dstFiles.Count) < $($srcFiles.Count)). Investigate."
}

Write-Host "=== 5. Write BOM-free SHA-256 inventory (provenance only) ===" -ForegroundColor Cyan
$lines = foreach ($f in ($srcFiles | Sort-Object FullName)) {
    $rel  = $f.FullName.Substring($Source.Length).TrimStart('\','/')
    $hash = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    "{0}  {1}" -f $hash, ($rel -replace '\\','/')
}
$inventory = ($lines -join "`n") + "`n"
$invPath = Join-Path $MirrorRoot ("reference_openai_inventory_{0}.sha256.txt" -f $headSha.Substring(0,7))
Write-Utf8NoBom -Path $invPath -Content $inventory
Write-Host "inventory: $invPath (UTF-8, no BOM)"

Write-Host "`n=== DONE (pull + mirror + verify) ===" -ForegroundColor Green
Write-Host "NOTHING was indexed, embedded, or mutated in SQLite/Chroma."
if ($AllowIndexReminder) {
    Write-Host "`nReminder: indexing is a SEPARATE, explicitly-authorized step." -ForegroundColor Yellow
    Write-Host "Only run your indexer after a source/exclusion/indexing-script change is approved."
}
