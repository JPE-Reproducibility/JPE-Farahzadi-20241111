* Create an artificial Figure A2 fixture with the original survey's variables.
* The data and practice rates are invented and do not reproduce the survey.
args output_dta seed
if `"`output_dta'"' == "" local output_dta "Synthetic Data\Citizenship Survey\citizenship survey synthetic.dta"
if `"`seed'"' == "" local seed 2011

clear
set seed `seed'
set obs 2800
gen byte Relig = floor((_n - 1) / 400) + 1
gen byte hcoba = cond(mod(_n - 1, 400) < 200, 1, 95)
gen byte relprac = runiform() < (0.25 + 0.07 * Relig + 0.05 * (hcoba == 95))
gen double WtFInds = 0.5 + runiform()

label define religion_label 1 "Christian" 2 "Buddhist" 3 "Hindu" ///
    4 "Jewish" 5 "Muslim" 6 "Sikh" 7 "Any other religion"
label values Relig religion_label
label define birthplace_label 1 "England" 95 "Other"
label values hcoba birthplace_label
label define practice_label 0 "Not actively practising religion" ///
    1 "Actively practising religion"
label values relprac practice_label
label var WtFInds "Individual weights for combined sample quarters 1, 2, 3 and 4"
compress
save "`output_dta'", replace
display as result "Synthetic citizenship survey saved: `output_dta'"
