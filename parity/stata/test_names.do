version 17.0
clear all
set more off

args in_csv out_csv y id t Ei kmin kmax scheme

import delimited using "`in_csv'", varnames(1) stringcols(_all) clear

local yname = "`y'"
local idname = "`id'"
local tname = "`t'"
local einame = "`Ei'"

noi display "yname=`yname' idname=`idname' tname=`tname' einame=`einame'"
foreach var in yname idname tname einame {
    local target = ``var''
    local lower = lower("`target'")
    noi display "checking target=`target' lower=`lower'"
    capture confirm variable `target'
    noi display "confirm target rc=" _rc
    if (_rc) {
        capture confirm variable `lower'
        noi display "confirm lower rc=" _rc
        if (!_rc) {
            rename `lower' `target'
        }
        else {
            display as error "variable `target' not found"
            exit 111
        }
    }
}
end
