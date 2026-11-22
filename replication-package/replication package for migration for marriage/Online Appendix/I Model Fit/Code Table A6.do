* Appendix Table A6: Estimated Endogamy Preferences with and without
* Marriage Migration (tab:nomig).
*
* With-migration column: runs the baseline estimation in
* "Paper\5 Results\Code Table 4.do", which excludes marriage
* migrants from the local match counts and models them separately (lxy/lyx).
*
* Without-migration column: uses the classic Choo and Siow (2006)
* framework in which migrants are kept as
* ordinary matches and the preference parameters are recovered by a
* minimum-distance regression of the observed match counts, rather than by
* the equilibrium-fitting procedure used for the with-migration column.
*
* Exports the nine preference contrasts (age x3, education, ethnicity x4,
* religion) and their standard errors for Muslim and non-Muslim groups under
* both specifications to Table A6.csv. The LaTeX fragment in
* "Paper text\tab_tex\tab_nomigration.tex" remains separately typeset.
*
* Usage (run from the package root):
* do "Online Appendix\I Model Fit\Code Table A6.do" ///
*   "data.dta" "model_dir_with_migration" "model_dir_without_migration" "output_dir"
args input_dta mig_dir nomig_dir output_dir
if `"`input_dta'"' == "" local input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`mig_dir'"' == "" local mig_dir "Synthetic Data\model_out\Muslim"
if `"`nomig_dir'"' == "" local nomig_dir "Synthetic Data\model_out\Muslim - No Migration"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"

capture confirm file `"`input_dta'"'
if _rc {
    display as error "Cleaned Census data not found: `input_dta'"
    exit 601
}
capture mkdir "Synthetic Data"
capture mkdir "Synthetic Data\model_out"
capture mkdir "`mig_dir'"
capture mkdir "`nomig_dir'"
capture mkdir "Online Appendix"
capture mkdir "Online Appendix\I Model Fit"
capture mkdir "`output_dir'"

* ------------------------------------------------------------------
* With migration: baseline estimation (Muslim vs. non-Muslim)
* ------------------------------------------------------------------
noisily do "Paper\5 Results\Code Table 4.do" ///
    "`input_dta'" "`mig_dir'" "`mig_dir'" 6 "Muslim"

* ------------------------------------------------------------------
* Without migration: observed matching counts
* Marriage migrants are kept as ordinary matches here (no lxy/lyx split),
* which is the defining difference from Code Table 4.do above.
* ------------------------------------------------------------------
use "`input_dta'", clear
keep if coupleid != . | single == 1

capture confirm variable tertiary_edu
if _rc {
    gen tertiary_edu = tertiary_education
}
capture confirm variable stertiary_edu
if _rc {
    gen stertiary_edu = stertiary_education
}

gen age_group = 1 if (sex == 2 & inrange(age, 23, 32)) | (sex == 1 & inrange(age, 25, 34))
replace age_group = 2 if (sex == 2 & inrange(age, 33, 42)) | (sex == 1 & inrange(age, 35, 44))
replace age_group = 3 if (sex == 2 & inrange(age, 43, 52)) | (sex == 1 & inrange(age, 45, 54))
gen sage_group = 1 if (sex == 1 & inrange(sage, 23, 32)) | (sex == 2 & inrange(sage, 25, 34))
replace sage_group = 2 if (sex == 1 & inrange(sage, 33, 42)) | (sex == 2 & inrange(sage, 35, 44))
replace sage_group = 3 if (sex == 1 & inrange(sage, 43, 52)) | (sex == 2 & inrange(sage, 45, 54))
keep if (!missing(age_group) & !missing(sage_group)) | (!missing(age_group) & single == 1)

gen ethnic_group = 1 if ethnicity == 1
replace ethnic_group = 0 if ethnicityew == 1
replace ethnic_group = 2 if ethnicity == 3
replace ethnic_group = 3 if inlist(ethnicity, 4, 5)
replace ethnic_group = 4 if ethnicity >= 6
replace ethnic_group = . if missing(ethnicity)
gen sethnic_group = 1 if sethnicity == 1
replace sethnic_group = 0 if sethnicityew == 1
replace sethnic_group = 2 if sethnicity == 3
replace sethnic_group = 3 if inlist(sethnicity, 4, 5)
replace sethnic_group = 4 if sethnicity >= 6
replace sethnic_group = . if missing(sethnicity)

