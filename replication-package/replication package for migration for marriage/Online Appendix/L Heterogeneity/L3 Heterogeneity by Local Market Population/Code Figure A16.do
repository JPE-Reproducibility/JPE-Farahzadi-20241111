* Online Appendix Figure A16: Muslim population share and marriage migration
* across regions, using the following statistics:
*   proportion sadult_immig if ethnicityew != 1 & muslim == 1, over(region)
*   proportion muslim, over(region)
* The Muslim share uses the full prepared sample (data_facts.dta); marriage
* migration is the share of Muslim non-White-British residents with an adult
* migrant spouse. Error bars are 95% confidence intervals (1.96 standard errors).
* Nothing plotted is hard-coded.
*
* Arguments: data_facts.dta path, output directory.
args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear
keep if !missing(region)

tempfile share
preserve
collapse (mean) muslim_share=muslim, by(region)
replace muslim_share = 100 * muslim_share
save `share'
restore

keep if muslim == 1 & ethnicityew != 1 & !missing(ethnicityew) & !missing(sadult_immig)
collapse (mean) migration_rate=sadult_immig (semean) migration_se=sadult_immig ///
    (count) n=sadult_immig, by(region)
merge 1:1 region using `share', nogen

gen double migration_pct = 100 * migration_rate
gen double error_pct = 100 * 1.96 * migration_se
gen double migration_pct_lo = migration_pct - error_pct
gen double migration_pct_hi = migration_pct + error_pct

* Region codes follow the Census order used in the paper figure.
gen str3 region_label = ""
local i 0
foreach r in NE NW YH EM WM EE GL SE SW W {
    local ++i
    replace region_label = "`r'" if region == `i'
}
sort region

export delimited region region_label muslim_share n migration_rate migration_pct error_pct ///
    using "`output_dir'\Figure A16 Marriage migration by region data.csv", replace

twoway (rcap migration_pct_lo migration_pct_hi muslim_share, lcolor(black)) ///
    (scatter migration_pct muslim_share, mcolor(black) msymbol(Oh) ///
        mlabel(region_label) mlabposition(3) mlabcolor(black)), ///
    xlabel(0(2)8) ylabel(0(10)70, angle(horizontal) grid) ///
    xtitle("Muslim Population (%)") ytitle("Marriage Migration (%)") ///
    legend(off) graphregion(color(white)) plotregion(color(white))
graph export "`output_dir'\Figure A16 Marriage migration by region.png", replace width(1600)
display as result "Figure A16 graph and data saved to: `output_dir'"
