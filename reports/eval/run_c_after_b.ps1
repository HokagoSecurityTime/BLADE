$ErrorActionPreference = 'Stop'
$metricsPath = 'C:\BLADE\reports\eval\b_qwen2.5_7b_v2.0_2026-10-20_metrics.json'
while ($true) {
    if (Test-Path -LiteralPath $metricsPath) {
        $metrics = Get-Content -LiteralPath $metricsPath -Raw | ConvertFrom-Json
        if ($metrics.state -eq 'complete') { break }
        if ($metrics.state -eq 'blocked_provider_errors') {
            'b provider errors; attempting independent RAG-off configuration c' | Set-Content -LiteralPath 'C:\BLADE\reports\eval\baseline_c.queued_status.txt'
            break
        }
    }
    Start-Sleep -Seconds 15
}
Set-Location -LiteralPath 'C:\BLADE'
& 'C:\BLADE\.python\python.exe' -m scripts.eval_classifier --configuration c --test-sha256 bd22c2580c2ddc2154974f76aa9e7aa2ca30bc6f8434e4960f3d3966093977fa
