version 17.0
clear all
set more off

import delimited using "parity/out/dgpC_pretrend.csv", varnames(1) stringcols(_all) clear
destring y i t Ei, replace force
adopath ++ "D:\dev\did-imputation-port\upstream\git"

did_imputation y i t Ei, horizons(0/0) pretrends(3) autosample minn(0)

matrix list e(b)
matrix list e(Nt)
