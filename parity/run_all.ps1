param(
  [string]$StataExe = $env:STATA_EXE
)

if (-not $StataExe -or -not (Test-Path $StataExe)) {
  Write-Host "ERROR: Set STATA_EXE to your Stata console binary path." -ForegroundColor Red
  exit 1
}

Set-Location D:\dev\did-imputation-port
.\.venv\Scripts\Activate.ps1

# 6.1 generate CSVs
python parity\python\make_csvs.py

# 6.2 scenarios
$cases = @(
  @{name="dgpA_no_treat"; kmin=-3; kmax=5; scheme="nobs"},
  @{name="dgpB_const_te"; kmin=0;  kmax=3; scheme="nobs"},
  @{name="dgpB_const_te"; kmin=0;  kmax=3; scheme="equal"},
  @{name="dgpB_const_te"; kmin=0;  kmax=3; scheme="cohort_share"},
  @{name="dgpC_pretrend"; kmin=-3; kmax=0; scheme="nobs"}
)

foreach ($c in $cases) {
  $in  = "parity/out/$($c.name).csv"
  $sout = "parity/out/$($c.name)_stata_$($c.scheme)_$($c.kmin)_$($c.kmax).csv"
  $pout = "parity/out/$($c.name)_py_$($c.scheme)_$($c.kmin)_$($c.kmax).csv"

  & $StataExe /e do "parity/stata/run_did.do" $in $sout Y i t Ei $($c.kmin) $($c.kmax) $($c.scheme)

  python parity\python\run_py.py $in $pout Y i t Ei $($c.kmin) $($c.kmax) $($c.scheme)
}

# 6.3 compare and report
python parity\python\compare.py

Write-Host "Done. See parity/out/PARITY_REPORT.md" -ForegroundColor Green
