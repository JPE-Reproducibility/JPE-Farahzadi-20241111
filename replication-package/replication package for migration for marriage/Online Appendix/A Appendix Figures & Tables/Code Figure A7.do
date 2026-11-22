* Online Appendix Figure A7: marriage migration by age for Hindu, Muslim and
* Sikh respondents.
* The figure is calculated from the prepared reduced-form dataset; no plotted
* values are hard-coded.
*
* Arguments: data_facts.dta path, output directory.
args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"


use "`input_dta'", clear

* Religion codes in the Census data: Hindu=4, Muslim=6, Sikh=7.
* Five-year bins cover ages 30-54.
keep if inlist(religion, 4, 6, 7) & inrange(age, 30, 54)
gen byte age_midpoint = 32 + 5 * floor((age - 30) / 5)
keep if inlist(sadult_immig, 0, 1)

collapse (mean) migration_rate=sadult_immig (count) n=sadult_immig, ///
    by(religion age_midpoint)
gen double migration_pct = 100 * migration_rate
label define religion_a8 4 "Hindu" 6 "Muslim" 7 "Sikh"
label values religion religion_a8
sort religion age_midpoint

export delimited religion age_midpoint n migration_rate migration_pct ///
    using "`output_dir'\Figure A7.csv", replace

twoway ///
    (connected migration_pct age_midpoint if religion == 4, ///
        lcolor(teal) mcolor(teal) msymbol(square)) ///
    (connected migration_pct age_midpoint if religion == 6, ///
        lcolor(purple) mcolor(purple) msymbol(triangle)) ///
    (connected migration_pct age_midpoint if religion == 7, ///
        lcolor(black) mcolor(black) msymbol(circle)), ///
    xlabel(32(5)52) xscale(range(30 55)) ///
    ylabel(0(10)60, angle(horizontal) grid) yscale(range(0 60)) ///
    xtitle("Age (group midpoint)") ytitle("Marriage Migration (%)") ///
    legend(order(1 "Hindu" 2 "Muslim" 3 "Sikh") rows(1) position(12)) ///
    graphregion(color(white)) plotregion(color(white))

graph export "`output_dir'\Figure A7.png", replace width(1600)
display as result "Figure A7 graph and data saved to: `output_dir'"
