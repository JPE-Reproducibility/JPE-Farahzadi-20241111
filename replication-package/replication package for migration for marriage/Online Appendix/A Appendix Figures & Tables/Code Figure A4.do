* Online Appendix Figure A4: educational attainment of marriage migrants
* (UK Census 2011) and of the origin-country population (India DHS 1998-99;
* Pakistan Census 1998 and Bangladesh Census 2001 via IPUMS-International).
* All shares are calculated from the data. Run from the package root.
*
* Arguments: prepared UK dataset, India DHS members file, IPUMS extract,
* output directory. Defaults use the synthetic files.
args uk_dta india_dta ipums_dta output_dir
if `"`uk_dta'"' == "" local uk_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`india_dta'"' == "" local india_dta "Synthetic Data\DHS India\IAPR42FL synthetic.dta"
if `"`ipums_dta'"' == "" local ipums_dta "Synthetic Data\IPUMS\ipumsi synthetic.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

* country: 1 India, 2 Pakistan, 3 Bangladesh. sex: 1 men, 2 women.
* edu_cat: 1 below secondary, 2 secondary, 3 tertiary.
tempfile migrants india_pop ipums_pop

* Marriage migrants: spouses of UK-raised individuals of Indian (sethnicity
* 3), Pakistani (4) or Bangladeshi (5) ethnicity who arrived at 18+. The panel sex is the UK-raised
* respondent's own sex (1 men, 2 women), not the migrant spouse's sex, and
* spouse education uses the raw ISCED codes (2, 3, 5 after merging 6 into 5)
* rather than grouped ranges; ISCED 1 and 4 are excluded.
use "`uk_dta'", clear
keep if inlist(sethnicity, 3, 4, 5)
replace sedu_level = 5 if sedu_level == 6
gen byte country = sethnicity - 2
gen byte edu_cat = sedu_level if inlist(sedu_level, 2, 3, 5)
recode edu_cat (2 = 1) (3 = 2) (5 = 3)
gen double w = 1
collapse (sum) w if sadult_immig == 1, by(country sex edu_cat)
drop if missing(edu_cat)
gen byte source = 1
save `migrants'

* India: DHS 1998-99. hv106 0 none, 1 primary, 2 secondary, 3 higher; sex from
* the sh54 sub-sample.
use "`india_dta'", clear
keep if inlist(hv106, 0, 1, 2, 3) & inlist(sh54, 1, 2)
gen byte edu_cat = max(hv106, 1)
gen byte sex = sh54
gen byte country = 1
collapse (sum) w=hv005, by(country sex edu_cat)
gen byte source = 2
save `india_pop'

* Pakistan 1998 and Bangladesh 2001: IPUMS edattain 1 less than primary,
* 2 primary, 3 secondary, 4 university. Ages match the preparation script's
* analysis windows (men 25-54, women 23-52).
use "`ipums_dta'", clear
keep if inlist(sample, 586199801, 50200101) & inrange(edattain, 1, 4)
keep if (sex == 1 & inrange(age, 25, 54)) | (sex == 2 & inrange(age, 23, 52))
gen byte country = cond(sample == 586199801, 2, 3)
gen byte edu_cat = cond(edattain <= 2, 1, cond(edattain == 3, 2, 3))
collapse (sum) w=perwt, by(country sex edu_cat)
gen byte source = 2
save `ipums_pop'

use `migrants', clear
append using `india_pop'
append using `ipums_pop'

bysort country sex source: egen double group_total = total(w)
gen double share_pct = 100 * w / group_total
gen double plot_x = edu_cat + cond(source == 1, -.18, .18)

label define country_label 1 "India" 2 "Pakistan" 3 "Bangladesh"
label values country country_label
label define sex_label 1 "Men" 2 "Women"
label values sex sex_label
label define source_label 1 "Marriage migrants" 2 "Origin-country population"
label values source source_label
label define edu_label 1 "< Secondary" 2 "Secondary" 3 "Tertiary"
label values edu_cat edu_label

sort country sex source edu_cat
export delimited country sex source edu_cat w share_pct ///
    using "`output_dir'\Figure A4.csv", replace

local letters a b c d e f
local countries India Pakistan Bangladesh
local sexes Men Women
local panels ""
forvalues c = 1/3 {
    forvalues s = 1/2 {
        local panel = (`c' - 1) * 2 + `s'
        local letter : word `panel' of `letters'
        local cname : word `c' of `countries'
        local sname : word `s' of `sexes'
        local legopt "legend(off)"
        if `panel' == 1 {
            local legopt `"legend(order(1 "Marriage migrants" 2 "Origin-country population") rows(1) size(vsmall) position(12))"'
        }
        twoway ///
            (bar share_pct plot_x if country == `c' & sex == `s' & source == 1, ///
                barwidth(.34) color(ltblue) lcolor(black)) ///
            (bar share_pct plot_x if country == `c' & sex == `s' & source == 2, ///
                barwidth(.34) color(navy) lcolor(black)), ///
            xlabel(1 "< Secondary" 2 "Secondary" 3 "Tertiary", labsize(small)) ///
            xscale(range(.5 3.5)) yscale(range(0 100)) ///
            ylabel(0(20)100, angle(horizontal) grid) ///
            xtitle("") ytitle("Proportion (%)") ///
            title("(`letter') `cname': `sname'", size(medsmall)) ///
            `legopt' graphregion(color(white)) name(panel`panel', replace)
        local panels "`panels' panel`panel'"
    }
}

graph combine `panels', cols(2) graphregion(color(white))
graph export "`output_dir'\Figure A4.png", replace width(2000)
display as result "Figure A4 data and graph saved to: `output_dir'"
