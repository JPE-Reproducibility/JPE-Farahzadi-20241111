* Online Appendix Figure A14: Muslim marriage migration by age group under two
* nativity definitions. This is a descriptive statistic from the cleaned Census
* data; no model is estimated.
*   - "UK-born or bred" (baseline): the resident sample used throughout the
*     paper (UK-born plus immigrants who arrived before age 18); a partner is a
*     marriage migrant if foreign-born, arrived at 18+ (sadult_immig as in
*     Code Prepare Reduced Form Data.do).
*   - "UK-born": residents are restricted to ukborn == 1 and any foreign-born
*     partner of the same detailed ethnicity counts (simmigrant == 1).
* Age groups follow the model (women 23-32/33-42/43-52, men 25-34/35-44/45-54).
* Sample: partnered Muslims who are not White British, excluding the mixed
* ethnic group, as in Figure 1.
*
* Arguments: cleaned person/spouse data (data.dta), output directory.
args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear
keep if !missing(coupleid)

gen byte age_group = 1 if (sex == 2 & inrange(age, 23, 32)) | (sex == 1 & inrange(age, 25, 34))
replace age_group = 2 if (sex == 2 & inrange(age, 33, 42)) | (sex == 1 & inrange(age, 35, 44))
replace age_group = 3 if (sex == 2 & inrange(age, 43, 52)) | (sex == 1 & inrange(age, 45, 54))
keep if !missing(age_group)

keep if religion == 6 & ethnicityew != 1 & !missing(ethnicityew) & ethnicity != 2

gen byte adult_baseline = simmigrant18 == 1 & sethnicityew == ethnicityew
replace adult_baseline = . if missing(simmigrant18) | simmigrant18 == -9
gen byte adult_ukborn = simmigrant == 1 & sethnicityew == ethnicityew if ukborn == 1

tempfile out
preserve
collapse (mean) rate=adult_baseline (count) n=adult_baseline, by(age_group)
gen str20 definition = "UK-born or bred"
save `out'
restore
collapse (mean) rate=adult_ukborn (count) n=adult_ukborn, by(age_group)
gen str20 definition = "UK-born"
append using `out'

gen double migration_pct = 100 * rate
label define age_a15 1 "Young" 2 "Middle-aged" 3 "Old"
label values age_group age_a15
sort definition age_group
export delimited age_group definition n rate migration_pct ///
    using "`output_dir'\Figure A14 Marriage migration by nativity data.csv", replace

graph bar migration_pct if definition == "UK-born" | definition == "UK-born or bred", ///
    over(definition) over(age_group) asyvars ///
    bar(1, color(navy%50)) bar(2, color(navy)) ///
    ytitle("Marriage migration (%)") ylabel(0(10)70, angle(horizontal) grid) ///
    legend(rows(1) position(12)) graphregion(color(white)) plotregion(color(white))
graph export "`output_dir'\Figure A14 Marriage migration by nativity.png", replace width(1600)
display as result "Figure A14 graph and data saved to: `output_dir'"
