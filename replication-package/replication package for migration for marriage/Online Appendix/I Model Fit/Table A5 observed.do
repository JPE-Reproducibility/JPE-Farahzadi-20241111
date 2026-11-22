* Calculate observed matching moments for Appendix Table A5.
* Usage: do "Table A5 observed.do" "path\to\data.dta" "path\to\output"
args input_file output_dir
if `"`input_file'"' == "" | `"`output_dir'"' == "" {
    display as error "Supply the cleaned data file and an existing output directory."
    exit 198
}
confirm file `"`input_file'"'
use `"`input_file'"', clear

capture confirm variable tertiary_edu
if _rc {
    gen tertiary_edu = tertiary_education
}
capture confirm variable stertiary_edu
if _rc {
    gen stertiary_edu = stertiary_education
}

keep if coupleid != . | single == 1

gen age_group = 1 if (sex == 2 & age >= 23 & age <= 32) | (sex == 1 & age >= 25 & age <= 34)
replace age_group = 2 if (sex == 2 & age >= 33 & age <= 42) | (sex == 1 & age >= 35 & age <= 44)
replace age_group = 3 if (sex == 2 & age >= 43 & age <= 52) | (sex == 1 & age >= 45 & age <= 54)

gen sage_group = 1 if (sex == 1 & sage >= 23 & sage <= 32) | (sex == 2 & sage >= 25 & sage <= 34)
replace sage_group = 2 if (sex == 1 & sage >= 33 & sage <= 42) | (sex == 2 & sage >= 35 & sage <= 44)
replace sage_group = 3 if (sex == 1 & sage >= 43 & sage <= 52) | (sex == 2 & sage >= 45 & sage <= 54)

keep if (age_group != . & sage_group != .) | (age_group != . & single == 1)

gen ethnic_group = 1 if ethnicity == 1 // white
replace ethnic_group = 0 if ethnicityew == 1 // white british
replace ethnic_group = 2 if ethnicity == 3 // indian
replace ethnic_group = 3 if ethnicity == 4 | ethnicity == 5 // pakistani/bangladeshi
replace ethnic_group = 4 if ethnicity >= 6  // other
replace ethnic_group = . if ethnicity == .

gen sethnic_group = 1 if sethnicity == 1 // white
replace sethnic_group = 0 if sethnicityew == 1 // white british
replace sethnic_group = 2 if sethnicity == 3 // indian
replace sethnic_group = 3 if sethnicity == 4 | sethnicity == 5 // pakistani/bangladeshi
replace sethnic_group = 4 if sethnicity >= 6 // other
replace sethnic_group = . if sethnicity == .


gen muslim = religion == 6
replace muslim = . if religion == . | religion == 9

gen smuslim = sreligion == 6
replace smuslim = . if sreligion == . | sreligion == 9

gen sadult_immig = simmigrant18 == 1 & sethnicityew == ethnicityew & ethnicityew != 1 if ethnicity != 2  // remove white british and mixed ethnicity
replace sadult_immig = -9 if simmigrant18 == -9
replace sadult_immig = . if simmigrant18 == .

drop if sadult_immig == -9 

gen group = age_group*1000 + ethnic_group*100 + muslim*10 + tertiary_edu
gen sgroup = sage_group*1000 + sethnic_group*100 + smuslim*10 + stertiary_edu

drop if group == .
drop if sgroup == . & coupleid != .

gen couple = coupleid != .
gen N = 1

preserve
gen inter_edu = tertiary_edu != stertiary_edu if tertiary_edu != . & stertiary_edu != .
rename tertiary_edu education_a5
collapse (mean) inter_edu (sum) inter_edu_count=inter_edu, by(muslim education_a5)
save `"`output_dir'\observed_inter_edu.dta"', replace
export delimited using `"`output_dir'\observed_inter_edu.csv"', replace
mkmat education_a5 muslim inter_edu, matrix(inter_edu)
mkmat education_a5 muslim inter_edu_count, matrix(inter_edu_count)
restore

preserve
gen inter_ethnic = ethnic_group != sethnic_group if ethnic_group != . & sethnic_group != .
collapse (mean) inter_ethnic (sum) inter_ethnic_count=inter_ethnic, by(muslim ethnic_group)
save `"`output_dir'\observed_inter_ethnic.dta"', replace
export delimited using `"`output_dir'\observed_inter_ethnic.csv"', replace
mkmat ethnic_group muslim inter_ethnic, matrix(inter_ethnic)
mkmat ethnic_group muslim inter_ethnic_count, matrix(inter_ethnic_count)
restore

preserve
gen inter_relig = muslim != smuslim if muslim != . & smuslim != .
collapse (mean) inter_relig (sum) inter_relig_count=inter_relig, by(muslim)
save `"`output_dir'\observed_inter_relig.dta"', replace
export delimited using `"`output_dir'\observed_inter_relig.csv"', replace
mkmat muslim inter_relig, matrix(inter_relig)
mkmat muslim inter_relig_count, matrix(inter_relig_count)
restore

preserve
collapse (mean) sadult_immig (sum) sadult_immig_count = sadult_immig, by(muslim ethnic_group)
save `"`output_dir'\observed_migration.dta"', replace
export delimited using `"`output_dir'\observed_migration.csv"', replace
mkmat ethnic_group muslim sadult_immig, matrix(marriage_migration)
mkmat ethnic_group muslim sadult_immig_count, matrix(marriage_migration_count)
restore

preserve
collapse (mean) single (sum) single_count = single, by(muslim)
save `"`output_dir'\observed_single.dta"', replace
export delimited using `"`output_dir'\observed_single.csv"', replace
mkmat muslim single, matrix(single)
mkmat muslim single_count, matrix(single_count)
restore

matrix list inter_edu
matrix list inter_ethnic
matrix list inter_relig
matrix list marriage_migration
matrix list single

matrix list inter_edu_count
matrix list inter_ethnic_count
matrix list inter_relig_count
matrix list marriage_migration_count
matrix list single_count