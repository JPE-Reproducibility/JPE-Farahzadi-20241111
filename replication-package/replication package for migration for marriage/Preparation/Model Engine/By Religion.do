* Estimate the baseline model, prepare counterfactual inputs, and calculate
* the estimated preference contrasts.
* Standalone inputs: cleaned Census DTA; output directory for model files;
* religion code to analyse (default 6 = Muslim); religion label.
* Optional fifth argument: 1 treats adult migrants whose spouse obtained a UK
* university degree as resident spouses (Appendix Table A7 sensitivity).
* Optional sixth argument: 1 treats linked cohabiters as couples for estimation.
* Example: do "Preparation\Model Engine\By Religion.do" ///
*     "data.dta" "outdir" 4 "Hindu"
args input_dta model_dir relcode relname exclude_uk_degree cohabitation_as_marriage
if `"`input_dta'"' == "" local input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`model_dir'"' == "" local model_dir "Synthetic Data\model_out"
if `"`relcode'"' == "" local relcode 6
if `"`relname'"' == "" local relname "Muslim"
if `"`exclude_uk_degree'"' == "" local exclude_uk_degree 0
if `"`cohabitation_as_marriage'"' == "" local cohabitation_as_marriage 0
capture mkdir "`model_dir'"

* Helper: D = b[a] + b[b] - b[d] - b[e] and its s.e. sqrt(L V L'),
* using the margins results in _b0 and _V0. Writes estimate to C[r,c]
* and standard error to C[r+1,c].
capture program drop dcon
program define dcon
    args r c a b d e
    tempname L est v
    matrix `L' = J(1, colsof(_b0), 0)
    matrix `L'[1,`a'] = 1
    matrix `L'[1,`b'] = 1
    matrix `L'[1,`d'] = -1
    matrix `L'[1,`e'] = -1
    matrix `est' = `L' * _b0'
    matrix `v'   = `L' * _V0 * `L''
    matrix C[`r',`c']     = `est'[1,1]
    matrix C[`r'+1,`c']   = sqrt(`v'[1,1])
end

use "`input_dta'", clear
if `cohabitation_as_marriage' == 1 {
    replace single = 0 if cohabiting == 1 & !missing(coupleid)
}
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

* Map detailed ethnicity groups to the model's categories.
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

* Religion indicator: 1 if religion == relcode, 0 otherwise (code 9 excluded)
gen rel = religion == `relcode'
replace rel = . if missing(religion) | religion == 9
gen srel = sreligion == `relcode'
replace srel = . if missing(sreligion) | sreligion == 9

quietly count if rel == 1
if r(N) == 0 {
    display as error "No observations with religion == `relcode'"
    exit 2000
}

gen sadult_immig = simmigrant18 == 1 & sethnicityew == ethnicityew & ethnicityew != 1 if ethnicity != 2
replace sadult_immig = -9 if simmigrant18 == -9
replace sadult_immig = . if missing(simmigrant18)
drop if sadult_immig == -9

if `exclude_uk_degree' == 1 {
    replace sadult_immig = 0 if sadult_immig == 1 & (squals08 == 1 | squals09 == 1) & (squals12 == 0 & squals14 == 0)
}

gen group = age_group*1000 + ethnic_group*100 + rel*10 + tertiary_edu
gen sgroup = sage_group*1000 + sethnic_group*100 + srel*10 + stertiary_edu
drop if missing(group)
drop if missing(sgroup) & !missing(coupleid)
gen N = 1

* weights for average ethnic endogamy preference
quietly count if rel == 1 & ethnic_group != 0 & !missing(ethnic_group)
local tot = r(N)
forvalues g = 1/4 {
    quietly count if rel == 1 & ethnic_group == `g'
    local w`g' = r(N)/`tot'
}

tempfile model_sample women_counts men_counts
save `model_sample'
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
save "`model_dir'\dist.dta", replace
preserve
keep group nx
save "`model_dir'\nx.dta", replace
restore
rename group sgroup
keep sgroup ny
save "`model_dir'\ny.dta", replace
use `model_sample', clear

preserve
keep if sadult_immig == 0 & single == 0 & sex == 2
collapse (sum) N, by(group sgroup)
rename N muxy
save "`model_dir'\muxy.dta", replace
restore
preserve
keep if sadult_immig == 1 & single == 0 & sex == 2
collapse (sum) N, by(group sgroup)
rename N lxy
save "`model_dir'\lxy.dta", replace
restore
preserve
keep if sadult_immig == 1 & single == 0 & sex == 1
collapse (sum) N, by(group sgroup)
rename group temp
rename sgroup group
rename temp sgroup
rename N lyx
save "`model_dir'\lyx.dta", replace
restore
preserve
keep if single == 1 & sex == 2
collapse (sum) N, by(group)
rename N mux0
save "`model_dir'\mux0.dta", replace
restore
keep if single == 1 & sex == 1
collapse (sum) N, by(group)
rename group sgroup
rename N mu0y
save "`model_dir'\mu0y.dta", replace

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

merge 1:1 group sgroup using "`model_dir'\muxy.dta", nogen
merge 1:1 group sgroup using "`model_dir'\lxy.dta", nogen
merge 1:1 group sgroup using "`model_dir'\lyx.dta", nogen
merge m:1 group using "`model_dir'\mux0.dta", nogen
merge m:1 sgroup using "`model_dir'\mu0y.dta", nogen
sort group sgroup

///////// beta ///////////