gen muslim = religion == 6
replace muslim = . if missing(religion) | religion == 9
gen smuslim = sreligion == 6
replace smuslim = . if missing(sreligion) | sreligion == 9

quietly count if muslim == 1
if r(N) == 0 {
    display as error "No observations with religion == 6"
    exit 2000
}

gen group = age_group*1000 + ethnic_group*100 + muslim*10 + tertiary_edu
gen sgroup = sage_group*1000 + sethnic_group*100 + smuslim*10 + stertiary_edu
drop if missing(group)
drop if missing(sgroup) & !missing(coupleid)

gen N = 1
tempfile nomig_sample
save `nomig_sample'

* Create all 60 groups, including groups with zero counts.
tempfile women_counts men_counts
preserve
keep if sex == 2
collapse (sum) N, by(group)
rename N nx
save `women_counts'
restore
preserve
keep if sex == 1
collapse (sum) N, by(group)
rename N ny
save `men_counts'
restore
clear
mata
a = ((1,2,3)#J(1,20,1))'
e = (J(1,3,1)#(0,1,2,3,4)#J(1,4,1))'
r = (J(1,15,1)#(0,1)#J(1,2,1))'
s = (J(1,30,1)#(0,1))'
allgroups = 1000:*a + 100:*e + 10:*r + s
st_matrix("allgroups", allgroups)
end
svmat allgroups, names(group)
rename group1 group
merge 1:1 group using `women_counts', nogen
merge 1:1 group using `men_counts', nogen
replace nx = 0 if missing(nx)
replace ny = 0 if missing(ny)
save "`nomig_dir'\dist.dta", replace
preserve
keep group nx
save "`nomig_dir'\nx.dta", replace
restore
rename group sgroup
keep sgroup ny
save "`nomig_dir'\ny.dta", replace
use `nomig_sample', clear

preserve
keep if single == 0 & sex == 2
collapse (sum) N, by(group sgroup)
rename N muxy
save "`nomig_dir'\muxy.dta", replace
restore
preserve
keep if single == 1 & sex == 2
collapse (sum) N, by(group)
rename N mux0
save "`nomig_dir'\mux0.dta", replace
restore
keep if single == 1 & sex == 1
collapse (sum) N, by(group)
rename group sgroup
rename N mu0y
save "`nomig_dir'\mu0y.dta", replace

