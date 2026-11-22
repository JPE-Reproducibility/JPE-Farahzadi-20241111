* Prepare the common reduced-form analysis sample.
*
* Run from the package root:
*   do "Preparation\Reduced Form Sample\Code Prepare Reduced Form Data.do" ///
*      "path\to\data.dta" "path\to\data_facts.dta"
*
* Arguments: cleaned person/spouse dataset, output analysis dataset.
* Defaults use the synthetic fixture; supply authorized paths for research data.
args input_dta output_dta

if `"`input_dta'"' == "" local input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`output_dta'"' == "" local output_dta "Preparation\Reduced Form Sample\data_facts.dta"

use "`input_dta'", clear

* Keep partnered respondents and never-married singles.
keep if !missing(coupleid) | single == 1

* Ten-year age groups use different age cutoffs for men and women.
gen byte age_group = 1 if (sex == 2 & inrange(age, 23, 32)) | (sex == 1 & inrange(age, 25, 34))
replace age_group = 2 if (sex == 2 & inrange(age, 33, 42)) | (sex == 1 & inrange(age, 35, 44))
replace age_group = 3 if (sex == 2 & inrange(age, 43, 52)) | (sex == 1 & inrange(age, 45, 54))

gen byte sage_group = 1 if (sex == 1 & inrange(sage, 23, 32)) | (sex == 2 & inrange(sage, 25, 34))
replace sage_group = 2 if (sex == 1 & inrange(sage, 33, 42)) | (sex == 2 & inrange(sage, 35, 44))
replace sage_group = 3 if (sex == 1 & inrange(sage, 43, 52)) | (sex == 2 & inrange(sage, 45, 54))
keep if (!missing(age_group) & !missing(sage_group)) | (!missing(age_group) & single == 1)

* Harmonize ethnicity into the five analytical categories used by the models.
gen byte ethnic_group = 1 if ethnicity == 1
replace ethnic_group = 0 if ethnicityew == 1
replace ethnic_group = 2 if ethnicity == 3
replace ethnic_group = 3 if inlist(ethnicity, 4, 5)
replace ethnic_group = 4 if ethnicity >= 6 & !missing(ethnicity)
replace ethnic_group = . if missing(ethnicity)

gen byte sethnic_group = 1 if sethnicity == 1
replace sethnic_group = 0 if sethnicityew == 1
replace sethnic_group = 2 if sethnicity == 3
replace sethnic_group = 3 if inlist(sethnicity, 4, 5)
replace sethnic_group = 4 if sethnicity >= 6 & !missing(sethnicity)
replace sethnic_group = . if missing(sethnicity)

gen byte muslim = religion == 6 if !missing(religion) & religion != 9
gen byte smuslim = sreligion == 6 if !missing(sreligion) & sreligion != 9

* Adult marriage migration requires a spouse born abroad who arrived at 18+,
* from the same detailed ethnic group, for non-mixed ethnic minorities.
gen byte sadult_immig = simmigrant18 == 1 & sethnicityew == ethnicityew ///
    & ethnicityew != 1 if ethnicity != 2
replace sadult_immig = -9 if simmigrant18 == -9
replace sadult_immig = . if missing(simmigrant18)
drop if sadult_immig == -9

* Create variable names referenced by the analysis scripts.
gen byte tertiary_edu = tertiary_education
gen byte stertiary_edu = stertiary_education
gen byte tertiary = tertiary_education
gen byte white = ethnicityew == 1 if !missing(ethnicityew)

replace religion = . if religion == 9
replace sreligion = . if sreligion == 9
gen byte inter_relig = religion != sreligion if religion != . & sreligion != .
gen byte inter_ethnic = ethnicity != sethnicity if ethnicity != . & sethnicity != . & ethnicity != 2 & sethnicity != 2

gen age_gap = sage - age if sex == 2
replace age_gap = age - sage if sex == 1
gen edu_diff = stertiary_edu - tertiary_edu

capture mkdir "Online Appendix\Output"
save "`output_dta'", replace
display as result "Reduced-form analysis dataset saved to: `output_dta'"
