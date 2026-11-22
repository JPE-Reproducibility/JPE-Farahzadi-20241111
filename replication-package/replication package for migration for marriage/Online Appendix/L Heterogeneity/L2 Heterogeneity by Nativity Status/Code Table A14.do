* Appendix Table A14: Comparison of Results by Nativity Status
* "UK-born" restricts residents to people born in the UK and counts any
* foreign-born same-ethnicity spouse as a marriage migrant, using simmigrant.
* "UK-born or bred" is the baseline sample.
* Code Table 4.do reads simmigrant18, so for the UK-born run simmigrant18 is
* set to simmigrant. Migration rates use the Figure 4 decomposition helper.
* Pooled observed overall rates are the percentages reported in the paper:
* UK-born (23.7 non-Muslim, 61.1 Muslim) and baseline (21.7, 53.0).
* Run from the replication-package root.
* Usage:
* do "Online Appendix\L Heterogeneity\L2 Heterogeneity by Nativity Status\Code Table A14.do" ///
*   "cleaned_census.dta" "baseline_model_dir" "ukborn_model_dir" ///
*   "output_dir" ["python.exe"]
args input_dta baseline_dir ukborn_dir output_dir python_exe
if `"`input_dta'"' == "" local input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`baseline_dir'"' == "" local baseline_dir "Synthetic Data\model_out"
if `"`ukborn_dir'"' == "" local ukborn_dir "Synthetic Data\model_out\Table A14"
if `"`output_dir'"' == "" {
    local output_dir "Online Appendix\Output"
}
if `"`python_exe'"' == "" local python_exe "python"

capture confirm file `"`input_dta'"'
if _rc {
    display as error "Cleaned Census data not found: `input_dta'"
    exit 601
}
capture mkdir "`baseline_dir'"
capture mkdir "`ukborn_dir'"
capture mkdir "`output_dir'"

use "`input_dta'", clear
keep if ukborn == 1
replace simmigrant18 = simmigrant
save "`ukborn_dir'\data.dta", replace

noisily do "Paper\5 Results\Code Table 4.do" ///
    "`input_dta'" "`baseline_dir'" "`baseline_dir'" 6 "Muslim" 0
noisily do "Paper\5 Results\Code Table 4.do" ///
    "`ukborn_dir'\data.dta" "`ukborn_dir'" "`ukborn_dir'" 6 "Muslim" 0

* Weighted-average ethnic endogamy and the Religion contrast, by sample.
tempfile assembled weights
local first 1
foreach spec in ukborn baseline {
    local dir "`ukborn_dir'"
    if "`spec'" == "baseline" local dir "`baseline_dir'"

    import delimited using "`dir'\Ethnic weights - Muslim.csv", clear varnames(1)
    save `weights', replace

    import delimited using "`dir'\Table 4 - Muslim.csv", clear varnames(1)
    keep if category == "Ethnicity"
    gen ethnic_group = contrast_id - 4
    merge 1:1 ethnic_group using `weights', assert(match) nogen
    gen double non_muslim_term = estimate_other * weight_other
    gen double muslim_term = estimate_rel * weight_rel
    collapse (sum) non_muslim = non_muslim_term muslim = muslim_term
    gen str12 specification = "`spec'"
    gen str12 measure = "ethnicity"
    tempfile eth_`spec'
    save `eth_`spec'', replace

    import delimited using "`dir'\Table 4 - Muslim.csv", clear varnames(1)
    keep if category == "Religion"
    rename estimate_other non_muslim
    rename estimate_rel muslim
    keep non_muslim muslim
    gen str12 specification = "`spec'"
    gen str12 measure = "religion"
    append using `eth_`spec''
    if `first' == 0 append using `assembled'
    save `assembled', replace
    local first 0
}

tempfile endogamy
use `assembled', clear
save `endogamy'

* Migration decomposition uses the same Figure 4 calculation as Tables A7/A8.
local migration_csv "`output_dir'\Table A14 migration.csv"
capture erase "`migration_csv'"
local baseline_non_muslim 21.7
local baseline_muslim 53.0
local ukborn_non_muslim 23.7
local ukborn_muslim 61.1
shell "`python_exe'" "Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration\table_a7_migration.py" ///
    --baseline-dir "`baseline_dir'" --sensitivity-dir "`ukborn_dir'" ///
    --output "`migration_csv'" ///
    --baseline-observed `baseline_non_muslim' `baseline_muslim' ///
    --sensitivity-observed `ukborn_non_muslim' `ukborn_muslim'
capture confirm file "`migration_csv'"
if _rc {
    display as error "Python migration decomposition did not produce: `migration_csv'"
    display as error "See the Python error above. The paper-reported pooled overall rates are supplied to the decomposition."
    exit 601
}

import delimited using "`migration_csv'", clear varnames(1)
replace specification = "ukborn" if specification == "sensitivity"
rename overall m_overall
rename outside_market_value m_outside
rename endogamy_preferences m_endogamy
reshape long m_, i(specification religion) j(measure) string
replace religion = lower(subinstr(religion, "-", "_", .))
reshape wide m_, i(specification measure) j(religion) string
rename m_non_muslim non_muslim
rename m_muslim muslim
append using `endogamy'

gen order = .
replace order = 1 if measure == "ethnicity"
replace order = 2 if measure == "religion"
replace order = 3 if measure == "overall"
replace order = 4 if measure == "outside"
replace order = 5 if measure == "endogamy"
gen section = cond(order <= 2, "Endogamy preferences", "Marriage migration (%)")
replace measure = "Ethnicity" if measure == "ethnicity"
replace measure = "Religion" if measure == "religion"
replace measure = "Overall" if measure == "overall"
replace measure = "Outside market value" if measure == "outside"
replace measure = "Endogamy preferences" if measure == "endogamy"

gen spec_order = specification == "baseline"
drop specification
sort order spec_order
reshape wide non_muslim muslim, i(order section measure) j(spec_order)
rename non_muslim0 ukborn_non_muslim
rename muslim0 ukborn_muslim
rename non_muslim1 ukborn_or_bred_non_muslim
rename muslim1 ukborn_or_bred_muslim
drop order
order section measure ukborn_non_muslim ukborn_muslim ///
    ukborn_or_bred_non_muslim ukborn_or_bred_muslim
export delimited using "`output_dir'\Table A14.csv", replace
erase "`migration_csv'"

display as result "Appendix Table A14 data written to `output_dir'\Table A14.csv"
