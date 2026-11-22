* Appendix Table A13: Estimated Endogamy Preferences by Census Year (2011 vs 2001)
* Creates person-and-spouse records from the raw Census files using
* "Preparation\Data Cleaning\census_comparison_cleaning.py".
*
* Marriage-migrant definition used for the comparison (differs from the baseline
* arrival-year definition because the 2001 Census has no year-of-arrival match):
*   - only UK-born individuals are kept (immigrant == 0);
*   - a UK-born person's marriage is a marriage-migrant match when the spouse is
*     foreign-born, has the same detailed ethnicity, and the person is not White
*     British. These matches are excluded from the native matching counts mu_xy
*     (their spouses are not part of the UK-born marriage market), and singles
*     are counted without any migrant filter.
* Ethnicity contrasts are not reported in the paper table (small 2001 samples),
* so only the education and religion contrasts are computed.
*
* D_zz' = Phi_zz + Phi_z'z' - Phi_zz' - Phi_z'z, Phi = 2*log(mu_xy / sqrt(mu_x0*mu_0y)),
* with +0.01 smoothing. Standard errors use the
* full covariance matrix returned by margins for each four-margin contrast.
*
* Run from the replication-package root.
* This workflow processes both Census years and can take a long time. For
* easier monitoring, run incrementally by complete sections in Stata's
* Do-file Editor and check the log between sections; later sections depend on
* files and state created earlier.
* Usage:
* do "Online Appendix\L Heterogeneity\L1 Heterogeneity by Cohort and Period\Code Table A13.do" ///
*   "raw_2001.dta" "raw_2011.csv" "work_dir" "output_dir" "python.exe"
args data2001 data2011 work_dir output_dir python_exe
if `"`data2001'"' == "" local data2001 "Synthetic Data\Census\synthetic_census_ew_2001.csv"
if `"`data2011'"' == "" local data2011 "Synthetic Data\Census\synthetic_census_ew_2011.csv"
if `"`work_dir'"' == "" local work_dir "Synthetic Data\Census"
if `"`output_dir'"' == "" {
    local output_dir "Online Appendix\Output"
}
if `"`python_exe'"' == "" local python_exe "python"
capture mkdir "`work_dir'"
capture mkdir "`output_dir'"

* Prepare the comparison-specific person/spouse files before their fields are
* referenced below. The raw Census files do not contain the derived immigrant
* or spouse variables used by the table.
local clean2001 "`work_dir'\data2001.csv"
local clean2011 "`work_dir'\data2011.csv"
global a13_python `"`python_exe'"'
global a13_data2001 `"`data2001'"'
global a13_data2011 `"`data2011'"'
global a13_clean2001 `"`clean2001'"'
global a13_clean2011 `"`clean2011'"'
capture erase "`clean2001'"
shell "$a13_python" "Preparation\Data Cleaning\census_comparison_cleaning.py" ///
    --year 2001 "$a13_data2001" "$a13_clean2001"
capture confirm file "`clean2001'"
if _rc {
    display as error "2001 comparison cleaning did not produce: `clean2001'"
    display as error "Check the raw Census input and Python executable."
    exit 601
}
capture erase "`clean2011'"
shell "$a13_python" "Preparation\Data Cleaning\census_comparison_cleaning.py" ///
    --year 2011 "$a13_data2011" "$a13_clean2011"
capture confirm file "`clean2011'"
if _rc {
    display as error "2011 comparison cleaning did not produce: `clean2011'"
    display as error "Check the raw Census input and Python executable."
    exit 601
}

