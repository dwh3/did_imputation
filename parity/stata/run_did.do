version 17.0
clear all
set more off

args in_csv out_csv y id t Ei kmin kmax scheme

local yname = lower("`y'")
local idname = lower("`id'")
local tname = lower("`t'")
local einame = lower("`Ei'")

import delimited using "`in_csv'", varnames(1) stringcols(_all) clear

destring `yname' `idname' `tname' `einame', replace force

adopath ++ "D:\dev\did-imputation-port\upstream\git"

local kmin_raw = "`kmin'"
local kmax_raw = "`kmax'"
local kmin_real = real("`kmin_raw'")
if missing(`kmin_real') {
    if substr("`kmin_raw'", 1, 1) == "/" {
        local kmin_real = -real(substr("`kmin_raw'", 2, .))
    }
}
local kmax_real = real("`kmax_raw'")
if missing(`kmax_real') {
    if substr("`kmax_raw'", 1, 1) == "/" {
        local kmax_real = -real(substr("`kmax_raw'", 2, .))
    }
}
if missing(`kmin_real') local kmin_real = 0
if missing(`kmax_real') local kmax_real = `kmin_real'

local pos_min = max(0, floor(`kmin_real'))
local pos_max = max(0, ceil(`kmax_real'))
local horizonopt ""
if (`kmax_real' >= 0) {
    local horizonopt "horizons(`pos_min'/`pos_max')"
}
local pre = 0
if (`kmin_real' < 0) local pre = round(-`kmin_real')
local preopt ""
if (`pre' > 0) local preopt "pretrends(`pre')"

local cmdopts "`horizonopt' `preopt' autosample minn(0)"

quietly did_imputation `yname' `idname' `tname' `einame', `cmdopts'

matrix b = e(b)
matrix V = e(V)
local names : colfullnames e(b)
local ntcols = 0
capture confirm matrix e(Nt)
if !_rc {
    matrix Nt = e(Nt)
    local ntcols = colsof(Nt)
}

tempname handle
tempfile tmp
postfile `handle' k estimate se n using `tmp', replace

local cols = colsof(b)
forvalues j = 1/`cols' {
    local name : word `j' of `names'
    local prefix = substr("`name'", 1, 3)
    if ("`prefix'" == "tau") {
        local kstr = substr("`name'", 4, .)
        if ("`kstr'" == "") local kval = 0
        else local kval = real("`kstr'")
        scalar est = b[1,`j']
        scalar var = V[`j',`j']
        scalar se = sqrt(var)
        scalar nobs = .
        if (`ntcols' >= `j') scalar nobs = Nt[1,`j']
        post `handle' (`kval') (est) (se) (nobs)
    }
    else if ("`prefix'" == "pre") {
        local kstr = substr("`name'", 4, .)
        local kval = -real("`kstr'")
        scalar est = b[1,`j']
        scalar var = V[`j',`j']
        scalar se = sqrt(var)
        scalar nobs = .
        post `handle' (`kval') (est) (se) (nobs)
    }
}
postclose `handle'

use `tmp', clear
sort k
export delimited using "`out_csv'", replace
