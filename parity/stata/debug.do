log using "D:\dev\did-imputation-port\parity\out\debug.log", replace text
import delimited using "parity/out/dgpB_const_te.csv", varnames(1) stringcols(_all) clear
destring t Ei, replace force
adopath ++ "D:\dev\did-imputation-port\upstream\git"
did_imputation Y i t Ei, horizons(0/3)
ereturn list
matrix list e(b)
matrix list e(Nt)
log close
