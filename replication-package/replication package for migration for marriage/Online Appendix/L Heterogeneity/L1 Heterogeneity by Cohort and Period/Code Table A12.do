* Appendix Table A12: Estimated Endogamy Preferences by Age Cohort
* Read baseline model-count files, estimate age-interacted preferences,
* and evaluate D_zz' = Phi_zz + Phi_z'z' - Phi_zz' - Phi_z'z
* for Young / Middle-aged / Old couples, separately for Muslims and Non-Muslims.
* Run from the replication-package root.
* Usage:
* do "Online Appendix\L Heterogeneity\L1 Heterogeneity by Cohort and Period\Code Table A12.do" ///
*   "model_dir" "output_dir"
args model_dir output_dir
if `"`model_dir'"' == "" local model_dir "Synthetic Data\model_out"
if `"`output_dir'"' == "" {
    local output_dir "Online Appendix\Output"
}
capture mkdir "`output_dir'"

foreach name in muxy lxy lyx mux0 mu0y {
    local model_file = "`model_dir'" + char(92) + "`name'.dta"
    capture confirm file "`model_file'"
    if _rc {
        display as error "Required baseline model file not found: `model_file'"
        exit 601
    }
}

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

merge 1:1 group sgroup using "`model_dir'\muxy.dta", nogen
merge 1:1 group sgroup using "`model_dir'\lxy.dta", nogen
merge 1:1 group sgroup using "`model_dir'\lyx.dta", nogen
merge m:1 group using "`model_dir'\mux0.dta", nogen
merge m:1 sgroup using "`model_dir'\mu0y.dta", nogen
sort group sgroup

egen N = total(muxy)
replace muxy = 0 if muxy == .
local delta = 0.01
replace muxy = N*(muxy + `delta')/(N+`delta')

gen dE = 2*log(muxy/sqrt(mux0*mu0y))

* Interact age with the religion, education and ethnicity terms.
quietly reg dE a_x##a_y##r_x##r_y a_x##a_y##s_x##s_y a_x##a_y##e_x##e_y a_x##a_y##r_x# r_y##e_x##e_y r_x##r_y##s_x##s_y

local agelab1 "Young"
local agelab2 "Middle-aged"
local agelab3 "Old"
local grplab0 "Non-Muslim"
local grplab1 "Muslim"
local ethlab1 "Other White & White British"
local ethlab2 "Indian & White British"
local ethlab3 "Pak/Bng & White British"
local ethlab4 "Other & White British"

tempname pf
tempfile results
postfile `pf' order str12 section str40 contrast str10 group str12 age_group ///
    double(estimate variance se) using `results', replace

foreach k in 1 2 3 {
    foreach g in 0 1 {
        quietly margins s_x#s_y [pw=muxy], at(r_x==`g' r_y==`g' a_x==`k' a_y==`k')
        matrix b = r(b)
        matrix v = r(V)
        local est = b[1,1] + b[1,4] - b[1,2] - b[1,3]
        local var = v[1,1] + v[4,4] + v[2,2] + v[3,3] ///
            + 2*v[1,4] - 2*v[1,2] - 2*v[1,3] ///
            - 2*v[4,2] - 2*v[4,3] + 2*v[2,3]
        post `pf' (1) ("Education") ("Less than college & College or more") ///
            ("`grplab`g''") ("`agelab`k''") (`est') (`var') (cond(`var' >= 0, sqrt(`var'), .))

        quietly margins e_x#e_y [pw=muxy], at(r_x==`g' r_y==`g' a_x==`k' a_y==`k')
        matrix b = r(b)
        matrix v = r(V)
        forvalues j = 1/4 {
            local diag = 6*`j' + 1
            local cross1 = `j' + 1
            local cross2 = 5*`j' + 1
            local est = b[1,`diag'] + b[1,1] - b[1,`cross1'] - b[1,`cross2']
            local var = v[`diag',`diag'] + v[1,1] + v[`cross1',`cross1'] + v[`cross2',`cross2'] ///
                + 2*v[`diag',1] - 2*v[`diag',`cross1'] - 2*v[`diag',`cross2'] ///
                - 2*v[1,`cross1'] - 2*v[1,`cross2'] + 2*v[`cross1',`cross2']
            post `pf' (1+`j') ("Ethnicity") ("`ethlab`j''") ///
                ("`grplab`g''") ("`agelab`k''") (`est') (`var') (cond(`var' >= 0, sqrt(`var'), .))
        }

        if `g' == 0 {
            quietly margins r_x#r_y [pw=muxy], at(a_x==`k' a_y==`k')
            matrix b = r(b)
            matrix v = r(V)
            local religion_est = b[1,4] + b[1,1] - b[1,2] - b[1,3]
            local religion_var = v[1,1] + v[4,4] + v[2,2] + v[3,3] ///
                + 2*v[1,4] - 2*v[1,2] - 2*v[1,3] ///
                - 2*v[4,2] - 2*v[4,3] + 2*v[2,3]
        }
        post `pf' (6) ("Religion") ("Muslim & Non-Muslim") ///
            ("`grplab`g''") ("`agelab`k''") (`religion_est') (`religion_var') ///
            (cond(`religion_var' >= 0, sqrt(`religion_var'), .))
    }
}
postclose `pf'

use `results', clear
gen str30 column = cond(group == "Muslim", "muslim_", "non_muslim_") + ///
    cond(age_group == "Young", "young", cond(age_group == "Old", "old", "middle_aged"))
drop group age_group
reshape wide estimate variance se, i(order section contrast) j(column) string
sort order
drop order
export delimited using "`output_dir'\Table A12.csv", replace

display as result "Appendix Table A12 data written to `output_dir'\Table A12.csv"
