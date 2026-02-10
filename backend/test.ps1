# OntoHub Backend Full Test Script

Write-Host "--- Start Backend Full Test ---" -ForegroundColor Cyan

# 1. Set environment to 'test' for isolation
$env:APP_ENV = "test"
Write-Host ">>> Test environment activated (APP_ENV=test)" -ForegroundColor Yellow

# 2. Cleanup cache
if (Test-Path "__pycache__") {
    Remove-Item -Recurse -Force "__pycache__"
}

# 3. Execute pytest
Write-Host ">>> Running pytest..." -ForegroundColor Green
pytest -v --cov=app --cov-report=term-missing tests/

# 4. Check result
if ($LASTEXITCODE -eq 0) {
    Write-Host ">>> [SUCCESS] All tests passed!" -ForegroundColor Green
} else {
    Write-Host ">>> [FAIL] Some tests failed. Check logs above." -ForegroundColor Red
}

# Restore environment
$env:APP_ENV = "development"