* ------------------------------------------------------------------
* Without migration: minimum-distance estimation
* Minimum-distance regression of the observed match counts onto the
* preference-model grid (Choo and Siow 2006).
* ------------------------------------------------------------------
clear
mata
a = ((1,2,3)#J(1,20,1))'
e = (J(1,3,1)#(0,1,2,3,4)#J(1,4,1))'
r = (J(1,15,1)#(0,1)#J(1,2,1))'
s = (J(1,30,1)#(0,1))'

ncat_x = rows(a)
ncat_y = rows(a)

ax = a#J(ncat_y,1,1)
ay = J(ncat_x,1,a)
ex = e#J(ncat_y,1,1)
ey = J(ncat_x,1,e)
rx = r#J(ncat_y,1,1)
ry = J(ncat_x,1,r)
sx = s#J(ncat_y,1,1)
sy = J(ncat_x,1,s)

group = (1000:*ax + 100:*ex + 10*rx + sx)
sgroup = (1000:*ay + 100:*ey + 10*ry + sy)

st_matrix("groupmat", group)
st_matrix("sgroupmat", sgroup)
st_matrix("ax", ax)
st_matrix("ay", ay)
st_matrix("sx", sx)
st_matrix("sy", sy)
st_matrix("ex", ex)
st_matrix("ey", ey)
st_matrix("rx", rx)
st_matrix("ry", ry)
end

svmat groupmat, names(group)
svmat sgroupmat, names(sgroup)
svmat ax, names(a_x)
svmat ay, names(a_y)
svmat sx, names(s_x)
svmat sy, names(s_y)
svmat ex, names(e_x)
svmat ey, names(e_y)
svmat rx, names(r_x)
svmat ry, names(r_y)
rename group1 group
rename sgroup1 sgroup
rename a_x1 a_x
rename a_y1 a_y
rename s_x1 s_x
rename s_y1 s_y
rename e_x1 e_x
rename e_y1 e_y
rename r_x1 r_x
rename r_y1 r_y

merge 1:1 group sgroup using "`nomig_dir'\muxy.dta", nogen
merge m:1 group using "`nomig_dir'\mux0.dta", nogen
merge m:1 sgroup using "`nomig_dir'\mu0y.dta", nogen
sort group sgroup

egen N = total(muxy)
replace muxy = 0 if missing(muxy)
local delta = 0.01
replace muxy = N*(muxy + `delta')/(N + `delta')
gen dE = 2*log(muxy/sqrt(mux0*mu0y))

reg dE a_x##a_y##r_x##r_y r_x##r_y##e_x##e_y r_x##r_y##s_x##s_y

matrix C = J(18,2,.)
* Column 1: non-Muslim (r=0); column 2: Muslim (r=1)

* age
quietly margins a_x#a_y [pw=muxy], at(r_x==0 r_y==0)
quietly matrix temp1 = r(b)
quietly matrix temp2 = r(V)
matrix C[1,1] =  temp1[1,1] + temp1[1,5] - temp1[1,2] - temp1[1,4]
matrix C[2,1] = sqrt(temp2[1,1] + temp2[5,5] + temp2[2,2] + temp2[4,4] + 2*temp2[1,5] - 2*temp2[1,2] - 2*temp2[1,4] - 2*temp2[5,2] - 2*temp2[5,4] + 2*temp2[2,4])
matrix C[3,1] = temp1[1,1] + temp1[1,9] - temp1[1,3] - temp1[1,7]
matrix C[4,1] = sqrt(temp2[1,1] + temp2[9,9] + temp2[3,3] + temp2[7,7] + 2*temp2[1,9] - 2*temp2[1,3] - 2*temp2[1,7] - 2*temp2[9,3] - 2*temp2[9,7] + 2*temp2[3,7])
matrix C[5,1] = temp1[1,5] + temp1[1,9] - temp1[1,6] - temp1[1,8]
matrix C[6,1] = sqrt(temp2[5,5] + temp2[9,9] + temp2[6,6] + temp2[8,8] + 2*temp2[5,9] - 2*temp2[5,6] - 2*temp2[5,8] - 2*temp2[9,6] - 2*temp2[9,8] + 2*temp2[6,8])

quietly margins a_x#a_y [pw=muxy], at(r_x==1 r_y==1)
quietly matrix temp1 = r(b)
quietly matrix temp2 = r(V)
matrix C[1,2] =  temp1[1,1] + temp1[1,5] - temp1[1,2] - temp1[1,4]
matrix C[2,2] = sqrt(temp2[1,1] + temp2[5,5] + temp2[2,2] + temp2[4,4] + 2*temp2[1,5] - 2*temp2[1,2] - 2*temp2[1,4] - 2*temp2[5,2] - 2*temp2[5,4] + 2*temp2[2,4])
matrix C[3,2] = temp1[1,1] + temp1[1,9] - temp1[1,3] - temp1[1,7]
matrix C[4,2] = sqrt(temp2[1,1] + temp2[9,9] + temp2[3,3] + temp2[7,7] + 2*temp2[1,9] - 2*temp2[1,3] - 2*temp2[1,7] - 2*temp2[9,3] - 2*temp2[9,7] + 2*temp2[3,7])
matrix C[5,2] = temp1[1,5] + temp1[1,9] - temp1[1,6] - temp1[1,8]
matrix C[6,2] = sqrt(temp2[5,5] + temp2[9,9] + temp2[6,6] + temp2[8,8] + 2*temp2[5,9] - 2*temp2[5,6] - 2*temp2[5,8] - 2*temp2[9,6] - 2*temp2[9,8] + 2*temp2[6,8])

* education
quietly margins s_x#s_y [pw=muxy], at(r_x==0 r_y==0)
quietly matrix temp1 = r(b)
quietly matrix temp2 = r(V)
matrix C[7,1] = temp1[1,1] + temp1[1,4] - temp1[1,2] - temp1[1,3]
matrix C[8,1] = sqrt(temp2[1,1] + temp2[4,4] + temp2[2,2] + temp2[3,3] + 2*temp2[1,4] - 2*temp2[1,2] - 2*temp2[1,3] - 2*temp2[4,2] - 2*temp2[4,3] + 2*temp2[2,3])

quietly margins s_x#s_y [pw=muxy], at(r_x==1 r_y==1)
quietly matrix temp1 = r(b)
quietly matrix temp2 = r(V)
matrix C[7,2] =  temp1[1,1] + temp1[1,4] - temp1[1,2] - temp1[1,3]
matrix C[8,2] = sqrt(temp2[1,1] + temp2[4,4] + temp2[2,2] + temp2[3,3] + 2*temp2[1,4] - 2*temp2[1,2] - 2*temp2[1,3] - 2*temp2[4,2] - 2*temp2[4,3] + 2*temp2[2,3])

* ethnicity
quietly margins e_x#e_y [pw=muxy], at(r_x==0 r_y==0)
quietly matrix temp1 = r(b)
quietly matrix temp2 = r(V)
matrix C[9,1]  = temp1[1,7]  + temp1[1,1] - temp1[1,2]  - temp1[1,6]
matrix C[10,1] = sqrt(temp2[7,7] + temp2[1,1] + temp2[2,2] + temp2[6,6] + 2*temp2[7,1] - 2*temp2[7,2] - 2*temp2[7,6] - 2*temp2[1,2] - 2*temp2[1,6] + 2*temp2[2,6])
matrix C[11,1] = temp1[1,13] + temp1[1,1] - temp1[1,3]  - temp1[1,11]
matrix C[12,1] = sqrt(temp2[13,13] + temp2[1,1] + temp2[3,3] + temp2[11,11] + 2*temp2[13,1] - 2*temp2[13,3] - 2*temp2[13,11] - 2*temp2[1,3] - 2*temp2[1,11] + 2*temp2[3,11])
matrix C[13,1] = temp1[1,19] + temp1[1,1] - temp1[1,4]  - temp1[1,16]
matrix C[14,1] = sqrt(temp2[19,19] + temp2[1,1] + temp2[4,4] + temp2[16,16] + 2*temp2[19,1] - 2*temp2[19,4] - 2*temp2[19,16] - 2*temp2[1,4] - 2*temp2[1,16] + 2*temp2[4,16])
matrix C[15,1] = temp1[1,25] + temp1[1,1] - temp1[1,5]  - temp1[1,21]
matrix C[16,1] = sqrt(temp2[25,25] + temp2[1,1] + temp2[5,5] + temp2[21,21] + 2*temp2[25,1] - 2*temp2[25,5] - 2*temp2[25,21] - 2*temp2[1,5] - 2*temp2[1,21] + 2*temp2[5,21])

quietly margins e_x#e_y [pw=muxy], at(r_x==1 r_y==1)
quietly matrix temp1 = r(b)
quietly matrix temp2 = r(V)
matrix C[9,2]  = temp1[1,7]  + temp1[1,1] - temp1[1,2]  - temp1[1,6]
matrix C[10,2] = sqrt(temp2[7,7] + temp2[1,1] + temp2[2,2] + temp2[6,6] + 2*temp2[7,1] - 2*temp2[7,2] - 2*temp2[7,6] - 2*temp2[1,2] - 2*temp2[1,6] + 2*temp2[2,6])
matrix C[11,2] = temp1[1,13] + temp1[1,1] - temp1[1,3]  - temp1[1,11]
matrix C[12,2] = sqrt(temp2[13,13] + temp2[1,1] + temp2[3,3] + temp2[11,11] + 2*temp2[13,1] - 2*temp2[13,3] - 2*temp2[13,11] - 2*temp2[1,3] - 2*temp2[1,11] + 2*temp2[3,11])
matrix C[13,2] = temp1[1,19] + temp1[1,1] - temp1[1,4]  - temp1[1,16]
matrix C[14,2] = sqrt(temp2[19,19] + temp2[1,1] + temp2[4,4] + temp2[16,16] + 2*temp2[19,1] - 2*temp2[19,4] - 2*temp2[19,16] - 2*temp2[1,4] - 2*temp2[1,16] + 2*temp2[4,16])
matrix C[15,2] = temp1[1,25] + temp1[1,1] - temp1[1,5]  - temp1[1,21]
matrix C[16,2] = sqrt(temp2[25,25] + temp2[1,1] + temp2[5,5] + temp2[21,21] + 2*temp2[25,1] - 2*temp2[25,5] - 2*temp2[25,21] - 2*temp2[1,5] - 2*temp2[1,21] + 2*temp2[5,21])

* religion
quietly margins r_x#r_y [pw=muxy]
quietly matrix temp1 = r(b)
quietly matrix temp2 = r(V)
matrix C[17,1] = temp1[1,4] + temp1[1,1] - temp1[1,2] - temp1[1,3]
matrix C[18,1] = sqrt(temp2[4,4] + temp2[1,1] + temp2[2,2] + temp2[3,3] + 2*temp2[4,1] - 2*temp2[4,2] - 2*temp2[4,3] - 2*temp2[1,2] - 2*temp2[1,3] + 2*temp2[2,3])
matrix C[17,2] = temp1[1,4] + temp1[1,1] - temp1[1,2] - temp1[1,3]
matrix C[18,2] = sqrt(temp2[4,4] + temp2[1,1] + temp2[2,2] + temp2[3,3] + 2*temp2[4,1] - 2*temp2[4,2] - 2*temp2[4,3] - 2*temp2[1,2] - 2*temp2[1,3] + 2*temp2[2,3])

clear
svmat C, names(col)
gen contrast_id = ceil(_n/2)
gen estimate_other = c1 if mod(_n, 2) == 1
gen se_other       = c1 if mod(_n, 2) == 0
gen estimate_rel   = c2 if mod(_n, 2) == 1
gen se_rel         = c2 if mod(_n, 2) == 0
collapse (max) estimate_other se_other estimate_rel se_rel, by(contrast_id)
gen str12 category = ""
gen str42 comparison = ""
replace category = "Age" if inrange(contrast_id, 1, 3)
replace comparison = "Young and middle-aged" if contrast_id == 1
replace comparison = "Young and old" if contrast_id == 2
replace comparison = "Middle-aged and old" if contrast_id == 3
replace category = "Education" if contrast_id == 4
replace comparison = "Less than college and college or more" if contrast_id == 4
replace category = "Ethnicity" if inrange(contrast_id, 5, 8)
replace comparison = "Other White and White British" if contrast_id == 5
replace comparison = "Indian and White British" if contrast_id == 6
replace comparison = "Pakistani/Bangladeshi and White British" if contrast_id == 7
replace comparison = "Other and White British" if contrast_id == 8
replace category = "Religion" if contrast_id == 9
replace comparison = "Muslim and non-Muslim" if contrast_id == 9
order contrast_id category comparison estimate_other se_other estimate_rel se_rel
export delimited using "`nomig_dir'\Table 4 - Muslim (no migration).csv", replace

tempfile nomig_results
save `nomig_results'

* ------------------------------------------------------------------
* Combine the with- and without-migration contrasts into Table A6.csv
* ------------------------------------------------------------------
import delimited using "`mig_dir'\Table 4 - Muslim.csv", clear varnames(1)
rename estimate_other with_migration_non_muslim
rename se_other with_migration_non_muslim_se
rename estimate_rel with_migration_muslim
rename se_rel with_migration_muslim_se
tempfile mig_results
save `mig_results'

use `nomig_results', clear
rename estimate_other without_migration_non_muslim
rename se_other without_migration_non_muslim_se
rename estimate_rel without_migration_muslim
rename se_rel without_migration_muslim_se
merge 1:1 contrast_id using `mig_results', keepusing( ///
    with_migration_non_muslim with_migration_non_muslim_se ///
    with_migration_muslim with_migration_muslim_se) assert(match) nogen

order contrast_id category comparison ///
    with_migration_non_muslim with_migration_non_muslim_se ///
    with_migration_muslim with_migration_muslim_se ///
    without_migration_non_muslim without_migration_non_muslim_se ///
    without_migration_muslim without_migration_muslim_se
sort contrast_id
export delimited using "`output_dir'\Table A6.csv", replace

display as result "Appendix Table A6 data written to `output_dir'\Table A6.csv"
