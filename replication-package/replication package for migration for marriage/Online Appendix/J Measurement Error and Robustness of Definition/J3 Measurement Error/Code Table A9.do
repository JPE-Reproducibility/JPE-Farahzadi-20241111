* Appendix Table A9: Marriage Migration Rates, Baseline and Lower-Bound Definitions
* Baseline: model-based marriage migration rates, entered as reported in the
* paper (Paper text\Appendix.tex, tab:mm_lowerbound_rates).
* Lower bound: Understanding Society wave 1, spouse arrives strictly after the
* year of marriage (cleaning.do and analysis.do in this folder).
* Run from the replication-package root.
* Usage:
* do "Online Appendix\J Measurement Error and Robustness of Definition\J3 Measurement Error\Code Table A9.do" ///
*   "indresp.dta" "work_dir" "output_dir"
args indresp_dta work_dir output_dir
if `"`work_dir'"' == "" local work_dir "Synthetic Data\Understanding Society"
if `"`output_dir'"' == "" {
    local output_dir "Online Appendix\Output"
}
capture mkdir "`output_dir'"

local code_dir "Online Appendix\J Measurement Error and Robustness of Definition\J3 Measurement Error"
noisily do "`code_dir'\cleaning.do" "`indresp_dta'" "`work_dir'"
noisily do "`code_dir'\analysis.do" "`work_dir'"
use "`work_dir'\lower_bound_rates.dta", clear
gen double lower_bound = rate / 100
keep sex muslim lower_bound
tempfile lower
save `lower'

* Baseline (model) rates; sex 1 = men, 2 = women.
clear
input byte(muslim sex) double baseline
0 1 0.228
0 2 0.196
1 1 0.511
1 2 0.537
end

merge 1:1 sex muslim using `lower', nogen
gen str10 religion_group = cond(muslim == 1, "Muslim", "Non-Muslim")
gen str5 gender = cond(sex == 1, "Men", "Women")
gsort muslim sex
order religion_group gender baseline lower_bound
keep religion_group gender baseline lower_bound
export delimited using "`output_dir'\Table A9.csv", replace

display as result "Appendix Table A9 data written to `output_dir'\Table A9.csv"
