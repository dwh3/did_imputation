version 17.0
clear all
set more off

args in_csv out_csv y id t Ei kmin kmax scheme
import delimited using "`in_csv'", varnames(1) stringcols(_all) clear
describe
list in 1/5