egen N = total(muxy)

replace muxy = 0 if muxy == .
local delta = 0.01
replace muxy = N*(muxy + `delta')/(N+`delta')

gen dE = 2*log(muxy/sqrt(mux0*mu0y))

reg dE a_x##a_y##r_x##r_y r_x##r_y##e_x##e_y r_x##r_y##s_x##s_y

predict phi, xb
preserve
rename group groupx
rename sgroup groupy
keep groupx groupy phi
save "`model_dir'\phi.dta", replace
restore

preserve
gen D_men = lyx*sqrt(mux0)/muxy
gen D_women = lxy*sqrt(mu0y)/muxy
replace D_men = 0 if D_men == . | muxy == N*(`delta')/(N+`delta')
replace D_women = 0 if D_women == . | muxy == N*(`delta')/(N+`delta')
rename group groupx
rename sgroup groupy
keep groupx groupy D_men D_women
save "`model_dir'\d.dta", replace
restore

bys a_x a_y s_x s_y r_x r_y: egen temp1 = total(phi*muxy)
bys a_x a_y s_x s_y r_x r_y: egen temp2 = total(muxy)
gen phi_e = temp1/temp2
drop temp*
preserve
rename group groupx
rename sgroup groupy
keep groupx groupy phi_e
save "`model_dir'\phi_e.dta", replace
restore

bys a_x a_y s_x s_y e_x e_y: egen temp1 = total(phi*muxy)
bys a_x a_y s_x s_y e_x e_y: egen temp2 = total(muxy)
gen phi_r = temp1/temp2
drop temp*
preserve
rename group groupx
rename sgroup groupy
keep groupx groupy phi_r
save "`model_dir'\phi_r.dta", replace
restore

bys a_x a_y s_x s_y: egen temp1 = total(phi*muxy)
bys a_x a_y s_x s_y: egen temp2 = total(muxy)
gen phi_er = temp1/temp2
drop temp*
preserve
rename group groupx
rename sgroup groupy
keep groupx groupy phi_er
save "`model_dir'\phi_er.dta", replace
restore

* C: rows 2k-1 = estimate, 2k = standard error of contrast k
* Column 1: other religions (r=0); column 2: chosen religion (r=1)
* margins cell order for a 3x3 factor: (1,1)=1 (1,2)=2 (1,3)=3 (2,1)=4 ...
matrix C = J(18,2,.)

forvalues c = 1/2 {
    local rr = `c' - 1

    * Age: young-middle, young-old, middle-old
    quietly margins a_x#a_y [pw=muxy], at(r_x==`rr' r_y==`rr')
    matrix _b0 = r(b)
    matrix _V0 = r(V)
    dcon 1 `c' 1 5 2 4
    dcon 3 `c' 1 9 3 7
    dcon 5 `c' 5 9 6 8

    * Education: less than college vs college or more (2x2)
    quietly margins s_x#s_y [pw=muxy], at(r_x==`rr' r_y==`rr')
    matrix _b0 = r(b)
    matrix _V0 = r(V)
    dcon 7 `c' 1 4 2 3

    * Ethnicity vs White British (5x5: cell (i,j) = 5*i + j + 1)
    quietly margins e_x#e_y [pw=muxy], at(r_x==`rr' r_y==`rr')
    matrix _b0 = r(b)
    matrix _V0 = r(V)
    dcon 9  `c' 7  1 2 6
    dcon 11 `c' 13 1 3 11
    dcon 13 `c' 19 1 4 16
    dcon 15 `c' 25 1 5 21
}

* Religion (2x2), same for both columns
quietly margins r_x#r_y [pw=muxy]
matrix _b0 = r(b)
matrix _V0 = r(V)
dcon 17 1 4 1 2 3
dcon 17 2 4 1 2 3

matrix list C

* Weighted-average ethnic endogamy (chosen religion) with s.e. from the full
* covariance matrix of the margins; weights w1-w4 treated as fixed.
quietly margins e_x#e_y [pw=muxy], at(r_x==1 r_y==1)
matrix _b0 = r(b)
matrix _V0 = r(V)
matrix Lw = J(1, colsof(_b0), 0)
forvalues g = 1/4 {
    local pa = 6*`g' + 1
    local pb = `g' + 1
    local pc = 5*`g' + 1
    matrix Lw[1,`pa'] = Lw[1,`pa'] + `w`g''
    matrix Lw[1,1]    = Lw[1,1]    + `w`g''
    matrix Lw[1,`pb'] = Lw[1,`pb'] - `w`g''
    matrix Lw[1,`pc'] = Lw[1,`pc'] - `w`g''
}
matrix eth_e = Lw * _b0'
matrix eth_v = Lw * _V0 * Lw'
local eth_est = eth_e[1,1]
local eth_se  = sqrt(eth_v[1,1])
display "Ethnic endogamy (`relname') = `eth_est' (s.e. `eth_se')"

* Export the nine estimated preference contrasts and their standard errors.
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
replace comparison = "`relname' and non-`relname'" if contrast_id == 9
order contrast_id category comparison estimate_other se_other ///
    estimate_rel se_rel
export delimited using "`model_dir'\Estimated Preferences - `relname'.csv", replace

clear
set obs 1
gen rel_est = C[17,2]
gen rel_se  = C[18,2]
gen eth_est = `eth_est'
gen eth_se  = `eth_se'
export delimited using "`model_dir'\Endogamy - `relname'.csv", replace