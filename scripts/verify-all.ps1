Set-Location -LiteralPath "C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team"
$log = "$env:USERPROFILE\Desktop\run-all.txt"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"VERIFY ALL :: $ts" | Tee-Object -FilePath $log

"== RELAY ==" | Tee-Object -Append $log
powershell -ExecutionPolicy Bypass -File scripts\verify-relay.ps1 | Tee-Object -Append $log

"== ASSISTANTS ==" | Tee-Object -Append $log
powershell -ExecutionPolicy Bypass -File scripts\test-assistants.ps1 | Tee-Object -Append $log

"== FILES ==" | Tee-Object -Append $log
powershell -ExecutionPolicy Bypass -File scripts\test-files.ps1 | Tee-Object -Append $log

"== RESPONSES ==" | Tee-Object -Append $log
powershell -ExecutionPolicy Bypass -File scripts\test-responses.ps1 | Tee-Object -Append $log

"✅ Completed all tests. Output in: $log"
