* Main-text Table 3: Educational Trade-offs in Marriage Migration.
* Output: Paper\Output\Table 3.csv.
* The implemented controls are own education, ethnicity, age group and region.
args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Paper\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear
keep if ethnicityew != 1 & !missing(ethnicityew) & !missing(coupleid)

tempfile table
tempname results
postfile `results' str20 specification str32 outcome str40 term ///
    byte sex byte muslim double estimate standard_error statistic p_value ///
    r_squared long observations using `table', replace

forvalues sex_id = 1/2 {
    forvalues muslim_id = 0/1 {
        quietly regress stertiary_edu i.sadult_immig##i.tertiary_edu ///
            i.ethnic_group i.age_group i.region ///
            if sex == `sex_id' & muslim == `muslim_id'
        local r2 = e(r2)
        local n = e(N)
        foreach term in "1.sadult_immig" "1.tertiary_edu" ///
            "1.sadult_immig#1.tertiary_edu" {
            local estimate = .
            local se = .
            local statistic = .
            local p = .
            capture local estimate = _b[`term']
            if !_rc local se = _se[`term']
            if !missing(`se') & `se' > 0 {
                local statistic = `estimate' / `se'
                local p = 2 * ttail(e(df_r), abs(`statistic'))
            }
            else {
                local estimate = .
                local se = .
            }
            local term_label "Marriage migration"
            if "`term'" == "1.tertiary_edu" local term_label "College education"
            if "`term'" == "1.sadult_immig#1.tertiary_edu" ///
                local term_label "Marriage migration x college education"
            post `results' ("Paper specification") ("Spouse college education") ///
                ("`term_label'") (`sex_id') (`muslim_id') (`estimate') (`se') ///
                (`statistic') (`p') (`r2') (`n')
        }
    }
}

postclose `results'
use `table', clear
gen byte term_order = 1 if term == "Marriage migration"
replace term_order = 2 if term == "College education"
replace term_order = 3 if term == "Marriage migration x college education"
gsort -muslim sex term_order
drop term_order
label define sex_label 1 "Male" 2 "Female"
label values sex sex_label
label define religion_label 0 "Non-Muslim" 1 "Muslim"
label values muslim religion_label
order specification outcome term sex muslim estimate standard_error statistic p_value r_squared observations
export delimited using "`output_dir'\Table 3.csv", replace
display as result "Main-text Table 3 data saved to: `output_dir'\Table 3.csv"
