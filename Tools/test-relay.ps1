param(
    [string]$LiveHost = "chatgpt-team.pages.dev",
    [int]$LocalPort = 8788,
    [switch]$IncludePaid  # use this switch to include tests that consume OpenAI credits (completions, etc.)
)

$ErrorActionPreference = "Stop"

# ---------- Helper Functions ----------
function Add-Row([string]$Target, [string]$Check, [string]$Result, [string]$Details="") {
    [PSCustomObject]@{ Target=$Target; Check=$Check; Result=$Result; Details=$Details }
}
$rows = @()

function Test-Http($Method, $Url, $Headers=@{}, $Body=$null) {
    # Performs an HTTP request and returns the response (or error response) object.
    $args = @{
        Method      = $Method
        Uri         = $Url
        Headers     = $Headers
        TimeoutSec  = 25
        MaximumRedirection = 0
        ErrorAction = "Stop"
    }
    if ($Body) {
        $args["Body"]        = $Body
        $args["ContentType"] = "application/json"
    }
    try {
        $resp = Invoke-WebRequest @args
        return $resp
    }
    catch {
        # Return the response object from exception if available (to get StatusCode)
        if ($_.Exception.Response) { return $_.Exception.Response }
        else { throw }
    }
}

function Has-Header($Resp, [string]$Name, [string]$Substring="") {
    # Checks if a header is present (and optionally contains a given substring)
    $val = $Resp.Headers[$Name]
    if (-not $val) { return $false }
    if ($Substring) {
        return ( ($val -join ",") -match [regex]::Escape($Substring) )
    }
    return $true
}

# ---------- Ensure sample file exists ----------
$sampleFile = "sample.txt"
if (-not (Test-Path -LiteralPath $sampleFile)) {
    "This is a sample file for testing." | Out-File -LiteralPath $sampleFile -Encoding ASCII
}

# ---------- Repository configuration checks ----------
$catchAllPath = "functions\v1\[[path]].ts"
$wranglerFile = "wrangler.toml"

# 1) Check that the catch-all Cloudflare Worker file exists and is not empty
if (Test-Path -LiteralPath $catchAllPath) {
    $size = (Get-Item -LiteralPath $catchAllPath).Length
    $result = if ($size -gt 0) { "✅ PASS" } else { "❌ FAIL" }
    $rows += Add-Row "repo" "catch-all exists" $result "size=${size} bytes"
} else {
    $rows += Add-Row "repo" "catch-all exists" "❌ FAIL" "missing $catchAllPath"
}

# 2) Check that CORS preflight handling is present in catch-all (look for 'OPTIONS' logic and CORS header)
if (Test-Path -LiteralPath $catchAllPath) {
    $content = Get-Content -LiteralPath $catchAllPath -Raw
    $hasCors = ($content -match 'request\.method\s*-eq\s*"OPTIONS"') -and ($content -match 'Access-Control-Allow-Origin')
    $result = $hasCors ? "✅ PASS" : "⚠️ SKIP"
    $details = $hasCors ? "found" : "not found"
    $rows += Add-Row "repo" "CORS preflight in relay code" $result $details
}

# 3) Check that wrangler.toml specifies a compatibility_date
if (Test-Path -LiteralPath $wranglerFile) {
    $wrContent = Get-Content -LiteralPath $wranglerFile -Raw
    if ($wrContent -match '(?m)^\s*compatibility_date\s*=\s*"(.*?)"') {
        $date = $Matches[1]
        $rows += Add-Row "repo" "wrangler compatibility_date" "✅ PASS" $date
    }
    else {
        $rows += Add-Row "repo" "wrangler compatibility_date" "❌ FAIL" "not set"
    }
} else {
    $rows += Add-Row "repo" "wrangler.toml exists" "❌ FAIL" "missing $wranglerFile"
}

# ---------- Define targets (local dev and live) ----------
$targets = @(
    @{ name="local"; base="http://127.0.0.1:$LocalPort"; up=$true },
    @{ name="live";  base="https://$LiveHost";           up=$true }
)

