* Appendix Table A15: Model Estimates with and without Geographic Restriction
* Limited geography keeps the East Midlands, West Midlands, East of England,
* Greater London and South East (region 4-8), as in
* Robustness - Geography\1 (observed matching.do and distributions.do).
* Otherwise the pipeline is the baseline one. England & Wales is the baseline.
* Migration decomposition uses the Figure 4 helper reused by Tables A7/A8.
* Pooled observed overall rates are the percentages reported in the paper:
* limited geography (22.7 non-Muslim, 52.0 Muslim) and baseline (21.7, 53.0).
* Run from the replication-package root.
* Usage:
* do "Online Appendix\L Heterogeneity\L3 Heterogeneity by Local Market Population\Code Table A15.do" ///
*   "cleaned_census.dta" "baseline_model_dir" "geography_model_dir" ///
*   "output_dir" ["python.exe"]
args input_dta baseline_dir geo_dir output_dir python_exe
if `"`input_dta'"' == "" local input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`baseline_dir'"' == "" local baseline_dir "Synthetic Data\model_out"
if `"`geo_dir'"' == "" local geo_dir "Synthetic Data\model_out\Table A15"
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
capture mkdir "`geo_dir'"
capture mkdir "`output_dir'"

use "`input_dta'", clear
keep if inrange(region, 4, 8)
save "`geo_dir'\data.dta", replace

noisily do "Paper\5 Results\Code Table 4.do" ///
    "`input_dta'" "`baseline_dir'" "`baseline_dir'" 6 "Muslim" 0
noisily do "Paper\5 Results\Code Table 4.do" ///
    "`geo_dir'\data.dta" "`geo_dir'" "`geo_dir'" 6 "Muslim" 0

* Weighted-average ethnic endogamy and the Religion contrast, by sample.
tempfile assembled weights
local first 1
foreach spec in geo baseline {
    local dir "`geo_dir'"
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
local migration_csv "`output_dir'\Table A15 migration.csv"
capture erase "`migration_csv'"
local baseline_non_muslim 21.7
local baseline_muslim 53.0
local geo_non_muslim 22.7
local geo_muslim 52.0
shell "`python_exe'" "Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration\table_a7_migration.py" ///
    --baseline-dir "`baseline_dir'" --sensitivity-dir "`geo_dir'" ///
    --output "`migration_csv'" ///
    --baseline-observed `baseline_non_muslim' `baseline_muslim' ///
    --sensitivity-observed `geo_non_muslim' `geo_muslim'
capture confirm file "`migration_csv'"
if _rc {
    display as error "Python migration decomposition did not produce: `migration_csv'"
    display as error "See the Python error above. The paper-reported pooled overall rates are supplied to the decomposition."
    exit 601
}

import delimited using "`migration_csv'", clear varnames(1)
replace specification = "geo" if specification == "sensitivity"
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
rename non_muslim0 geo_non_muslim
rename muslim0 geo_muslim
rename non_muslim1 england_wales_non_muslim
rename muslim1 england_wales_muslim
drop order
order section measure geo_non_muslim geo_muslim ///
    england_wales_non_muslim england_wales_muslim
export delimited using "`output_dir'\Table A15.csv", replace
erase "`migration_csv'"

display as result "Appendix Table A15 data written to `output_dir'\Table A15.csv"
