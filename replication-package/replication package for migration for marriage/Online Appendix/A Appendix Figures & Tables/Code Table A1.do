* Online Appendix Table A1: Educational Sorting in Marriage Migration (Logit).
* Reports average marginal effects for marriage migration, by sex/religion,

args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear
capture confirm variable white
if _rc {
    gen byte white = ethnicityew == 1 if !missing(ethnicityew)
}
drop if white == 1

tempfile table
tempname results
postfile `results' str12 specification str24 outcome str32 term ///
    byte sex byte muslim double estimate standard_error statistic p_value ///
    long observations using `table', replace

forvalues sex_id = 1/2 {
    forvalues muslim_id = 0/1 {
        foreach specification in baseline adjusted {
            quietly count if sex == `sex_id' & muslim == `muslim_id' ///
                & !missing(tertiary_edu, sadult_immig)
            local sample_n = r(N)
            if "`specification'" == "baseline" {
                capture quietly logit tertiary_edu sadult_immig  ///
                     if sex == `sex_id' & muslim == `muslim_id'
            }
            else {
                capture quietly logit tertiary_edu sadult_immig  ///
                    i.ethnic_group i.age_group i.region ///
                    if sex == `sex_id' & muslim == `muslim_id'
            }
            if _rc {
                display as error "Table A1 `specification' logit not estimable for sex=`sex_id', muslim=`muslim_id'; row recorded with missing estimates."
                post `results' ("`specification'") ("College education") ///
                    ("Marriage migration AME") (`sex_id') (`muslim_id') ///
                    (.) (.) (.) (.) (`sample_n')
                continue
            }
            local n = e(N)
            capture quietly margins, dydx(sadult_immig)
            if _rc {
                display as error "Table A1 AME unavailable for `specification', sex=`sex_id', muslim=`muslim_id'; row recorded with missing estimates."
                post `results' ("`specification'") ("College education") ///
                    ("Marriage migration AME") (`sex_id') (`muslim_id') ///
                    (.) (.) (.) (.) (`n')
                continue
            }
            matrix marginal_effect = r(table)
            local estimate = marginal_effect[1, 1]
            local se = marginal_effect[2, 1]
            local statistic = marginal_effect[3, 1]
            local p = marginal_effect[4, 1]
            if missing(`se') | `se' <= 0 {
                local estimate = .
                local se = .
                local statistic = .
                local p = .
            }
            post `results' ("`specification'") ("College education") ///
                ("Marriage migration AME") (`sex_id') (`muslim_id') ///
                (`estimate') (`se') (`statistic') (`p') (`n')
        }
    }
}

postclose `results'
use `table', clear
gen byte specification_order = 1 if specification == "baseline"
replace specification_order = 2 if specification == "adjusted"
gsort -muslim sex specification_order
drop specification_order
label define sex_label 1 "Male" 2 "Female"
label values sex sex_label
label define religion_label 0 "Non-Muslim" 1 "Muslim"
label values muslim religion_label
order specification outcome term sex muslim estimate standard_error statistic p_value observations
export delimited using "`output_dir'\Table A1.csv", replace
display as result "Online Appendix Table A1 data saved to: `output_dir'\Table A1.csv"
