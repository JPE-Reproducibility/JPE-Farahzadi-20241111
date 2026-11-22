* Online Appendix Figure A2: share actively practicing individuals, by
* religion and nativity, using the 2010-2011 Citizenship Survey or a
* synthetic file with the same variables. Run from the package root.

args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Synthetic Data\Citizenship Survey\citizenship survey synthetic.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear

foreach var in Relig hcoba relprac WtFInds {
    capture confirm numeric variable `var'
    if _rc {
        display as error "Numeric variable `var' is required in `input_dta'."
        exit 111
    }
}

* The published figure treats all other birthplace codes, including refusals
* and missing responses, as immigrant rather than excluding them.
gen byte uk_born = inrange(hcoba, 1, 5)
keep if inrange(Relig, 1, 7) & inlist(relprac, 0, 1)
keep if WtFInds > 0 & !missing(WtFInds)

gen byte religion_order = Relig
gen str16 religion_group = ""
replace religion_group = "Christian" if religion_order == 1
replace religion_group = "Buddhist" if religion_order == 2
replace religion_group = "Hindu" if religion_order == 3
replace religion_group = "Jewish" if religion_order == 4
replace religion_group = "Muslim" if religion_order == 5
replace religion_group = "Sikh" if religion_order == 6
replace religion_group = "Other" if religion_order == 7

collapse (mean) practice_share=relprac (rawsum) weighted_n=WtFInds ///
    [aw=WtFInds], by(religion_order religion_group uk_born)
gen double practice_pct = 100 * practice_share

sort religion_order uk_born
order religion_order religion_group uk_born weighted_n practice_share practice_pct
export delimited religion_order religion_group uk_born weighted_n practice_share practice_pct ///
    using "`output_dir'\Figure A2.csv", replace

gen double plot_x = religion_order + cond(uk_born == 1, -.18, .18)
twoway ///
    (bar practice_pct plot_x if uk_born == 1, ///
        barwidth(.34) color(ltblue)) ///
    (bar practice_pct plot_x if uk_born == 0, ///
        barwidth(.34) color(navy)), ///
    xlabel(1 "Christian" 2 "Buddhist" 3 "Hindu" 4 "Jewish" 5 "Muslim" 6 "Sikh" 7 "Other") ///
    xscale(range(.5 7.5)) ///
    yscale(range(0 100)) ylabel(0(10)100, angle(horizontal)) ///
    xtitle("Religion") ytitle("Percentage") ///
    legend(order(1 "UK-born" 2 "Immigrant") rows(1) position(12)) ///
    graphregion(color(white))

graph export "`output_dir'\Figure A2.png", replace width(1600)
display as result "Figure A2 graph and data saved to: `output_dir'"
