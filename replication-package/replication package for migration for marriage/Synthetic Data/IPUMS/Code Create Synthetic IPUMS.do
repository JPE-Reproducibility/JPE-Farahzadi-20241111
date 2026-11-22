* Create a synthetic version of the IPUMS-International extract
* (ipumsi_00001.dta) for the Pakistan 1998 and Bangladesh 2001 censuses,
* keeping the variables used for Appendix Figure A4 (sample, sex, age,
* edattain, perwt). Weighted counts are aggregated to sample x sex x age x
* education cells and synthetic persons are drawn from each census's cell
* distribution with randomised rounding. Run from the package root.
args input_dta output_dta target_n seed
if `"`input_dta'"' == "" local input_dta "Synthetic Data\IPUMS\Data\ipumsi_00001.dta"
if `"`output_dta'"' == "" local output_dta "Synthetic Data\IPUMS\Data\ipumsi synthetic.dta"
if `"`target_n'"' == "" local target_n 30000
if `"`seed'"' == "" local seed 1998

* Pakistan 1998 = 586199801; Bangladesh 2001 = 50200101.
use sample sex age edattain perwt using "`input_dta'" ///
    if inlist(sample, 586199801, 50200101), clear
keep if inlist(sex, 1, 2) & !missing(age) & inrange(edattain, 1, 4)

collapse (sum) pop=perwt, by(sample sex age edattain)
bysort sample: egen double sample_total = total(pop)

set seed `seed'
gen long synth_n = floor(`target_n' * pop / sample_total + runiform())
drop if synth_n == 0
expand synth_n

gen double perwt = pop / synth_n
drop pop sample_total synth_n
gen long person_synth = _n
order person_synth sample sex age edattain perwt
compress
save "`output_dta'", replace
display as result "Synthetic IPUMS extract saved: `output_dta'"
