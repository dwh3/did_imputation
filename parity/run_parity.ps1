$env:STATA_EXE = "$Env:STATA_EXE" # if already set, keep it
if (-not $env:STATA_EXE -or -not (Test-Path $env:STATA_EXE)) {
  Write-Host "Set STATA_EXE to your Stata console binary path, e.g.:" -ForegroundColor Yellow
  Write-Host '$env:STATA_EXE = "C:\Program Files\Stata18\StataMP-64.exe"' -ForegroundColor Yellow
}
