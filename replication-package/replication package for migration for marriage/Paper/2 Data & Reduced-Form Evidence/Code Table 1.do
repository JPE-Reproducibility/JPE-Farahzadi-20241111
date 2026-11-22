* Main-text Table 1: Summary Statistics by Religion, Ethnicity, and Gender.
* Output: Paper\Output\Table 1.csv (one row per measure/group/sex).
* Use data_facts.dta from the reduced-form preparation script.
args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Paper\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear

* Classify respondents by ethnicity and religion; religion code 9 is excluded.
tempvar white
gen byte `white' = ethnicityew == 1 if ethnicity != .

gen byte table_group = .
replace table_group = 1 if `white' == 1 & muslim == 0
replace table_group = 2 if `white' == 0 & muslim == 0
replace table_group = 3 if muslim == 1

tempfile table
tempname results
postfile `results' str32 measure str32 group byte sex double value long n ///
    using `table', replace

forvalues group_id = 1/3 {
    forvalues sex_id = 1/2 {
        local sample "table_group == `group_id' & sex == `sex_id'"
        local group_name "White British non-Muslim"
        if `group_id' == 2 local group_name "Ethnic minority non-Muslim"
        if `group_id' == 3 local group_name "Muslim"
        quietly summarize age if `sample'
        post `results' ("Age") ("`group_name'") (`sex_id') (r(mean)) (r(N))

        quietly summarize tertiary if `sample'
        post `results' ("College education (%)") ("`group_name'") (`sex_id') (100 * r(mean)) (r(N))

        quietly summarize ukborn if `sample'
        post `results' ("UK-born (%)") ("`group_name'") (`sex_id') (100 * r(mean)) (r(N))

        quietly summarize married if `sample'
        post `results' ("Married (%)") ("`group_name'") (`sex_id') (100 * r(mean)) (r(N))
    }
}

* Post the remaining summary means and sample counts.
forvalues group_id = 1/3 {
    forvalues sex_id = 1/2 {
        local sample "table_group == `group_id' & sex == `sex_id'"
        local group_name "White British non-Muslim"
        if `group_id' == 2 local group_name "Ethnic minority non-Muslim"
        if `group_id' == 3 local group_name "Muslim"

        quietly summarize sadult_immig if `sample' & married == 1
        local migration = 100 * r(mean)
        local migration_n = r(N)
        post `results' ("Marriage migration (%)") ("`group_name'") (`sex_id') ///
            (`migration') (`migration_n')

        quietly summarize inter_relig if `sample' & married == 1
        post `results' ("Inter-religious (%)") ("`group_name'") (`sex_id') ///
            (100 * r(mean)) (r(N))

        quietly summarize inter_ethnic if `sample' & married == 1
        post `results' ("Inter-ethnic (%)") ("`group_name'") (`sex_id') ///
            (100 * r(mean)) (r(N))

        quietly count if `sample'
        post `results' ("Number of observations") ("`group_name'") (`sex_id') ///
            (r(N)) (r(N))
    }
}

postclose `results'
use `table', clear
label define sex_label 1 "Male" 2 "Female"
label values sex sex_label
gen byte measure_order = 1 if measure == "Age"
replace measure_order = 2 if measure == "College education (%)"
replace measure_order = 3 if measure == "Married (%)"
replace measure_order = 4 if measure == "UK-born (%)"
replace measure_order = 5 if measure == "Marriage migration (%)"
replace measure_order = 6 if measure == "Inter-religious (%)"
replace measure_order = 7 if measure == "Inter-ethnic (%)"
replace measure_order = 8 if measure == "Number of observations"
gen byte group_order = 1 if group == "White British non-Muslim"
replace group_order = 2 if group == "Ethnic minority non-Muslim"
replace group_order = 3 if group == "Muslim"
sort measure_order group_order sex
drop measure_order group_order
order measure group sex value n
export delimited using "`output_dir'\Table 1.csv", replace
display as result "Main-text Table 1 data saved to: `output_dir'\Table 1.csv"
