param(
    [int]$WarmupIterations = 3,
    [int]$MeasuredIterations = 10
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$benchmarkRoot = Join-Path $repositoryRoot "benchmarks/analysis-models"
$virtualEnvironment = Join-Path $benchmarkRoot ".venv"
$python = Join-Path $virtualEnvironment "Scripts/python.exe"
$cacheRoot = Join-Path $benchmarkRoot ".cache"
$downloadsRoot = Join-Path $benchmarkRoot "downloads"
$generatedRoot = Join-Path $benchmarkRoot "generated"
$resultsRoot = Join-Path $benchmarkRoot "results"

if (-not (Test-Path -LiteralPath $python)) {
    python -m venv $virtualEnvironment
}

& $python -m pip install --disable-pip-version-check -r (Join-Path $benchmarkRoot "requirements.txt")

New-Item -ItemType Directory -Force -Path $cacheRoot, $downloadsRoot, $generatedRoot, $resultsRoot | Out-Null

$env:HF_HOME = Join-Path $cacheRoot "huggingface"
$env:HF_HUB_DISABLE_TELEMETRY = "1"
$env:TRANSFORMERS_NO_ADVISORY_WARNINGS = "1"
$env:TOKENIZERS_PARALLELISM = "false"

& $python (Join-Path $benchmarkRoot "export_onnx.py") `
    --cache-dir $cacheRoot `
    --downloads-dir $downloadsRoot `
    --generated-dir $generatedRoot `
    --results-dir $resultsRoot

& $python (Join-Path $benchmarkRoot "verify_outputs.py") `
    --metadata (Join-Path $resultsRoot "export-results.json") `
    --messages (Join-Path $benchmarkRoot "test_messages.json") `
    --results (Join-Path $resultsRoot "verification-results.json")

& $python (Join-Path $benchmarkRoot "benchmark.py") `
    --metadata (Join-Path $resultsRoot "export-results.json") `
    --results-json (Join-Path $resultsRoot "benchmark-results.json") `
    --results-csv (Join-Path $resultsRoot "benchmark-results.csv") `
    --warmup-iterations $WarmupIterations `
    --measured-iterations $MeasuredIterations

Write-Host "Benchmark completed."
Write-Host "Raw results: $resultsRoot"
Write-Host "Review and update benchmarks/analysis-models/BENCHMARK_REPORT.md before committing."
