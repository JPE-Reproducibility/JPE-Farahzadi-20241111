* Appendix Table A11: Sensitivity to the Treatment of Cohabitation.
*
* Build both analysis datasets from the raw Census CSV. The first links
* cohabiting partners (HPARTNER == 2, relationship code 3); the estimator
* treats linked cohabiters as non-single. The second uses legal marriage.
*
* Run from the replication-package root:
* do "Online Appendix\K Robustness to Cohabitation\Code Table A11.do" ///
*   "raw_census.csv" "work_dir" "output_dir" "python.exe"
args input_csv work_root output_dir python_exe
if `"`input_csv'"' == "" local input_csv "Synthetic Data\Census\synthetic_census_ew_2011.csv"
if `"`work_root'"' == "" local work_root "Synthetic Data\model_out\Table A11"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
if `"`python_exe'"' == "" local python_exe "python"

capture mkdir "`work_root'"
capture mkdir "`output_dir'"

local dta_marriage "`work_root'\data_cohab_marriage.dta"
local dta_single "`work_root'\data_cohab_single.dta"
local dir_marriage "`work_root'\cohabitation_as_marriage"
local dir_single "`work_root'\cohabitation_as_single"
local cleaner "Preparation\Data Cleaning\census_cleaning.py"

capture confirm file "`input_csv'"
if _rc {
    display as error "Raw Census CSV not found: `input_csv'"
    exit 601
}

* Generate the two samples with the same cleaner and age threshold.
capture erase "`dta_marriage'"
global a11_python `"`python_exe'"'
global a11_input_csv `"`input_csv'"'
global a11_output_dta `"`dta_marriage'"'
shell "$a11_python" "`cleaner'" --input-csv "$a11_input_csv" ///
    --output-dta "$a11_output_dta" --cohabitation-as-marriage
capture confirm file "`dta_marriage'"
if _rc {
    display as error "Cohabitation-as-marriage cleaning did not produce: `dta_marriage'"
    display as error "Check that the raw CSV includes HPARTNER and that Python can run census_cleaning.py."
    exit 601
}

capture erase "`dta_single'"
global a11_output_dta `"`dta_single'"'
shell "$a11_python" "`cleaner'" --input-csv "$a11_input_csv" ///
    --output-dta "$a11_output_dta"
capture confirm file "`dta_single'"
if _rc {
    display as error "Baseline cohabitation-as-single cleaning did not produce: `dta_single'"
    exit 601
}

capture mkdir "`dir_marriage'"
capture mkdir "`dir_single'"
noisily do "Paper\5 Results\Code Table 4.do" ///
    "`dta_marriage'" "`dir_marriage'" "`dir_marriage'" 6 "Muslim" 0 1
noisily do "Paper\5 Results\Code Table 4.do" ///
    "`dta_single'" "`dir_single'" "`dir_single'" 6 "Muslim" 0 0

foreach s in marriage single {
    foreach filename in "dist.dta" "d.dta" "phi.dta" "phi_er.dta" ///
        "muxy.dta" "lxy.dta" "lyx.dta" ///
        "Table 4 - Muslim.csv" "Ethnic weights - Muslim.csv" {
        capture confirm file "`dir_`s''/`filename'"
        if _rc {
            display as error "Table A11 `s' model did not produce required input: `dir_`s''/`filename'"
            exit 601
        }
    }
}

* Weighted-average ethnic endogamy and the Religion contrast, by treatment.
tempfile assembled weights
local first 1
foreach s in marriage single {
    import delimited using "`dir_`s''\Ethnic weights - Muslim.csv", clear varnames(1)
    save `weights', replace

    import delimited using "`dir_`s''\Table 4 - Muslim.csv", clear varnames(1)
    keep if category == "Ethnicity"
    gen ethnic_group = contrast_id - 4
    merge 1:1 ethnic_group using `weights', assert(match) nogen
    gen double non_muslim_term = estimate_other * weight_other
    gen double muslim_term = estimate_rel * weight_rel
    collapse (sum) non_muslim = non_muslim_term muslim = muslim_term
    gen str12 specification = "`s'"
    gen str12 measure = "ethnicity"
    tempfile eth_`s'
    save `eth_`s'', replace

    import delimited using "`dir_`s''\Table 4 - Muslim.csv", clear varnames(1)
    keep if category == "Religion"
    rename estimate_other non_muslim
    rename estimate_rel muslim
    keep non_muslim muslim
    gen str12 specification = "`s'"
    gen str12 measure = "religion"
    append using `eth_`s''
    if `first' == 0 append using `assembled'
    save `assembled', replace
    local first 0
}

tempfile endogamy
use `assembled', clear
save `endogamy'

local migration_csv "`work_root'\Table A11 migration.csv"
capture erase "`migration_csv'"
global a11_migration_csv `"`migration_csv'"'
shell "$a11_python" ///
    "Online Appendix\K Robustness to Cohabitation\table_a11_migration.py" ///
    --marriage-dir "`dir_marriage'" --single-dir "`dir_single'" ///
    --marriage-observed 19.6 51.3 --single-observed 21.7 53.0 ///
    --output "$a11_migration_csv"
capture confirm file "`migration_csv'"
if _rc {
    display as error "Python migration decomposition did not produce: `migration_csv'"
    display as error "Check the Python environment and the model inputs required by Figure 4."
    exit 601
}

import delimited using "`migration_csv'", clear varnames(1)
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

gen treated_as_single = specification == "single"
drop specification
reshape wide non_muslim muslim, i(order section measure) j(treated_as_single)
sort order
rename non_muslim0 cohab_marriage_non_muslim
rename muslim0 cohab_marriage_muslim
rename non_muslim1 cohab_single_non_muslim
rename muslim1 cohab_single_muslim
drop order
order section measure cohab_marriage_non_muslim cohab_marriage_muslim ///
    cohab_single_non_muslim cohab_single_muslim
export delimited using "`output_dir'\Table A11.csv", replace

display as result "Appendix Table A11 data written to `output_dir'\Table A11.csv"
