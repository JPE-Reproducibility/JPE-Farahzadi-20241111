* Online Appendix Table A2: Age Trade-offs in Marriage Migration.
* Controls: Ethnicity, age, region
.
args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear
keep if ethnicityew != 1 & !missing(ethnicityew) & !missing(coupleid)

tempfile table
tempname results
postfile `results' str12 specification str20 outcome str32 term ///
    byte sex byte muslim double estimate standard_error statistic p_value ///
    r_squared long observations using `table', replace

forvalues sex_id = 1/2 {
    forvalues muslim_id = 0/1 {
        foreach specification in baseline adjusted {
            if "`specification'" == "baseline" {
                quietly regress sage sadult_immig age  ///
                    if sex == `sex_id' & muslim == `muslim_id'
            }
            else {
                quietly regress sage sadult_immig age  ///
                    i.ethnic_group i.age_group i.region ///
                    if sex == `sex_id' & muslim == `muslim_id'
            }
            local r2 = e(r2)
            local n = e(N)
            foreach term in sadult_immig age {
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
                if "`term'" == "age" local term_label "Age"
                post `results' ("`specification'") ("Spouse age") ///
                    ("`term_label'") (`sex_id') (`muslim_id') (`estimate') ///
                    (`se') (`statistic') (`p') (`r2') (`n')
            }
        }
    }
}

postclose `results'
use `table', clear
gen byte specification_order = 1 if specification == "baseline"
replace specification_order = 2 if specification == "adjusted"
gen byte term_order = 1 if term == "Marriage migration"
replace term_order = 2 if term == "Age"
gsort -muslim sex specification_order term_order
drop specification_order term_order
label define sex_label 1 "Male" 2 "Female"
label values sex sex_label
label define religion_label 0 "Non-Muslim" 1 "Muslim"
label values muslim religion_label
order specification outcome term sex muslim estimate standard_error statistic p_value r_squared observations
export delimited using "`output_dir'\Table A2.csv", replace
display as result "Online Appendix Table A2 data saved to: `output_dir'\Table A2.csv"
