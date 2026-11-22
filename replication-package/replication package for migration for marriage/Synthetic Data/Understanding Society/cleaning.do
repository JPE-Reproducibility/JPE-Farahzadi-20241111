* Match each person in Understanding Society wave 1 with their spouse.
* Standalone inputs: wave 1 indresp.dta; working directory for spinfo.dta.
args indresp_dta work_dir
if `"`indresp_dta'"' == "" {
    local indresp_dta "Synthetic Data\Understanding Society\indresp.dta"
}
if `"`work_dir'"' == "" local work_dir "Synthetic Data\Understanding Society"
capture mkdir "`work_dir'"

// match each person with their spouse (understanding society)

use a_hidp a_pno a_ppno a_sex_dv a_age_dv a_birthy a_yr2uk4 a_lcmary4 a_ukborn a_oprlg1 a_oprlg a_racel using "`indresp_dta'", clear

keep if a_ppno > 0

rename a_* a_sp_*
rename a_sp_ppno a_pno
rename a_sp_hidp a_hidp
drop a_sp_pno

save "`work_dir'\temp", replace

use a_hidp a_pno a_ppno a_sex_dv a_age_dv a_birthy a_yr2uk4 a_lcmary4 a_ukborn a_mlstat a_oprlg1 a_oprlg a_racel a_indinus_xw using "`indresp_dta'", clear

keep if a_ppno > 0

merge 1:1 a_hidp a_pno using "`work_dir'\temp.dta"
drop _merge 

rename a_* *

save "`work_dir'\spinfo", replace 

erase "`work_dir'\temp.dta"
