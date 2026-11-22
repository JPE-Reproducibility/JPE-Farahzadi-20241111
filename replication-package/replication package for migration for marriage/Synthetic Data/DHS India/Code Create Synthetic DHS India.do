* Create a synthetic version of the India DHS 1998-99 (NFHS-2) Members Recode
* (IAPR42FL.DTA) containing the variables used for Appendix Figure A4.
* Weighted counts are aggregated to sex x age x education cells and synthetic
* persons are then drawn from the cell distribution with randomised rounding.
* This generator requires the restricted source data. Run from the package root.
args input_dta output_dta target_n seed
if `"`input_dta'"' == "" local input_dta "Synthetic Data\IPUMS\IAPR42DT\IAPR42FL.DTA"
if `"`output_dta'"' == "" local output_dta "Synthetic Data\DHS India\IAPR42FL synthetic.dta"
if `"`target_n'"' == "" local target_n 20000
if `"`seed'"' == "" local seed 1999

capture mkdir "Synthetic Data\DHS India"

* sh54 is the sex variable of the survey sub-sample;
* hv104/hv105/hv106 are sex, age and highest educational level.
use hv005 hv104 hv105 hv106 sh54 using "`input_dta'", clear
keep if !missing(sh54) & inlist(hv106, 0, 1, 2, 3)

collapse (sum) pop=hv005, by(sh54 hv104 hv105 hv106)
quietly summarize pop
local total = r(sum)

set seed `seed'
gen long synth_n = floor(`target_n' * pop / `total' + runiform())
drop if synth_n == 0
expand synth_n

gen double hv005 = pop / synth_n
drop pop synth_n
gen long hhid_synth = _n
order hhid_synth hv005 hv104 hv105 hv106 sh54
label variable hv005 "Sample weight (synthetic)"
label variable hv104 "Sex of household member"
label variable hv105 "Age of household member"
label variable hv106 "Highest educational level"
label variable sh54 "Sex"
compress
save "`output_dta'", replace
display as result "Synthetic India DHS saved: `output_dta'"
