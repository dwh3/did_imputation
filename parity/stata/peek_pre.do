version 17.0
clear all
set more off

import delimited using "parity/out/dgpA_no_treat.csv", varnames(1) stringcols(_all) clear
adopath ++ "D:\dev\did-imputation-port\upstream\git"
destring y i t ei, replace force
rename ei Ei
rename y Y
rename i I
rename t T
did_imputation Y I T Ei, horizons(0/5) pretrends(3) autosample minn(0)
matrix list e(b)
