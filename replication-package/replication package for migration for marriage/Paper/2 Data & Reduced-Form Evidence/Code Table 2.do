* Main-text Table 2: Educational Sorting in Marriage Migration (LPM).
* Output: Paper\Output\Table 2.csv.
* The regression sample is ethnic minorities.
* Controls: Ethnicity, age, region.

args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Paper\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear
keep if ethnicityew != 1 & !missing(ethnicityew)

tempfile table
tempname results
postfile `results' str20 specification str24 outcome str32 term ///
    byte sex byte muslim double estimate standard_error statistic p_value ///
    r_squared long observations using `table', replace

forvalues sex_id = 1/2 {
    forvalues muslim_id = 0/1 {
        quietly regress tertiary_edu sadult_immig i.ethnic_group i.age_group i.region ///
            if sex == `sex_id' & muslim == `muslim_id'
        local estimate = .
        local se = .
        local statistic = .
        local p = .
        capture local estimate = _b[sadult_immig]
        if !_rc local se = _se[sadult_immig]
        if !missing(`se') & `se' > 0 {
            local statistic = `estimate' / `se'
            local p = 2 * ttail(e(df_r), abs(`statistic'))
        }
        else {
            local estimate = .
            local se = .
        }
        local r2 = e(r2)
        local n = e(N)
        post `results' ("Paper specification") ("College education") ///
            ("Marriage migration") (`sex_id') (`muslim_id') (`estimate') ///
            (`se') (`statistic') (`p') (`r2') (`n')
    }
}

postclose `results'
use `table', clear
gsort -muslim sex
label define sex_label 1 "Male" 2 "Female"
label values sex sex_label
label define religion_label 0 "Non-Muslim" 1 "Muslim"
label values muslim religion_label
order specification outcome term sex muslim estimate standard_error statistic p_value r_squared observations
export delimited using "`output_dir'\Table 2.csv", replace
display as result "Main-text Table 2 data saved to: `output_dir'\Table 2.csv"
