* Appendix Table A8: Sensitivity to the Age Threshold Used to Define
* Marriage Migration.
*
* End-to-end workflow: reuse the age-18 baseline model, clean the raw Census
* CSV at age thresholds 16 and 20, estimate those two models, then assemble
* A8. Intermediate datasets and model outputs are retained under model_root.
* The marriage-migration decomposition (overall, outside market value,
* endogamy preferences) uses the Figure 4 Python code via
* table_a8_migration.py.
*
* Run from the replication-package root:
* do "Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration\Code Table A8.do" ///
*   "raw_census.csv" "baseline_model_dir" "baseline_table_dir" ///
*   "model_root" "output_dir" "python.exe"
args input_csv baseline_dir baseline_table_dir model_root output_dir python_exe
if `"`input_csv'"' == "" local input_csv "Synthetic Data\Census\synthetic_census_ew_2011.csv"
if `"`baseline_dir'"' == "" local baseline_dir "Synthetic Data\model_out"
if `"`baseline_table_dir'"' == "" local baseline_table_dir "Synthetic Data\model_out"
if `"`model_root'"' == "" local model_root "Synthetic Data\model_out\Table A8"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
if `"`python_exe'"' == "" local python_exe "python"
capture mkdir "`model_root'"
capture mkdir "`output_dir'"
local dir16 "`model_root'\age16"
local dir18 "`baseline_dir'"
local dir20 "`model_root'\age20"
capture confirm file "`input_csv'"
if _rc {
    display as error "Raw Census CSV not found: `input_csv'"
    exit 601
}

foreach filename in "dist.dta" "d.dta" "phi.dta" "phi_er.dta" ///
    "muxy.dta" "lxy.dta" "lyx.dta" "Ethnic weights - Muslim.csv" {
    capture confirm file "`dir18'/`filename'"
    if _rc {
        display as error "Baseline age-18 Table 4 input not found: `dir18'/`filename'"
        exit 601
    }
}
capture confirm file "`baseline_table_dir'\Table 4 - Muslim.csv"
if _rc {
    display as error "Baseline age-18 Table 4 results not found: `baseline_table_dir'\Table 4 - Muslim.csv"
    exit 601
}

foreach threshold in 16 20 {
    local cleaned_dta "`model_root'\cleaned_age`threshold'.dta"
    local modeldir "`dir`threshold''"
    global a8_python `"`python_exe'"'
    global a8_input_csv `"`input_csv'"'
    global a8_cleaned_dta `"`cleaned_dta'"'
    capture erase "`cleaned_dta'"
    shell "$a8_python" "Preparation\Data Cleaning\census_cleaning.py" ///
        --input-csv "$a8_input_csv" --output-dta "$a8_cleaned_dta" ///
        --age-threshold `threshold'
    capture confirm file "`cleaned_dta'"
    if _rc {
        display as error "Census cleaning did not produce the required dataset: `cleaned_dta'"
        exit 601
    }
    do "Paper\5 Results\Code Table 4.do" ///
        "`cleaned_dta'" "`modeldir'" "`modeldir'" 6 "Muslim" 0
}

foreach threshold in 16 20 {
    local modeldir "`dir`threshold''"
    foreach filename in "dist.dta" "d.dta" "phi.dta" "phi_er.dta" ///
        "muxy.dta" "lxy.dta" "lyx.dta" ///
        "Table 4 - Muslim.csv" "Ethnic weights - Muslim.csv" {
        capture confirm file "`modeldir'/`filename'"
        if _rc {
            display as error "Age-`threshold' Table 4 input not found: `modeldir'/`filename'"
            exit 601
        }
    }
}

* Marriage-migration decomposition from the Figure 4 code.
local rates_csv "`model_root'\a8_migration_rates.csv"
capture erase "`rates_csv'"
local py_script "Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration\table_a8_migration.py"
* Observed percentages pooled across women and men, by threshold and religion.
local non_muslim16 22.11
local muslim16 58.13
local non_muslim18 21.74
local muslim18 52.97
local non_muslim20 20.60
local muslim20 39.54
shell "`python_exe'" "`py_script'" --dir16 "`dir16'" --dir18 "`dir18'" --dir20 "`dir20'" --output "`rates_csv'" --observed16 `non_muslim16' `muslim16' --observed18 `non_muslim18' `muslim18' --observed20 `non_muslim20' `muslim20'
capture confirm file "`rates_csv'"
if _rc {
    display as error "Python decomposition did not produce `rates_csv'. See the Python error above."
    exit 601
}

tempfile rates16 rates18 rates20 endogamy
import delimited using "`rates_csv'", clear varnames(1)
foreach threshold in 16 18 20 {
    preserve
    keep if specification == "t`threshold'"
    save "`rates`threshold''", replace
    restore
}

local first 1
foreach threshold in 16 18 20 {
    local dir "`dir`threshold''"
    local resultsdir "`dir'"
    if `threshold' == 18 local resultsdir "`baseline_table_dir'"
    import delimited using "`dir'\Ethnic weights - Muslim.csv", clear varnames(1)
    tempfile weights
    save `weights', replace

    import delimited using "`resultsdir'\Table 4 - Muslim.csv", clear varnames(1)
    keep if category == "Ethnicity"
    gen ethnic_group = contrast_id - 4
    merge 1:1 ethnic_group using `weights', assert(match) nogen
    gen double non_muslim_term = estimate_other * weight_other
    gen double muslim_term = estimate_rel * weight_rel
    collapse (sum) non_muslim = non_muslim_term muslim = muslim_term
    gen str12 specification = "t`threshold'"
    gen str12 measure = "ethnicity"
    tempfile ethnic_`threshold'
    save `ethnic_`threshold'', replace

    import delimited using "`resultsdir'\Table 4 - Muslim.csv", clear varnames(1)
    keep if category == "Religion"
    rename estimate_other non_muslim
    rename estimate_rel muslim
    keep non_muslim muslim
    gen str12 specification = "t`threshold'"
    gen str12 measure = "religion"
    append using `ethnic_`threshold''
    if `first' == 1 {
        save `endogamy', replace
        local first 0
    }
    else {
        append using `endogamy'
        save `endogamy', replace
    }
}

use `rates16', clear
append using `rates18'
append using `rates20'
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
gen threshold = real(substr(specification, 2, .))
drop specification
reshape wide non_muslim muslim, i(order section measure) j(threshold)
foreach threshold in 16 18 20 {
    rename non_muslim`threshold' threshold`threshold'_non_muslim
    rename muslim`threshold' threshold`threshold'_muslim
}

tempfile migration
save `migration', replace

use `endogamy', clear
gen order = cond(measure == "ethnicity", 1, 2)
gen section = "Endogamy preferences"
replace measure = "Ethnicity" if measure == "ethnicity"
replace measure = "Religion" if measure == "religion"
gen threshold = real(substr(specification, 2, .))
drop specification
reshape wide non_muslim muslim, i(order section measure) j(threshold)
foreach threshold in 16 18 20 {
    rename non_muslim`threshold' threshold`threshold'_non_muslim
    rename muslim`threshold' threshold`threshold'_muslim
}
append using `migration'
sort order
drop order
order section measure threshold16_non_muslim threshold16_muslim ///
    threshold18_non_muslim threshold18_muslim ///
    threshold20_non_muslim threshold20_muslim
export delimited using "`output_dir'\Table A8.csv", replace
display as result "Appendix Table A8 data written to `output_dir'\Table A8.csv"
