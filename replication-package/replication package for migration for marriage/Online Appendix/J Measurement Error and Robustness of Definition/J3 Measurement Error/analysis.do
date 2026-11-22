
* Lower-bound marriage migration rates by sex and religion (Appendix Table A9).
* Standalone inputs: working directory holding spinfo.dta (from cleaning.do).
args work_dir
if `"`work_dir'"' == "" local work_dir "Synthetic Data\Understanding Society"

use "`work_dir'\spinfo", clear

capture rename sex_dv sex

keep if mlstat == 2

gen focus_sample = 0
replace focus_sample = 1 if (ukborn >= 1 & ukborn <= 4) 
replace focus_sample = 1 if (ukborn == 5 & (yr2uk4 - birthy < 18) & birthy > 0 & yr2uk4 > 0)

gen sp_marriage_migrant = 0 if (sp_ukborn >= 1 & sp_ukborn <= 4) 
replace sp_marriage_migrant = lcmary4 < sp_yr2uk4 if sp_lcmary4 > 0 & sp_yr2uk4 > 0

gen ethnicity = .
replace ethnicity = 0 if racel == 1
replace ethnicity = 1 if racel >= 2 & racel <= 4
replace ethnicity = 2 if racel == 9
replace ethnicity = 3 if racel == 10 | racel == 11
replace ethnicity = 4 if racel >= 12 & racel <= 97

gen sp_ethnicity = .
replace sp_ethnicity = 0 if sp_racel == 1
replace sp_ethnicity = 1 if sp_racel >= 2 & sp_racel <= 4
replace sp_ethnicity = 2 if sp_racel == 9
replace sp_ethnicity = 3 if sp_racel == 10 | sp_racel == 11
replace sp_ethnicity = 4 if sp_racel >= 12 & sp_racel <= 97

replace sp_marriage_migrant = 0 if ethnicity != sp_ethnicity & sp_ethnicity != .

gen muslim = 0 if oprlg == 2 | oprlg1 > 0
replace muslim = 1 if oprlg1 == 12 

gen all = 1 if sp_marriage_migrant != .

collapse (sum) all sp_marriage_migrant if focus_sample == 1 [weight = indinus_xw], by(sex muslim)
drop if muslim == .

gen rate = sp_marriage_migrant/all*100

save "`work_dir'\lower_bound_rates", replace