* Online Appendix Figure A3: inter-religious and inter-ethnic marriage rates,
* by ethnicity and religion (Muslim vs non-Muslim), with 95% confidence
* intervals. Calculated from the prepared reduced-form dataset.
args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear

* inter_relig and inter_ethnic are defined in the preparation script.
gen byte category = ethnicity
replace category = 2 if ethnicity == 3
replace category = 3 if ethnicity == 4
replace category = 4 if ethnicity == 5
replace category = 5 if ethnicity == 6
replace category = 6 if ethnicity == 7
replace category = 7 if ethnicity == 8
replace category = 8 if ethnicity == 9

replace religion = . if religion == 9
replace sreligion = . if sreligion == 9

tempfile relig ethnic

preserve
keep if !missing(inter_relig)
collapse (mean) rate=inter_relig (semean) se=inter_relig (count) n=inter_relig, ///
    by(category muslim)
gen str12 outcome = "inter_relig"
save `relig'
restore

keep if !missing(inter_ethnic)
collapse (mean) rate=inter_ethnic (semean) se=inter_ethnic (count) n=inter_ethnic, ///
    by(category muslim)
gen str12 outcome = "inter_ethnic"
save `ethnic'

use `relig', clear
append using `ethnic'

gen double rate_pct = 100 * rate
gen double lower_pct = max(0, 100 * (rate - invnormal(.975) * se))
gen double upper_pct = min(100, 100 * (rate + invnormal(.975) * se))
gen double plot_x = category + cond(muslim == 1, .18, -.18)
sort outcome category muslim

order outcome category muslim n rate_pct lower_pct upper_pct
export delimited outcome category muslim n rate_pct lower_pct upper_pct ///
    using "`output_dir'\Figure A3.csv", replace

local xlab `"1 "Non-British White" 2 "Indian" 3 "Pakistani" 4 "Bangladeshi" 5 "Other Asian" 6 "Black" 7 "Arab" 8 "Other""'

twoway ///
    (bar rate_pct plot_x if outcome == "inter_relig" & muslim == 0, barwidth(.34) color(ltblue) lcolor(black)) ///
    (bar rate_pct plot_x if outcome == "inter_relig" & muslim == 1, barwidth(.34) color(navy) lcolor(black)) ///
    (rcap upper_pct lower_pct plot_x if outcome == "inter_relig" & muslim == 0, lcolor(black)) ///
    (rcap upper_pct lower_pct plot_x if outcome == "inter_relig" & muslim == 1, lcolor(black)), ///
    xlabel(`xlab', labsize(vsmall)) xscale(range(.5 8.5)) ///
    yscale(range(0 100)) ylabel(0(20)100, angle(horizontal)) ///
    xtitle("") ytitle("Inter-religious Marriage (%)") ///
    title("Inter-religious marriage", size(medsmall)) ///
    legend(order(1 "Non-Muslim" 2 "Muslim") rows(1) position(12)) ///
    graphregion(color(white)) name(panel_relig, replace)

twoway ///
    (bar rate_pct plot_x if outcome == "inter_ethnic" & muslim == 0, barwidth(.34) color(ltblue) lcolor(black)) ///
    (bar rate_pct plot_x if outcome == "inter_ethnic" & muslim == 1, barwidth(.34) color(navy) lcolor(black)) ///
    (rcap upper_pct lower_pct plot_x if outcome == "inter_ethnic" & muslim == 0, lcolor(black)) ///
    (rcap upper_pct lower_pct plot_x if outcome == "inter_ethnic" & muslim == 1, lcolor(black)), ///
    xlabel(`xlab', labsize(vsmall)) xscale(range(.5 8.5)) ///
    yscale(range(0 100)) ylabel(0(20)100, angle(horizontal)) ///
    xtitle("Ethnic Group") ytitle("Inter-ethnic Marriage (%)") ///
    title("Inter-ethnic marriage", size(medsmall)) ///
    legend(order(1 "Non-Muslim" 2 "Muslim") rows(1) position(12)) ///
    graphregion(color(white)) name(panel_ethnic, replace)

graph combine panel_relig panel_ethnic, cols(1) imargin(small) graphregion(color(white))
graph export "`output_dir'\Figure A3.png", replace width(2000)
display as result "Figure A3 data and graph saved to: `output_dir'"