# ---------- Probe each target ----------
foreach ($t in $targets) {
    $name = $t.name
    $base = $t.base

    # 0) Basic reachability: GET /v1/models
    try {
        $r = Test-Http -Method GET -Url ("$base/v1/models") -Headers @{ Authorization="Bearer test" }
        $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
        $rows += Add-Row $name "GET /v1/models" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) "status=$($r.StatusCode)"
        $t.up = $ok
    }
    catch {
        $rows += Add-Row $name "GET /v1/models" "❌ FAIL" ("error: " + $_.Exception.Message)
        $t.up = $false
    }

    if (-not $t.up) {
        # If this target is not reachable, skip further tests for it
        continue
    }

    # 1) CORS preflight: OPTIONS /v1/chat/completions
    try {
        $optHeaders = @{
            "Origin" = "https://example.com";
            "Access-Control-Request-Method"  = "POST";
            "Access-Control-Request-Headers" = "authorization, content-type, openai-organization"
        }
        $r = Test-Http -Method OPTIONS -Url ("$base/v1/chat/completions") -Headers $optHeaders
        $ok = ($r.StatusCode -eq 204) -and (Has-Header $r "Access-Control-Allow-Origin" "*")
        $details = "status=$($r.StatusCode), A-C-A-O=$($r.Headers['Access-Control-Allow-Origin'])"
        $rows += Add-Row $name "OPTIONS /v1/chat/completions" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) $details
    }
    catch {
        $rows += Add-Row $name "OPTIONS /v1/chat/completions" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 2) Header hygiene: ensure OpenAI response headers are present (e.g. openai-version)
    try {
        $r = Test-Http -Method GET -Url ("$base/v1/models") -Headers @{ Authorization="Bearer test" }
        $ok = Has-Header $r "openai-version"
        $rows += Add-Row $name "Upstream responded (OpenAI headers)" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) ("openai-version=" + $r.Headers["openai-version"])
    }
    catch {
        $rows += Add-Row $name "Upstream responded (OpenAI headers)" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 3) (Optional) Chat Completion and Unified Responses (token-consuming tests)
    if ($IncludePaid) {
        # 3a. POST /v1/chat/completions (simple chat request)
        try {
            $chatBody = @{
                model    = "gpt-3.5-turbo";
                messages = @(@{ role="user"; content="ping" });
                max_tokens = 5
            } | ConvertTo-Json -Depth 4
            $r = Test-Http -Method POST -Url ("$base/v1/chat/completions") -Headers @{ Authorization="Bearer test" } -Body $chatBody
            $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
            $rows += Add-Row $name "POST /v1/chat/completions" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) ("status=" + $r.StatusCode)
        }
        catch {
            $rows += Add-Row $name "POST /v1/chat/completions" "❌ FAIL" ("error: " + $_.Exception.Message)
        }

        # 3b. POST /v1/responses (unified response endpoint)
        try {
            $respBody = @{
                model = "gpt-4o-mini";
                input = "ping";
                max_output_tokens = 8
            } | ConvertTo-Json -Depth 5
            $r = Test-Http -Method POST -Url ("$base/v1/responses") -Headers @{ Authorization="Bearer test" } -Body $respBody
            $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
            $rows += Add-Row $name "POST /v1/responses" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) ("status=" + $r.StatusCode)
        }
        catch {
            $rows += Add-Row $name "POST /v1/responses" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    }

    # 4) POST /v1/embeddings (generate embeddings for a sample input)
    try {
        $embedBody = @{
            model = "text-embedding-ada-002";
            input = "hello world"
        } | ConvertTo-Json
        $r = Test-Http -Method POST -Url ("$base/v1/embeddings") -Headers @{ Authorization="Bearer test" } -Body $embedBody
        $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
        if ($ok) {
            # Parse embedding length for detail
            $embedData = $r.Content | ConvertFrom-Json
            $vecLen = $embedData.data[0].embedding.Count
            $rows += Add-Row $name "POST /v1/embeddings" "✅ PASS" ("status=200, vector_length=$vecLen")
        }
        else {
            $rows += Add-Row $name "POST /v1/embeddings" "❌ FAIL" ("status=" + $r.StatusCode)
        }
    }
    catch {
        $rows += Add-Row $name "POST /v1/embeddings" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 5) POST /v1/audio/speech (Text-to-Speech)
    $ttsFile = "$name-tts-output.mp3"
    try {
        # Use curl for binary response to save directly to file
        Remove-Item -ErrorAction SilentlyContinue $ttsFile  # remove old file if exists
        $curlCmd = "curl.exe -s -w `%{http_code}` -H `"Authorization: Bearer test`" -H `"Content-Type: application/json`" -d `'{"model":"tts-1","input":"Hello world","voice":"en-US-JennyNeural"}'` `"${base}/v1/audio/speech`" -o `"$ttsFile`""
        $statusCodeStr = Invoke-Expression $curlCmd
        $statusCode = [int] $statusCodeStr 2>$null
        if ($statusCode -eq 200 -and (Test-Path -LiteralPath $ttsFile) -and ((Get-Item $ttsFile).Length -gt 0)) {
            $bytes = (Get-Item $ttsFile).Length
            $rows += Add-Row $name "POST /v1/audio/speech" "✅ PASS" "status=200, bytes=$bytes"
        }
        elseif ($statusCodeStr) {
            # Received an HTTP error code
            $rows += Add-Row $name "POST /v1/audio/speech" "❌ FAIL" "status=$statusCodeStr"
        }
        else {
            # Curl didn't return a status (likely connection or execution failure)
            $exitCode = $LASTEXITCODE
            $rows += Add-Row $name "POST /v1/audio/speech" "❌ FAIL" ("no response (curl exit $exitCode)")
        }
    }
    catch {
        $rows += Add-Row $name "POST /v1/audio/speech" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 6) POST /v1/audio/transcriptions (Speech-to-Text)
    if (-not (Test-Path -LiteralPath $ttsFile) -or (Get-Item $ttsFile).Length -eq 0) {
        # No audio file available from TTS, skip STT test
        $rows += Add-Row $name "POST /v1/audio/transcriptions" "⚠️ SKIP" "no audio to transcribe"
    }
    else {
        try {
            $sttForm = @{ file = Get-Item $ttsFile; model = "whisper-1" }
            $r = Invoke-WebRequest -Uri ("$base/v1/audio/transcriptions") -Headers @{ Authorization="Bearer test" } -Method Post -Form $sttForm
            $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
            if ($ok) {
                $transcribed = ($r.Content | ConvertFrom-Json).text
                $rows += Add-Row $name "POST /v1/audio/transcriptions" "✅ PASS" ("status=200, text=\"${transcribed}\"")
            }
            else {
                $rows += Add-Row $name "POST /v1/audio/transcriptions" "❌ FAIL" ("status=" + $r.StatusCode)
            }
        }
        catch {
            $rows += Add-Row $name "POST /v1/audio/transcriptions" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    }

    # 7) POST /v1/images/generations (Image generation)
    try {
        $imgBody = @{
            model = "dall-e-2";
            prompt = "A red apple";
            size   = "1024x1024";
            response_format = "url"
        } | ConvertTo-Json
        $r = Test-Http -Method POST -Url ("$base/v1/images/generations") -Headers @{ Authorization="Bearer test" } -Body $imgBody
        $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
        if ($ok) {
            $imgData = $r.Content | ConvertFrom-Json
            $count = ($imgData.data).Count
            if (-not $count) { $count = 0 }
            $rows += Add-Row $name "POST /v1/images/generations" "✅ PASS" ("status=200, images=$count")
        }
        else {
            $rows += Add-Row $name "POST /v1/images/generations" "❌ FAIL" ("status=" + $r.StatusCode)
        }
    }
    catch {
        $rows += Add-Row $name "POST /v1/images/generations" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 8) File operations: GET/POST/GET-content/DELETE /v1/files
    # 8a. GET /v1/files (list files)
    try {
        $r = Test-Http -Method GET -Url ("$base/v1/files") -Headers @{ Authorization="Bearer test" }
        $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
        if ($ok) {
            $fileList = $r.Content | ConvertFrom-Json
            $fileCount = ($fileList.data).Count
            if (-not $fileCount) { $fileCount = 0 }
            $rows += Add-Row $name "GET /v1/files" "✅ PASS" ("status=200, count=$fileCount")
        }
        else {
            $rows += Add-Row $name "GET /v1/files" "❌ FAIL" ("status=" + $r.StatusCode)
        }
    }
    catch {
        $rows += Add-Row $name "GET /v1/files" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 8b. POST /v1/files (upload sample.txt)
    $uploadedFileId = $null
    try {
        $formData = @{ file = Get-Item $sampleFile; purpose = "fine-tune" }
        $r = Invoke-WebRequest -Uri ("$base/v1/files") -Headers @{ Authorization="Bearer test" } -Method Post -Form $formData
        $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
        if ($ok) {
            $respJson = $r.Content | ConvertFrom-Json
            $uploadedFileId = $respJson.id
            $rows += Add-Row $name "POST /v1/files" "✅ PASS" ("status=200, id=$uploadedFileId")
        }
        else {
            $rows += Add-Row $name "POST /v1/files" "❌ FAIL" ("status=" + $r.StatusCode)
        }
    }
    catch {
        $rows += Add-Row $name "POST /v1/files" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 8c. GET /v1/files/{id}/content (download file content)
    if (-not $uploadedFileId) {
        # If upload failed, skip download and delete
        $rows += Add-Row $name "GET /v1/files/{id}/content" "⚠️ SKIP" "no file to download"
        $rows += Add-Row $name "DELETE /v1/files/{id}" "⚠️ SKIP" "no file to delete"
    }
    else {
        try {
            $downloadPath = "$name-downloaded-sample.txt"
            Remove-Item -ErrorAction SilentlyContinue $downloadPath
            # Use curl to download file content to disk (binary-safe)
            $curlCmd = "curl.exe -s -w `%{http_code}` -H `"Authorization: Bearer test`" `"${base}/v1/files/$uploadedFileId/content`" -o `"$downloadPath`""
            $statusCodeStr = Invoke-Expression $curlCmd
            $code = [int] $statusCodeStr 2>$null
            if ($code -eq 200 -and (Test-Path -LiteralPath $downloadPath)) {
                # Compare downloaded content with original
                $origBytes = [IO.File]::ReadAllBytes($sampleFile)
                $downBytes = [IO.File]::ReadAllBytes($downloadPath)
                $match = ($origBytes.Length -eq $downBytes.Length) -and ($origBytes -ceq $downBytes)
                if ($match) {
                    $size = $downBytes.Length
                    $rows += Add-Row $name "GET /v1/files/$uploadedFileId/content" "✅ PASS" "status=200, size=${size} bytes"
                }
                else {
                    $rows += Add-Row $name "GET /v1/files/$uploadedFileId/content" "❌ FAIL" "content mismatch"
                }
            }
            elseif ($statusCodeStr) {
                $rows += Add-Row $name "GET /v1/files/$uploadedFileId/content" "❌ FAIL" "status=$statusCodeStr"
            }
            else {
                $rows += Add-Row $name "GET /v1/files/$uploadedFileId/content" "❌ FAIL" "no response"
            }
        }
        catch {
            $rows += Add-Row $name "GET /v1/files/$uploadedFileId/content" "❌ FAIL" ("error: " + $_.Exception.Message)
        }

        # 8d. DELETE /v1/files/{id} (delete uploaded file)
        try {
            $r = Test-Http -Method DELETE -Url ("$base/v1/files/$uploadedFileId") -Headers @{ Authorization="Bearer test" }
            $ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
            if ($ok) {
                $delJson = $r.Content | ConvertFrom-Json
                $deletedFlag = $delJson.deleted
                $rows += Add-Row $name "DELETE /v1/files/$uploadedFileId" ($(if ($deletedFlag) { "✅ PASS" } else { "❌ FAIL" })) ("status=200, deleted=$deletedFlag")
            }
            else {
                $rows += Add-Row $name "DELETE /v1/files/$uploadedFileId" "❌ FAIL" ("status=" + $r.StatusCode)
            }
        }
        catch {
            $rows += Add-Row $name "DELETE /v1/files/$uploadedFileId" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    }
}

# ---------- Output Results ----------
# Format and print the results table with color-coded PASS/FAIL
# (Color only the Result column for clarity)
# Print header
Write-Host ("{0,-7}  {1,-30}  {2,-6}  {3}" -f "Target", "Check", "Result", "Details")
foreach ($row in $rows) {
    $target = $row.Target
    $check  = $row.Check
    $resultText = $row.Result
    $details = $row.Details
    # Determine color for result text
    $color = "White"
    if ($resultText -like "*PASS*") { $color = "Green" }
    elseif ($resultText -like "*FAIL*") { $color = "Red" }
    elseif ($resultText -like "*SKIP*") { $color = "Yellow" }
    # Write each row with the result colored
    Write-Host ("{0,-7}  {1,-30}  " -f $target, $check) -NoNewline
    Write-Host ("$resultText") -ForegroundColor $color -NoNewline
    Write-Host ("  $details")
}
