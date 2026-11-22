* Online Appendix Figure A1: share of partnered men in cohabiting unions.
* Prepares the cohabitation data directly from the raw Census 2011 person file
* and calculates cohabitation shares by five-year age group and the man's
* religion. Run from the package root; arguments are the raw Census CSV and
* the output directory.

args input_csv output_dir
if `"`input_csv'"' == "" local input_csv "Synthetic Data\Census\synthetic_census_ew_2011.csv"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

import delimited using "`input_csv'", clear varnames(1) case(lower)
keep sex agec religionew hpartner hspouse

* Match the row percentages from tab age_group cohabiting, row.
gen byte cohabiting = 1 if hpartner == 2
replace cohabiting = 0 if hspouse == 2

rename agec age
rename religionew religion
keep if sex == 1 & inrange(age, 25, 54) & !missing(cohabiting)

gen byte muslim = religion == 6
gen byte age_group = floor((age - 25) / 5) + 1
label define age_group_label 1 "25-29" 2 "30-34" 3 "35-39" ///
    4 "40-44" 5 "45-49" 6 "50-54", replace
label values age_group age_group_label

collapse (mean) cohabiting_share=cohabiting (count) partnered_men=cohabiting, ///
    by(age_group muslim)
sort age_group muslim
order age_group muslim partnered_men cohabiting_share
export delimited age_group muslim partnered_men cohabiting_share ///
    using "`output_dir'\Figure A1.csv", replace

gen double plot_x = age_group + cond(muslim == 1, .18, -.18)
twoway ///
    (bar cohabiting_share plot_x if muslim == 0, ///
        barwidth(.34) color(ltblue)) ///
    (bar cohabiting_share plot_x if muslim == 1, ///
        barwidth(.34) color(navy)), ///
    xlabel(1 "25-29" 2 "30-34" 3 "35-39" 4 "40-44" 5 "45-49" 6 "50-54") ///
    xscale(range(.5 6.5)) ///
    yscale(range(0 .7)) ylabel(0(.1).7, angle(horizontal)) ///
    xtitle("Men's Age Group") ytitle("Proportion Cohabiting") ///
    legend(order(1 "Non-Muslim" 2 "Muslim") rows(1) position(12)) ///
    graphregion(color(white))

graph export "`output_dir'\Figure A1.png", replace width(1600)
display as result "Figure A1 data and graph saved to: `output_dir'"
