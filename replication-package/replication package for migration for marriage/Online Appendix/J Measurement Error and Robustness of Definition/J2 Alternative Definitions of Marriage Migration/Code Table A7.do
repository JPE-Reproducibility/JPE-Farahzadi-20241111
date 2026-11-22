* Appendix Table A7: Sensitivity to the Definition of Marriage Migration.
*
* Workflow: reuse the cleaned Census dataset and baseline model, estimate the
* exclude-UK-degree definition with the main Table 4 producer, then assemble
* A7. Only sadult_immig changes in the sensitivity estimation. The marriage-
* migration decomposition (overall, outside market value, endogamy
* preferences) uses the Figure 4 Python code via table_a7_migration.py.
*
* Run from the replication-package root:
* do "Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration\Code Table A7.do" ///
*   "cleaned_census.dta" "baseline_model_dir" "baseline_table_dir" ///
*   "model_root" "output_dir" "python_exe"
args cleaned_input_dta baseline_dir baseline_table_dir model_root output_dir python_exe
if `"`cleaned_input_dta'"' == "" local cleaned_input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`baseline_dir'"' == "" local baseline_dir "Synthetic Data\model_out"
if `"`baseline_table_dir'"' == "" local baseline_table_dir "Synthetic Data\model_out"
if `"`model_root'"' == "" local model_root "Synthetic Data\model_out\Table A7"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
if `"`python_exe'"' == "" local python_exe "python"

local sensitivity_dir "`model_root'\exclude_uk_degree"
capture mkdir "`model_root'"
capture mkdir "`output_dir'"
capture confirm file "`cleaned_input_dta'"
if _rc {
    display as error "Cleaned Census dataset not found: `cleaned_input_dta'"
    exit 601
}

foreach filename in "dist.dta" "d.dta" "phi.dta" "phi_er.dta" ///
    "muxy.dta" "lxy.dta" "lyx.dta" "Ethnic weights - Muslim.csv" {
    capture confirm file "`baseline_dir'/`filename'"
    if _rc {
        display as error "Baseline Table 4 input not found: `baseline_dir'/`filename'"
        exit 601
    }
}
capture confirm file "`baseline_table_dir'\Table 4 - Muslim.csv"
if _rc {
    display as error "Baseline Table 4 results not found: `baseline_table_dir'\Table 4 - Muslim.csv"
    exit 601
}

do "Paper\5 Results\Code Table 4.do" ///
    "`cleaned_input_dta'" "`sensitivity_dir'" "`sensitivity_dir'" 6 "Muslim" 1

foreach filename in "dist.dta" "d.dta" "phi.dta" "phi_er.dta" ///
    "muxy.dta" "lxy.dta" "lyx.dta" ///
    "Table 4 - Muslim.csv" "Ethnic weights - Muslim.csv" {
    capture confirm file "`sensitivity_dir'/`filename'"
    if _rc {
        display as error "Exclude-UK-degree Table 4 input not found: `sensitivity_dir'/`filename'"
        exit 601
    }
}
capture mkdir "`output_dir'"

* Marriage-migration decomposition from the Figure 4 code.
local rates_csv "`model_root'\a7_migration_rates.csv"
capture erase "`rates_csv'"
local py_script "Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration\table_a7_migration.py"
* Observed percentages pooled across women and men, by definition and religion.
local baseline_non_muslim 21.74
local baseline_muslim 52.97
local sensitivity_non_muslim 18.02
local sensitivity_muslim 49.79
shell "`python_exe'" "`py_script'" --baseline-dir "`baseline_dir'" --sensitivity-dir "`sensitivity_dir'" --output "`rates_csv'" --baseline-observed `baseline_non_muslim' `baseline_muslim' --sensitivity-observed `sensitivity_non_muslim' `sensitivity_muslim'
capture confirm file "`rates_csv'"
if _rc {
    display as error "Python decomposition did not produce `rates_csv'. See the Python error above."
    exit 601
}

tempfile rates_baseline rates_sensitivity endogamy
import delimited using "`rates_csv'", clear varnames(1)
keep if specification == "baseline"
save "`rates_baseline'", replace
import delimited using "`rates_csv'", clear varnames(1)
keep if specification == "sensitivity"
save "`rates_sensitivity'", replace

local first 1
foreach spec in sensitivity baseline {
    local dir "`sensitivity_dir'"
    local results_dir "`sensitivity_dir'"
    if "`spec'" == "baseline" {
        local dir "`baseline_dir'"
        local results_dir "`baseline_table_dir'"
    }
    import delimited using "`dir'\Ethnic weights - Muslim.csv", clear varnames(1)
    tempfile weights
    save `weights', replace

    import delimited using "`results_dir'\Table 4 - Muslim.csv", clear varnames(1)
    keep if category == "Ethnicity"
    gen ethnic_group = contrast_id - 4
    merge 1:1 ethnic_group using `weights', assert(match) nogen
    gen double non_muslim_term = estimate_other * weight_other
    gen double muslim_term = estimate_rel * weight_rel
    collapse (sum) non_muslim = non_muslim_term muslim = muslim_term
    gen str12 specification = "`spec'"
    gen str12 measure = "ethnicity"
    tempfile ethnic_`spec'
    save `ethnic_`spec'', replace

    import delimited using "`results_dir'\Table 4 - Muslim.csv", clear varnames(1)
    keep if category == "Religion"
    rename estimate_other non_muslim
    rename estimate_rel muslim
    keep non_muslim muslim
    gen str12 specification = "`spec'"
    gen str12 measure = "religion"
    append using `ethnic_`spec''
    if `first' == 1 {
        save `endogamy', replace
        local first 0
    }
    else {
        append using `endogamy'
        save `endogamy', replace
    }
}

use `rates_baseline', clear
append using `rates_sensitivity'
rename overall m_overall
rename outside_market_value m_outside
rename endogamy_preferences m_endogamy
reshape long m_, i(specification religion) j(measure) string
replace religion = lower(subinstr(religion, "-", "_", .))
reshape wide m_, i(specification measure) j(religion) string
rename m_non_muslim non_muslim
rename m_muslim muslim

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
reshape wide non_muslim muslim, i(order section measure) j(spec_order)
rename non_muslim0 excl_uk_degree_non_muslim
rename muslim0 excl_uk_degree_muslim
rename non_muslim1 baseline_non_muslim
rename muslim1 baseline_muslim

tempfile migration
save `migration', replace

use `endogamy', clear
gen order = cond(measure == "ethnicity", 1, 2)
gen section = "Endogamy preferences"
replace measure = "Ethnicity" if measure == "ethnicity"
replace measure = "Religion" if measure == "religion"
gen spec_order = specification == "baseline"
drop specification
reshape wide non_muslim muslim, i(order section measure) j(spec_order)
rename non_muslim0 excl_uk_degree_non_muslim
rename muslim0 excl_uk_degree_muslim
rename non_muslim1 baseline_non_muslim
rename muslim1 baseline_muslim
append using `migration'
sort order
drop order
order section measure excl_uk_degree_non_muslim excl_uk_degree_muslim ///
    baseline_non_muslim baseline_muslim
export delimited using "`output_dir'\Table A7.csv", replace
display as result "Appendix Table A7 data written to `output_dir'\Table A7.csv"
