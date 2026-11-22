* Table A4: Estimated Endogamy Preferences by Religious Group
* Run from the replication-package root.
* Usage: do "Online Appendix\A Appendix Figures & Tables\A2 Tables\Code Table A4.do" ///
*   "data.dta" "model_dir" "output_dir"
args input_dta model_dir output_dir
if `"`input_dta'"' == "" local input_dta 
if `"`model_dir'"' == "" local model_dir "Synthetic Data\model_out"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
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

* Religion codes in the 2011 England and Wales Census; code 9 (not stated)
* is excluded by the model.
local codes 6 4 7 2 1
local names `" "Muslim" "Hindu" "Sikh" "Christian" "No Religion" "'
local nrel : word count `codes'

* ---- Step 1: estimate by religion and collect results ----
forvalues j = 1/`nrel' {
    local c  : word `j' of `codes'
    local nm : word `j' of `names'
    local sub "`model_dir'`path_separator'`nm'"

    forvalues i = 1/9 {
        local est_`i'_`j' "."
        local se_`i'_`j'  "."
    }

    display as text _n "=== Estimating: `nm' (religion == `c') ==="
    local need_estimation = 0
    foreach required_file in ///
        "Endogamy - `nm'.csv" ///
        "Estimated Preferences - `nm'.csv" ///
        "dist.dta" "phi_er.dta" "d.dta" ///
        "muxy.dta" "lxy.dta" "lyx.dta" {
        capture confirm file "`sub'`path_separator'`required_file'"
        if _rc local need_estimation = 1
    }
    if `need_estimation' {
        noisily do "`model_code'" "`input_dta'" "`sub'" `c' "`nm'"
    }
    import delimited using "`sub'\Estimated Preferences - `nm'.csv", clear varnames(1)
    forvalues i = 1/9 {
        quietly summarize estimate_rel if contrast_id == `i', meanonly
        if r(N) > 0 local est_`i'_`j' = r(mean)
        quietly summarize se_rel if contrast_id == `i', meanonly
        if r(N) > 0 local se_`i'_`j' = r(mean)
    }
}

* Export the same religion-specific estimates in machine-readable form.
tempfile table_a4_data
tempname table_a4_post
postfile `table_a4_post' ///
    int contrast_id str12 category str48 comparison ///
    double Muslim_estimate Muslim_se ///
    double Hindu_estimate Hindu_se ///
    double Sikh_estimate Sikh_se ///
    double Christian_estimate Christian_se ///
    double NoReligion_estimate NoReligion_se ///
    using `table_a4_data', replace

forvalues i = 1/9 {
    local category "Age"
    if `i' == 4 local category "Education"
    if inrange(`i', 5, 8) local category "Ethnicity"
    if `i' == 9 local category "Religion"

    local comparison ""
    if `i' == 1 local comparison "Young and Middle-aged"
    if `i' == 2 local comparison "Young and Old"
    if `i' == 3 local comparison "Middle-aged and Old"
    if `i' == 4 local comparison "Less than college and College or more"
    if `i' == 5 local comparison "Other White and White British"
    if `i' == 6 local comparison "Indian and White British"
    if `i' == 7 local comparison "Pakistani/Bangladeshi and White British"
    if `i' == 8 local comparison "Other and White British"
    if `i' == 9 local comparison "Different religions"

    post `table_a4_post' (`i') ("`category'") ("`comparison'") ///
        (real("`est_`i'_1'")) (real("`se_`i'_1'")) ///
        (real("`est_`i'_2'")) (real("`se_`i'_2'")) ///
        (real("`est_`i'_3'")) (real("`se_`i'_3'")) ///
        (real("`est_`i'_4'")) (real("`se_`i'_4'")) ///
        (real("`est_`i'_5'")) (real("`se_`i'_5'"))
}
postclose `table_a4_post'

preserve
use `table_a4_data', clear
export delimited using "`output_dir'\Table A4.csv", replace
restore

display as result _n "Table A4 CSV saved to: `output_dir'\Table A4.csv"