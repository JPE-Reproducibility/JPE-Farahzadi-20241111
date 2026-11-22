* Figure: Estimated ethnic and religious endogamy preferences by religion
* Run from the replication-package root. Each target religion is coded 1;
* every other reported religion is coded 0 by By Religion.do.
args input_dta model_dir
if `"`input_dta'"' == "" local input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`model_dir'"' == "" local model_dir "Synthetic Data\model_out"
if `"`output_dir'"' == "" local output_dir "Paper\Output"

local model_code "Preparation\Model Engine\By Religion.do"
local path_separator = char(92)
capture confirm file "`input_dta'"
if _rc {
    display as error "Input data file not found: `input_dta'"
    exit 601
}
capture confirm file "`model_code'"
if _rc {
    display as error ///
        "Cannot find `model_code'. Run this script from the replication-package root."
    exit 601
}
capture mkdir "`model_dir'"
capture mkdir "`output_dir'"
local out_png "`output_dir'\Figure 5.png"

* Census 2011 religion codes: 6 Muslim, 4 Hindu, 7 Sikh, 2 Christian,
* and 1 no religion; code 9 (not stated) is excluded by the estimator.
local codes 6 4 7 2 1
local names `" "Muslim" "Hindu" "Sikh" "Christian" "No Religion" "'
local nrel : word count `codes'

forvalues j = 1/`nrel' {
    local c  : word `j' of `codes'
    local nm : word `j' of `names'
    local sub "`model_dir'`path_separator'`nm'"

    local need_estimation = 0
    foreach required_file in ///
        "Endogamy - `nm'.csv" ///
        "Estimated Preferences - `nm'.csv" ///
        "dist.dta" "phi.dta" "phi_er.dta" "d.dta" ///
        "muxy.dta" "lxy.dta" "lyx.dta" {
        capture confirm file "`sub'`path_separator'`required_file'"
        if _rc local need_estimation = 1
    }
    if `need_estimation' {
        noisily do "`model_code'" "`input_dta'" "`sub'" `c' "`nm'"
    }
    import delimited using "`sub'\Endogamy - `nm'.csv", clear varnames(1)
    if _N != 1 {
        display as error ///
            "Expected exactly one endogamy result row for `nm' in `sub'."
        exit 459
    }
    local re`j' "."
    local rs`j' "."
    local ee`j' "."
    local es`j' "."
    if !missing(rel_est[1], rel_se[1]) {
        local re`j' = rel_est[1]
        local rs`j' = 1.96*rel_se[1]
    }
    if !missing(eth_est[1], eth_se[1]) {
        local ee`j' = eth_est[1]
        local es`j' = 1.96*eth_se[1]
    }
}

clear
set obs `nrel'
generate byte j = _n
generate double xr = j - 0.2
generate double xe = j + 0.2
generate double rel_b = .
generate double rel_hi = .
generate double rel_lo = .
generate double eth_b = .
generate double eth_hi = .
generate double eth_lo = .
forvalues j = 1/`nrel' {
    if "`re`j''" != "." & "`rs`j''" != "." {
        replace rel_b  = `re`j''              in `j'
        replace rel_hi = `re`j'' + `rs`j''    in `j'
        replace rel_lo = `re`j'' - `rs`j''    in `j'
    }
    if "`ee`j''" != "." & "`es`j''" != "." {
        replace eth_b  = `ee`j''              in `j'
        replace eth_hi = `ee`j'' + `es`j''    in `j'
        replace eth_lo = `ee`j'' - `es`j''    in `j'
    }
}

twoway ///
    (bar rel_b xr, barwidth(0.35) color("153 194 230")) ///
    (rcap rel_hi rel_lo xr, lcolor(black)) ///
    (bar eth_b xe, barwidth(0.35) color("0 51 102")) ///
    (rcap eth_hi eth_lo xe, lcolor(black)), ///
    xlabel(1 "Muslim" 2 "Hindu" 3 "Sikh" 4 "Christian" 5 "No Religion", ///
        noticks) ///
    xscale(range(0.5 5.5)) ///
    ylabel(0(5)30, angle(horizontal) nogrid) yscale(range(0 30)) ///
    ytitle("Endogamy Preferences Parameter") xtitle("") ///
    legend(order(1 "Religious Endogamy" 3 "Ethnic Endogamy") ///
        rows(1) position(12) ring(1)) ///
    graphregion(color(white)) plotregion(margin(small))
graph export "`out_png'", width(2400) replace
display as text "Figure written to `out_png'"