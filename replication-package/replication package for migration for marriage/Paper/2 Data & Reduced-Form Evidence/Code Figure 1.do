* Main-text Figure 1: marriage migration rates by ethnicity and religion.
* Exports the plotted group means and 95% confidence intervals as a CSV and PNG.
* Run from the package root after preparing data_facts.dta.
args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Paper\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear
keep if ethnicityew != 1 & !missing(ethnicityew) /// Drop white British and missing
    & inlist(ethnicity, 1, 3, 4, 5, 6, 7, 8, 9) /// Exclude mixed ethnic group
    & inlist(muslim, 0, 1) & !missing(sadult_immig)

collapse (mean) migration_rate=sadult_immig ///
    (semean) migration_se=sadult_immig ///
    (count) n=sadult_immig, by(ethnicity muslim)

* Exclude mixed ethnicity and retain the eight categories shown in the paper.
gen byte category = ethnicity // Non-British White
replace category = 2 if ethnicity == 3 // Indian
replace category = 3 if ethnicity == 4 // Pakistani
replace category = 4 if ethnicity == 5 // Bangladeshi
replace category = 5 if ethnicity == 6 // Other Asian
replace category = 6 if ethnicity == 7 // Black
replace category = 7 if ethnicity == 8 // Arab
replace category = 8 if ethnicity == 9 // Other

gen double rate_pct = 100 * migration_rate
gen double lower_pct = max(0, 100 * (migration_rate - invnormal(.975) * migration_se))
gen double upper_pct = min(100, 100 * (migration_rate + invnormal(.975) * migration_se))
gen double plot_x = category + cond(muslim == 1, .18, -.18)
sort category muslim

order ethnicity category muslim n rate_pct lower_pct upper_pct
export delimited ethnicity category muslim n rate_pct lower_pct upper_pct ///
    using "`output_dir'\Figure 1.csv", replace

twoway ///
    (bar rate_pct plot_x if muslim == 0, barwidth(.34) color(ltblue) lcolor(black)) ///
    (bar rate_pct plot_x if muslim == 1, barwidth(.34) color(navy) lcolor(black)) ///
    (rcap upper_pct lower_pct plot_x if muslim == 0, lcolor(black)) ///
    (rcap upper_pct lower_pct plot_x if muslim == 1, lcolor(black)), ///
    xlabel(1 "Non-British White" 2 "Indian" 3 "Pakistani" 4 "Bangladeshi" ///
        5 "Other Asian" 6 "Black" 7 "Arab" 8 "Other", labsize(vsmall)) ///
    xscale(range(.5 8.5)) ///
    yscale(range(0 70)) ylabel(0(10)70, angle(horizontal)) ///
    xtitle("Ethnic Group") ytitle("Marriage Migration (%)") ///
    legend(order(1 "Non-Muslim" 2 "Muslim") rows(1) position(12)) ///
    graphregion(color(white))

graph export "`output_dir'\Figure 1.png", replace width(2000)
display as result "Figure 1 data and graph saved to: `output_dir'"