capture program drop a13_observed
program define a13_observed
    args csvfile year outdir

    import delimited using "`csvfile'", clear
    keep if immigrant == 0

    foreach x of varlist age sage sex ethnicity sethnicity religion sreligion ///
        tertiary_education stertiary_education {
        replace `x' = . if `x' < 0
    }
    if `year' == 2001 {
        * Shift 2001 religion codes so that 6 = Muslim.
        replace religion = 0 if religion == 8
        replace religion = religion + 1 if religion >= 0 & religion < 8
        replace sreligion = 0 if sreligion == 8
        replace sreligion = sreligion + 1 if sreligion >= 0 & sreligion < 8
    }

    capture confirm string variable coupleid
    if _rc == 0 {
        gen byte incouple = coupleid != ""
    }
    else {
        gen byte incouple = coupleid != .
    }
    keep if incouple == 1 | single == 1

    gen age_group = 1 if (sex == 2 & age >= 23 & age <= 32) | (sex == 1 & age >= 25 & age <= 34)
    replace age_group = 2 if (sex == 2 & age >= 33 & age <= 42) | (sex == 1 & age >= 35 & age <= 44)
    replace age_group = 3 if (sex == 2 & age >= 43 & age <= 52) | (sex == 1 & age >= 45 & age <= 54)

    gen sage_group = 1 if (sex == 1 & sage >= 23 & sage <= 32) | (sex == 2 & sage >= 25 & sage <= 34)
    replace sage_group = 2 if (sex == 1 & sage >= 33 & sage <= 42) | (sex == 2 & sage >= 35 & sage <= 44)
    replace sage_group = 3 if (sex == 1 & sage >= 43 & sage <= 52) | (sex == 2 & sage >= 45 & sage <= 54)

    keep if (age_group != . & sage_group != .) | (age_group != . & single == 1)

    gen ethnic_group = 1 if ethnicity == 1
    replace ethnic_group = 0 if ethnicity == 0
    replace ethnic_group = 2 if ethnicity == 3
    replace ethnic_group = 3 if ethnicity == 4 | ethnicity == 5
    replace ethnic_group = 4 if ethnicity >= 6
    replace ethnic_group = . if ethnicity == .

    gen sethnic_group = 1 if sethnicity == 1
    replace sethnic_group = 0 if sethnicity == 0
    replace sethnic_group = 2 if sethnicity == 3
    replace sethnic_group = 3 if sethnicity == 4 | sethnicity == 5
    replace sethnic_group = 4 if sethnicity >= 6
    replace sethnic_group = . if sethnicity == .

    gen muslim = religion == 6
    replace muslim = . if religion == . | religion == 9

    gen smuslim = sreligion == 6
    replace smuslim = . if sreligion == . | sreligion == 9

    gen sadult_immig = simmigrant == 1 & sethnicity == ethnicity & ethnicity != 0 if ethnicity != 2
    replace sadult_immig = -9 if simmigrant == -9
    replace sadult_immig = . if simmigrant == .
    drop if sadult_immig == -9

    gen group = age_group*1000 + ethnic_group*100 + muslim*10 + tertiary_education
    gen sgroup = sage_group*1000 + sethnic_group*100 + smuslim*10 + stertiary_education

    drop if group == .
    drop if sgroup == . & incouple == 1

    gen N = 1
    capture mkdir "`outdir'/`year'"

    preserve
    keep if sadult_immig == 0
    keep if single == 0 & sex == 2
    collapse (sum) N, by(group sgroup)
    rename N muxy
    save "`outdir'/`year'/muxy.dta", replace

    restore
    preserve
    keep if single == 1 & sex == 2
    collapse (sum) N, by(group)
    rename N mux0
    save "`outdir'/`year'/mux0.dta", replace

    restore
    keep if single == 1 & sex == 1
    collapse (sum) N, by(group)
    rename group sgroup
    rename N mu0y
    save "`outdir'/`year'/mu0y.dta", replace
end

a13_observed "`clean2001'" 2001 "`work_dir'"
a13_observed "`clean2011'" 2011 "`work_dir'"

clear all
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

foreach y in 2001 2011 {
    merge 1:1 group sgroup using "`work_dir'/`y'/muxy.dta", nogen
    merge m:1 group using "`work_dir'/`y'/mux0.dta", nogen
    merge m:1 sgroup using "`work_dir'/`y'/mu0y.dta", nogen
    sort group sgroup

    egen N = total(muxy)
    replace muxy = 0 if muxy == .
    local delta = 0.01
    replace muxy = N*(muxy + `delta')/(N + `delta')
    gen phi`y' = 2*log(muxy/sqrt(mux0*mu0y))
    drop mux0 mu0y N
    rename muxy muxy`y'
}

foreach y in 2001 2011 {
    quietly reg phi`y' a_x##a_y##r_x##r_y r_x##r_y##e_x##e_y r_x##r_y##s_x##s_y

    foreach g in 0 1 {
        quietly margins s_x#s_y [pw=muxy`y'], at(r_x==`g' r_y==`g')
        matrix b = r(b)
        matrix v = r(V)
        local edu_est_`y'_`g' = b[1,1] + b[1,4] - b[1,2] - b[1,3]
        tempname contrast variance
        matrix `contrast' = (1,-1,-1,1)
        matrix `variance' = `contrast' * v * `contrast''
        local edu_var_`y'_`g' = `variance'[1,1]
    }

    quietly margins r_x#r_y [pw=muxy`y']
    matrix b = r(b)
    matrix v = r(V)
    local rel_est_`y' = b[1,4] + b[1,1] - b[1,2] - b[1,3]
    tempname contrast variance
    matrix `contrast' = (1,-1,-1,1)
    matrix `variance' = `contrast' * v * `contrast''
    local rel_var_`y' = `variance'[1,1]
}

tempname pf
tempfile results
postfile `pf' str12 section str40 contrast ///
    double(estimate_muslim_2011 variance_muslim_2011 se_muslim_2011 ///
           estimate_non_muslim_2011 variance_non_muslim_2011 se_non_muslim_2011 ///
           estimate_muslim_2001 variance_muslim_2001 se_muslim_2001 ///
           estimate_non_muslim_2001 variance_non_muslim_2001 se_non_muslim_2001) ///
    using `results'

local row_edu ""
foreach y in 2011 2001 {
    foreach g in 1 0 {
        local row_edu `row_edu' (`edu_est_`y'_`g'') (`edu_var_`y'_`g'') ///
            (cond(`edu_var_`y'_`g'' >= 0, sqrt(`edu_var_`y'_`g''), .))
    }
}
post `pf' ("Education") ("Less than college & College or more") `row_edu'

local row_rel ""
foreach y in 2011 2001 {
    foreach g in 1 0 {
        local row_rel `row_rel' (`rel_est_`y'') (`rel_var_`y'') ///
            (cond(`rel_var_`y'' >= 0, sqrt(`rel_var_`y''), .))
    }
}
post `pf' ("Religion") ("Muslim & Non-Muslim") `row_rel'
postclose `pf'

use `results', clear
drop variance_*
list, noobs abbreviate(24)
export delimited using "`output_dir'/Table A13.csv", replace
