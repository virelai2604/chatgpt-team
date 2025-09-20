param(
    [string]$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Auth = "dev",
    [int]$TimeoutSec = 60,
    [int]$LocalPort = 8788
)

$ErrorActionPreference = "Stop"

# Helper: Load environment variables from .dev.vars if present
function Read-DotEnv($path) {
    if (!(Test-Path $path)) { return @{} }
    $envMap = @{}
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $envMap[$parts[0].Trim()] = $parts[1].Trim().Trim('"')
        }
    }
    return $envMap
}

# Load .dev.vars and resolve API key
Set-Location $RepoRoot
$dotenv = Read-DotEnv (Join-Path $RepoRoot ".dev.vars")
function Get-AuthKey {
    param([string]$Mode, [hashtable]$DotEnv)
    if ($Mode -and $Mode -ne "dev") {
        return $Mode  # explicit key was provided
    }
    $candidates = @(
        $env:OPENAI_CLIENT_KEY, $env:OPENAI_API_KEY, $env:OPENAI_KEY,
        $DotEnv["OPENAI_CLIENT_KEY"], $DotEnv["OPENAI_API_KEY"], $DotEnv["OPENAI_KEY"]
    ) | Where-Object { $_ -and $_.Trim() }
    if ($candidates.Count -eq 0) {
        throw "No OpenAI API key found in environment or .dev.vars"
    }
    return $candidates[0]
}
$OpenAIKey = Get-AuthKey -Mode $Auth -DotEnv $dotenv

# Prepare results collection and helper
function Add-Row([string]$Target, [string]$Check, [string]$Result, [string]$Details="") {
    [PSCustomObject]@{ Target=$Target; Check=$Check; Result=$Result; Details=$Details }
}
$rows = @()

# HTTP request helper (standardized timeout & error handling)
function Test-Http($Method, $Url, $Headers, $Body=$null) {
    $params = @{
        Method      = $Method
        Uri         = $Url
        Headers     = $Headers
        TimeoutSec  = $TimeoutSec
        MaximumRedirection = 0
        ErrorAction = "Stop"
    }
    if ($Body) {
        $params["Body"]        = $Body
        $params["ContentType"] = "application/json"
    }
    try {
        return Invoke-WebRequest @params
    } catch {
        # If the response has a status (e.g. 4xx/5xx), return it; otherwise rethrow
        if ($_.Exception.Response) { return $_.Exception.Response }
        throw
    }
}

# Ensure a small sample file exists for file upload tests
$sampleFile = "sample.txt"
if (-not (Test-Path $sampleFile)) {
    "This is a sample file for testing." | Set-Content -Path $sampleFile -Encoding ASCII
}

# Define targets: official OpenAI, local Pages dev, deployed Pages
$targets = @(
    @{ name="openai"; base="https://api.openai.com/v1"; up=$true },
    @{ name="local";  base="http://127.0.0.1:$LocalPort/v1"; up=$true },
    @{ name="pages";  base="https://chatgpt-team.pages.dev/v1"; up=$true }
)

foreach ($t in $targets) {
    $name = $t.name
    $base = $t.base
    # Use real API key for official, dummy "test" for relay (relay will inject real key server-side)
    $authHeaderValue = if ($name -eq "openai") { "Bearer $OpenAIKey" } else { "Bearer test" }
    $commonHeaders = @{ Authorization = $authHeaderValue }

    # 0) Basic reachability: GET /v1/models
    try {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method GET -Url "$base/models" -Headers $commonHeaders
        $sw.Stop()
        $status = $resp.StatusCode
        $ok = ($status -ge 200 -and $status -lt 300)
        $rows += Add-Row $name "GET /v1/models" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) "status=$status, time=${($sw.ElapsedMilliseconds)}ms"
        $t.up = $ok
    } catch {
        $rows += Add-Row $name "GET /v1/models" "❌ FAIL" ("error: " + $_.Exception.Message)
        $t.up = $false
    }
    if (-not $t.up) { continue }  # skip further tests if not reachable

    # 1) OPTIONS /v1/chat/completions (CORS preflight, only relevant for relay)
    if ($name -ne "openai") {
        try {
            $preflightHeaders = @{
                "Origin" = "https://example.com";
                "Access-Control-Request-Method"  = "POST";
                "Access-Control-Request-Headers" = "authorization, content-type, openai-organization"
            }
            $sw = [Diagnostics.Stopwatch]::StartNew()
            $resp = Test-Http -Method OPTIONS -Url "$base/chat/completions" -Headers $preflightHeaders
            $sw.Stop()
            $status = $resp.StatusCode
            $allowOrigin = $resp.Headers['Access-Control-Allow-Origin']
            $ok = ($status -eq 204) -and ($allowOrigin -eq '*')
            $rows += Add-Row $name "OPTIONS /v1/chat/completions" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) "status=$status, A-C-A-O=$allowOrigin, time=${($sw.ElapsedMilliseconds)}ms"
        } catch {
            $rows += Add-Row $name "OPTIONS /v1/chat/completions" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    } else {
        $rows += Add-Row $name "OPTIONS /v1/chat/completions" "⚠️ SKIP" "not applicable"
    }

    # 2) Header hygiene: OpenAI response headers (e.g. openai-version)
    try {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method GET -Url "$base/models" -Headers $commonHeaders
        $sw.Stop()
        $openaiVer = $resp.Headers["openai-version"]
        $ok = [string]::IsNullOrEmpty($openaiVer) -ne $true
        $detail = ($openaiVer ? "openai-version=$openaiVer" : "missing openai-version")
        $rows += Add-Row $name "OpenAI headers present" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) ($detail + ", time=${($sw.ElapsedMilliseconds)}ms")
    } catch {
        $rows += Add-Row $name "OpenAI headers present" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 3a) POST /v1/chat/completions (simple chat request)
    try {
        $chatBody = @{
            model    = "gpt-3.5-turbo";
            messages = @(@{ role="user"; content="ping" });
            max_tokens = 5
        } | ConvertTo-Json -Depth 4
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method POST -Url "$base/chat/completions" -Headers $commonHeaders -Body $chatBody
        $sw.Stop()
        $status = $resp.StatusCode
        $ok = ($status -ge 200 -and $status -lt 300)
        $rows += Add-Row $name "POST /v1/chat/completions" ($(if ($ok) { "✅ PASS" } else { "❌ FAIL" })) "status=$status, time=${($sw.ElapsedMilliseconds)}ms"
    } catch {
        $rows += Add-Row $name "POST /v1/chat/completions" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 3b) POST /v1/completions (legacy text completions)
    try {
        $compBody = @{ model="text-ada-001"; prompt="Hello"; max_tokens=5 } | ConvertTo-Json
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method POST -Url "$base/completions" -Headers $commonHeaders -Body $compBody
        $sw.Stop()
        $status = $resp.StatusCode
        $ok = ($status -ge 200 -and $status -lt 300)
        if ($ok) {
            $out = $resp.Content | ConvertFrom-Json
            $textOut = $out.choices[0].text -replace "`r`n", " "
            if ($textOut.Length -gt 50) { $textOut = $textOut.Substring(0,47) + "..." }
            $rows += Add-Row $name "POST /v1/completions" "✅ PASS" "status=200, text=\"${textOut}\", time=${($sw.ElapsedMilliseconds)}ms"
        } else {
            $rows += Add-Row $name "POST /v1/completions" "❌ FAIL" "status=$status"
        }
    } catch {
        $rows += Add-Row $name "POST /v1/completions" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 4) POST /v1/embeddings (embedding vector generation)
    try {
        $embBody = @{ model="text-embedding-ada-002"; input="hello world" } | ConvertTo-Json
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method POST -Url "$base/embeddings" -Headers $commonHeaders -Body $embBody
        $sw.Stop()
        $status = $resp.StatusCode
        if ($status -ge 200 -and $status -lt 300) {
            $data = $resp.Content | ConvertFrom-Json
            $vecLen = $data.data[0].embedding.Count
            $rows += Add-Row $name "POST /v1/embeddings" "✅ PASS" "status=200, vector_length=$vecLen, time=${($sw.ElapsedMilliseconds)}ms"
        } else {
            $rows += Add-Row $name "POST /v1/embeddings" "❌ FAIL" "status=$status"
        }
    } catch {
        $rows += Add-Row $name "POST /v1/embeddings" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 5) POST /v1/audio/speech (Text-to-Speech)
    $ttsFile = "$name-tts-output.mp3"
    try {
        Remove-Item -ErrorAction SilentlyContinue $ttsFile
        $ttsJson = '{"model":"tts-1","input":"Hello world","voice":"en-US-JennyNeural"}'
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $curlCmd = "curl.exe -s -H `"Authorization: $authHeaderValue`" -H `"Content-Type: application/json`" -d '$ttsJson' `"$base/audio/speech`" -o `"$ttsFile`" -w %{http_code}"
        $code = Invoke-Expression $curlCmd
        $sw.Stop()
        if ([int]$code -eq 200 -and (Test-Path $ttsFile) -and ((Get-Item $ttsFile).Length -gt 0)) {
            $bytes = (Get-Item $ttsFile).Length
            $rows += Add-Row $name "POST /v1/audio/speech" "✅ PASS" "status=200, bytes=$bytes, time=${($sw.ElapsedMilliseconds)}ms"
        } elseif ($code) {
            $rows += Add-Row $name "POST /v1/audio/speech" "❌ FAIL" "status=$code"
        } else {
            $rows += Add-Row $name "POST /v1/audio/speech" "❌ FAIL" "no response (curl exit $LASTEXITCODE)"
        }
    } catch {
        $rows += Add-Row $name "POST /v1/audio/speech" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 6) POST /v1/audio/transcriptions (Speech-to-Text)
    if (-not (Test-Path $ttsFile) -or (Get-Item $ttsFile).Length -eq 0) {
        $rows += Add-Row $name "POST /v1/audio/transcriptions" "⚠️ SKIP" "no audio to transcribe"
    } else {
        try {
            $sw = [Diagnostics.Stopwatch]::StartNew()
            $sttResp = Invoke-WebRequest -Uri "$base/audio/transcriptions" -Headers $commonHeaders -Method Post -Form @{ file=Get-Item $ttsFile; model="whisper-1" } -TimeoutSec $TimeoutSec
            $sw.Stop()
            $status = $sttResp.StatusCode
            if ($status -ge 200 -and $status -lt 300) {
                $text = (ConvertFrom-Json $sttResp.Content).text
                if ($text.Length -gt 50) { $text = $text.Substring(0,47) + "..." }
                $rows += Add-Row $name "POST /v1/audio/transcriptions" "✅ PASS" "status=200, text=\"${text}\", time=${($sw.ElapsedMilliseconds)}ms"
            } else {
                $rows += Add-Row $name "POST /v1/audio/transcriptions" "❌ FAIL" "status=$status"
            }
        } catch {
            $rows += Add-Row $name "POST /v1/audio/transcriptions" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    }

    # 7) POST /v1/images/generations (image creation)
    try {
        $imgBody = @{ model="dall-e-2"; prompt="A red apple"; size="256x256"; response_format="url" } | ConvertTo-Json
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method POST -Url "$base/images/generations" -Headers $commonHeaders -Body $imgBody
        $sw.Stop()
        $status = $resp.StatusCode
        if ($status -ge 200 -and $status -lt 300) {
            $imgData = $resp.Content | ConvertFrom-Json
            $count = ($imgData.data).Count; if (-not $count) { $count = 0 }
            $rows += Add-Row $name "POST /v1/images/generations" "✅ PASS" "status=200, images=$count, time=${($sw.ElapsedMilliseconds)}ms"
        } else {
            $rows += Add-Row $name "POST /v1/images/generations" "❌ FAIL" "status=$status"
        }
    } catch {
        $rows += Add-Row $name "POST /v1/images/generations" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 8a) GET /v1/files (list files)
    try {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method GET -Url "$base/files" -Headers $commonHeaders
        $sw.Stop()
        $status = $resp.StatusCode
        if ($status -ge 200 -and $status -lt 300) {
            $fileList = $resp.Content | ConvertFrom-Json
            $count = ($fileList.data).Count; if (-not $count) { $count = 0 }
            $rows += Add-Row $name "GET /v1/files" "✅ PASS" "status=200, count=$count, time=${($sw.ElapsedMilliseconds)}ms"
        } else {
            $rows += Add-Row $name "GET /v1/files" "❌ FAIL" "status=$status"
        }
    } catch {
        $rows += Add-Row $name "GET /v1/files" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 8b) POST /v1/files (upload file)
    $uploadedFileId = $null
    try {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Invoke-WebRequest -Uri "$base/files" -Headers $commonHeaders -Method Post -Form @{ file=Get-Item $sampleFile; purpose="fine-tune" } -TimeoutSec $TimeoutSec
        $sw.Stop()
        $status = $resp.StatusCode
        if ($status -ge 200 -and $status -lt 300) {
            $respJson = $resp.Content | ConvertFrom-Json
            $uploadedFileId = $respJson.id
            $rows += Add-Row $name "POST /v1/files" "✅ PASS" "status=200, id=$uploadedFileId, time=${($sw.ElapsedMilliseconds)}ms"
        } else {
            $rows += Add-Row $name "POST /v1/files" "❌ FAIL" "status=$status"
        }
    } catch {
        $rows += Add-Row $name "POST /v1/files" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 8c) GET /v1/files/{id}/content (download file content)
    if (-not $uploadedFileId) {
        $rows += Add-Row $name "GET /v1/files/{id}/content" "⚠️ SKIP" "no file to download"
        $rows += Add-Row $name "DELETE /v1/files/{id}" "⚠️ SKIP" "no file to delete"
    } else {
        try {
            $downloadPath = "$name-downloaded.txt"
            Remove-Item -ErrorAction SilentlyContinue $downloadPath
            $sw = [Diagnostics.Stopwatch]::StartNew()
            $curlCmd = "curl.exe -s -H `"Authorization: $authHeaderValue`" `"$base/files/$uploadedFileId/content`" -o `"$downloadPath`" -w %{http_code}"
            $code = Invoke-Expression $curlCmd
            $sw.Stop()
            if ([int]$code -eq 200 -and (Test-Path $downloadPath)) {
                $origBytes = [IO.File]::ReadAllBytes($sampleFile)
                $downBytes = [IO.File]::ReadAllBytes($downloadPath)
                $match = ($origBytes.Length -eq $downBytes.Length) -and ($origBytes -ceq $downBytes)
                if ($match) {
                    $rows += Add-Row $name "GET /v1/files/{id}/content" "✅ PASS" "status=200, size=${($downBytes.Length)} bytes, time=${($sw.ElapsedMilliseconds)}ms"
                } else {
                    $rows += Add-Row $name "GET /v1/files/{id}/content" "❌ FAIL" "content mismatch"
                }
            } elseif ($code) {
                $rows += Add-Row $name "GET /v1/files/{id}/content" "❌ FAIL" "status=$code"
            } else {
                $rows += Add-Row $name "GET /v1/files/{id}/content" "❌ FAIL" "no response"
            }
        } catch {
            $rows += Add-Row $name "GET /v1/files/{id}/content" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
        # 8d) DELETE /v1/files/{id}
        try {
            $sw = [Diagnostics.Stopwatch]::StartNew()
            $resp = Test-Http -Method DELETE -Url "$base/files/$uploadedFileId" -Headers $commonHeaders
            $sw.Stop()
            $status = $resp.StatusCode
            if ($status -ge 200 -and $status -lt 300) {
                $delJson = $resp.Content | ConvertFrom-Json
                $deletedFlag = $delJson.deleted
                $rows += Add-Row $name "DELETE /v1/files/{id}" ($(if ($deletedFlag) { "✅ PASS" } else { "❌ FAIL" })) "status=200, deleted=$deletedFlag, time=${($sw.ElapsedMilliseconds)}ms"
            } else {
                $rows += Add-Row $name "DELETE /v1/files/{id}" "❌ FAIL" "status=$status"
            }
        } catch {
            $rows += Add-Row $name "DELETE /v1/files/{id}" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    }

    # 9a) POST /assistants (create assistant)
    $assistantId = $null
    try {
        $asstBody = @{ name="Test Assistant"; instructions="You are a helpful assistant."; model="gpt-3.5-turbo" } | ConvertTo-Json -Depth 4
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method POST -Url "$base/assistants" -Headers $commonHeaders -Body $asstBody
        $sw.Stop()
        $status = $resp.StatusCode
        if ($status -ge 200 -and $status -lt 300) {
            $assistantId = (ConvertFrom-Json $resp.Content).id
            $rows += Add-Row $name "POST /assistants" "✅ PASS" "status=200, id=$assistantId, time=${($sw.ElapsedMilliseconds)}ms"
        } else {
            $rows += Add-Row $name "POST /assistants" ($(if ($status -eq 404) { "⚠️ SKIP" } else { "❌ FAIL" })) "status=$status"
        }
    } catch {
        if ($_.Exception.Message -match "404") {
            $rows += Add-Row $name "POST /assistants" "⚠️ SKIP" "not supported"
        } else {
            $rows += Add-Row $name "POST /assistants" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    }
    if (-not $assistantId) {
        $rows += Add-Row $name "POST /threads" "⚠️ SKIP" "assistant not created"
        $rows += Add-Row $name "POST /threads/{id}/messages" "⚠️ SKIP" "assistant not created"
        $rows += Add-Row $name "POST /threads/{id}/runs" "⚠️ SKIP" "assistant not created"
        $rows += Add-Row $name "GET /threads/{id}/messages" "⚠️ SKIP" "assistant not created"
        $rows += Add-Row $name "Tool call flow" "⚠️ SKIP" "assistant not created"
        continue
    }

    # 9b) POST /threads (create conversation thread)
    $threadId = $null
    try {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method POST -Url "$base/threads" -Headers $commonHeaders -Body "{}"
        $sw.Stop()
        $status = $resp.StatusCode
        if ($status -ge 200 -and $status -lt 300) {
            $threadId = (ConvertFrom-Json $resp.Content).id
            $rows += Add-Row $name "POST /threads" "✅ PASS" "status=200, id=$threadId, time=${($sw.ElapsedMilliseconds)}ms"
        } else {
            $rows += Add-Row $name "POST /threads" "❌ FAIL" "status=$status"
        }
    } catch {
        $rows += Add-Row $name "POST /threads" "❌ FAIL" ("error: " + $_.Exception.Message)
    }
    if (-not $threadId) {
        $rows += Add-Row $name "POST /threads/{id}/messages" "⚠️ SKIP" "thread not created"
        $rows += Add-Row $name "POST /threads/{id}/runs" "⚠️ SKIP" "thread not created"
        $rows += Add-Row $name "GET /threads/{id}/messages" "⚠️ SKIP" "thread not created"
        $rows += Add-Row $name "Tool call flow" "⚠️ SKIP" "thread not created"
        continue
    }

    # 9c) POST /threads/{id}/messages (add user message)
    try {
        $msgBody = @{ role="user"; content="What is 2 + 2?" } | ConvertTo-Json
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method POST -Url "$base/threads/$threadId/messages" -Headers $commonHeaders -Body $msgBody
        $sw.Stop()
        $status = $resp.StatusCode
        $rows += Add-Row $name "POST /threads/{id}/messages" ($(if ($status -ge 200 -and $status -lt 300) { "✅ PASS" } else { "❌ FAIL" })) "status=$status, time=${($sw.ElapsedMilliseconds)}ms"
    } catch {
        $rows += Add-Row $name "POST /threads/{id}/messages" "❌ FAIL" ("error: " + $_.Exception.Message)
    }

    # 9d) POST /threads/{id}/runs (invoke assistant on thread)
    $runId = $null
    try {
        $runBody = @{ assistant_id = $assistantId } | ConvertTo-Json
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $resp = Test-Http -Method POST -Url "$base/threads/$threadId/runs" -Headers $commonHeaders -Body $runBody
        $sw.Stop()
        $status = $resp.StatusCode
        if ($status -ge 200 -and $status -lt 300) {
            $runId = (ConvertFrom-Json $resp.Content).id
            $rows += Add-Row $name "POST /threads/{id}/runs" "✅ PASS" "status=200, id=$runId, time=${($sw.ElapsedMilliseconds)}ms"
        } else {
            $rows += Add-Row $name "POST /threads/{id}/runs" "❌ FAIL" "status=$status"
        }
    } catch {
        $rows += Add-Row $name "POST /threads/{id}/runs" "❌ FAIL" ("error: " + $_.Exception.Message)
    }
    if ($runId) {
        # Poll run status until completed or waiting (required_action)
        try {
            $maxPoll = 10; $pollCount = 0; $runStatus = $null
            do {
                Start-Sleep -Seconds 2
                $pollCount++
                $runStatus = (Test-Http -Method GET -Url "$base/threads/$threadId/runs/$runId" -Headers $commonHeaders).Content | ConvertFrom-Json
            } while ($pollCount -lt $maxPoll -and $runStatus.status -notin @("completed","failed") -and -not $runStatus.required_action)
            if ($runStatus.required_action) {
                $rows += Add-Row $name "GET /threads/{id}/runs/{id}" "✅ PASS" "status=$($runStatus.status), required_action=$($runStatus.required_action.type)"
            } elseif ($runStatus.status -eq "completed") {
                $rows += Add-Row $name "GET /threads/{id}/runs/{id}" "✅ PASS" "status=completed"
            } else {
                $rows += Add-Row $name "GET /threads/{id}/runs/{id}" "❌ FAIL" "status=$($runStatus.status)"
            }
        } catch {
            $rows += Add-Row $name "GET /threads/{id}/runs/{id}" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    } else {
        $rows += Add-Row $name "GET /threads/{id}/runs/{id}" "⚠️ SKIP" "run not started"
    }

    # 9e) GET /threads/{id}/messages (retrieve all messages, including assistant reply)
    if ($runId) {
        try {
            $sw = [Diagnostics.Stopwatch]::StartNew()
            $resp = Test-Http -Method GET -Url "$base/threads/$threadId/messages" -Headers $commonHeaders
            $sw.Stop()
            $status = $resp.StatusCode
            if ($status -ge 200 -and $status -lt 300) {
                $messages = ConvertFrom-Json $resp.Content
                $assistantMsg = $messages.data | Where-Object { $_.role -eq "assistant" } | Select-Object -First 1
                $replyPreview = ""
                if ($assistantMsg) {
                    try { $replyPreview = $assistantMsg.content[0].text.value }
                    catch { $replyPreview = ($assistantMsg.content | Out-String).Trim() }
                    if ($replyPreview.Length -gt 50) { $replyPreview = $replyPreview.Substring(0,47) + "..." }
                }
                $rows += Add-Row $name "GET /threads/{id}/messages" "✅ PASS" "status=200, assistant_reply=\"${replyPreview}\", time=${($sw.ElapsedMilliseconds)}ms"
            } else {
                $rows += Add-Row $name "GET /threads/{id}/messages" "❌ FAIL" "status=$status"
            }
        } catch {
            $rows += Add-Row $name "GET /threads/{id}/messages" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    } else {
        $rows += Add-Row $name "GET /threads/{id}/messages" "⚠️ SKIP" "run not completed"
    }

    # 9f) Tool call flow: create assistant with a function tool and test function-call handling
    $toolAsstId = $null; $toolThreadId = $null
    try {
        $toolAsstBody = @{
            name = "Tool Test Assistant";
            instructions = "You have a 'get_time' tool to fetch current time. If asked for the current time, always call the get_time function.";
            model = "gpt-3.5-turbo";
            tools = @(@{
                name="get_time";
                description="Get current time";
                parameters=@{ type="object"; properties=@{} }
            })
        } | ConvertTo-Json -Depth 6
        $toolResp = Test-Http -Method POST -Url "$base/assistants" -Headers $commonHeaders -Body $toolAsstBody
        if ($toolResp.StatusCode -ge 200 -and $toolResp.StatusCode -lt 300) {
            $toolAsstId = (ConvertFrom-Json $toolResp.Content).id
        }
    } catch {}
    if ($toolAsstId) {
        try {
            $thrResp = Test-Http -Method POST -Url "$base/threads" -Headers $commonHeaders -Body "{}"
            if ($thrResp.StatusCode -ge 200 -and $thrResp.StatusCode -lt 300) {
                $toolThreadId = (ConvertFrom-Json $thrResp.Content).id
            }
        } catch {}
    }
    if ($toolAsstId -and $toolThreadId) {
        try {
            $msgBody = @{ role="user"; content="What time is it now?" } | ConvertTo-Json
            $null = Test-Http -Method POST -Url "$base/threads/$toolThreadId/messages" -Headers $commonHeaders -Body $msgBody
            $runBody = @{ assistant_id = $toolAsstId } | ConvertTo-Json
            $runResp = Test-Http -Method POST -Url "$base/threads/$toolThreadId/runs" -Headers $commonHeaders -Body $runBody
            if ($runResp.StatusCode -ge 200 -and $runResp.StatusCode -lt 300) {
                $newRunId = (ConvertFrom-Json $runResp.Content).id
                Start-Sleep -Seconds 3
                $statusResp = Test-Http -Method GET -Url "$base/threads/$toolThreadId/runs/$newRunId" -Headers $commonHeaders
                $runStatus = ConvertFrom-Json $statusResp.Content
                if ($runStatus.required_action -and ($runStatus.required_action.type -like "*function*")) {
                    $rows += Add-Row $name "Tool call flow" "✅ PASS" "tool call triggered (requires_action)"
                } elseif ($runStatus.status -eq "completed") {
                    $rows += Add-Row $name "Tool call flow" "❌ FAIL" "no tool call (run completed)"
                } else {
                    $rows += Add-Row $name "Tool call flow" "❌ FAIL" "status=$($runStatus.status)"
                }
            } else {
                $rows += Add-Row $name "Tool call flow" "❌ FAIL" "run start status=$($runResp.StatusCode)"
            }
        } catch {
            $rows += Add-Row $name "Tool call flow" "❌ FAIL" ("error: " + $_.Exception.Message)
        }
    } else {
        $rows += Add-Row $name "Tool call flow" "⚠️ SKIP" "assistant or thread create failed"
    }
}

# Output results table with colored PASS/FAIL
Write-Host ("{0,-7}  {1,-30}  {2,-6}  {3}" -f "Target", "Check", "Result", "Details")
foreach ($row in $rows) {
    $t = $row.Target; $c = $row.Check; $r = $row.Result; $d = $row.Details
    $color = "White"
    if ($r -like "*PASS") { $color = "Green" }
    elseif ($r -like "*FAIL") { $color = "Red" }
    elseif ($r -like "*SKIP") { $color = "Yellow" }
    Write-Host ("{0,-7}  {1,-30}  " -f $t, $c) -NoNewline
    Write-Host ("$r") -ForegroundColor $color -NoNewline
    Write-Host ("  $d")
}
