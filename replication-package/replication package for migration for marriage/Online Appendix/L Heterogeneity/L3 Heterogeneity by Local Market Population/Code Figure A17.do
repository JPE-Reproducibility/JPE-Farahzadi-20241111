* Online Appendix Figure A17: Marriage migration in high and low Muslim
* population local authorities.
*
* High Muslim population: la_muslim_share > 0.1. Low Muslim population:
* la_muslim_share < 0.1. Local authorities with a share of exactly 0.1 or a
* missing share are in neither group. The baseline model (Code Table 4.do) is
* estimated separately on each sample and the marriage-migration decomposition
* (overall, outside market value, endogamy preferences) comes from the Figure 4
* implementation.
*
* Run from the replication-package root:
* do "Online Appendix\L Heterogeneity\L3 Heterogeneity by Local Market Population\Code Figure A17.do" ///
*   "cleaned_census.dta" "work_dir" "output_dir" "python.exe"
args input_dta work_root output_dir python_exe
if `"`input_dta'"' == "" local input_dta "Synthetic Data\Census\synthetic_cleaned.dta"
if `"`work_root'"' == "" local work_root "Synthetic Data\model_out\Figure A17"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
if `"`python_exe'"' == "" local python_exe "python"

capture confirm file `"`input_dta'"'
if _rc {
    display as error "Cleaned Census data not found: `input_dta'"
    exit 601
}
capture mkdir "`work_root'"
capture mkdir "`output_dir'"
local high_dir "`work_root'\high"
local low_dir "`work_root'\low"
capture mkdir "`high_dir'"
capture mkdir "`low_dir'"

use "`input_dta'", clear
capture confirm variable la_muslim_share
if _rc {
    display as error "la_muslim_share not found in `input_dta'"
    exit 111
}
quietly count if la_muslim_share > 0.1 & !missing(la_muslim_share)
if r(N) == 0 {
    display as error "Figure A17 requires observations with la_muslim_share > 0.1."
    exit 2000
}
quietly count if la_muslim_share < 0.1
if r(N) == 0 {
    display as error "Figure A17 requires observations with la_muslim_share < 0.1."
    exit 2000
}
preserve
keep if la_muslim_share > 0.1 & !missing(la_muslim_share)
save "`high_dir'\data.dta", replace
restore
keep if la_muslim_share < 0.1
save "`low_dir'\data.dta", replace

noisily do "Paper\5 Results\Code Table 4.do" ///
    "`high_dir'\data.dta" "`high_dir'" "`high_dir'" 6 "Muslim" 0
noisily do "Paper\5 Results\Code Table 4.do" ///
    "`low_dir'\data.dta" "`low_dir'" "`low_dir'" 6 "Muslim" 0

local rates_csv "`output_dir'\Figure A17 data.csv"
local observed_csv "`work_root'\observed_rates.csv"
capture erase "`rates_csv'"

* Observed rates: share of Census respondents with an adult-immigrant spouse of
* the same ethnicity, among ethnicityew != 1, by Muslim and sex (Figure 4 input).
tempname post
tempfile observed_dta
postfile `post' str5 area str10 religion str5 sex double observed_percent using `observed_dta', replace
foreach area in high low {
    use "``area'_dir'\data.dta", clear
    gen sadult_immig = simmigrant18 == 1 & sethnicityew == ethnicityew & ethnicityew != 1 if ethnicity != 2
    replace sadult_immig = . if missing(simmigrant18) | simmigrant18 == -9
    gen muslim = religion == 6 if !missing(religion) & religion != 9
    foreach m in 0 1 {
        foreach s in 1 2 {
            quietly summarize sadult_immig if ethnicityew != 1 & muslim == `m' & sex == `s'
            local rel = cond(`m' == 1, "Muslim", "Non-Muslim")
            local sx = cond(`s' == 1, "Men", "Women")
            post `post' ("`area'") ("`rel'") ("`sx'") (100 * r(mean))
        }
    }
}
postclose `post'
use `observed_dta', clear
export delimited using "`observed_csv'", replace

shell "`python_exe'" "Online Appendix\L Heterogeneity\L3 Heterogeneity by Local Market Population\figure_a17_migration.py" --high-dir "`high_dir'" --low-dir "`low_dir'" --observed "`observed_csv'" --output "`rates_csv'"
capture confirm file "`rates_csv'"
if _rc {
    display as error "Python decomposition did not produce `rates_csv'. See the Python error above."
    exit 601
}

import delimited using "`rates_csv'", clear varnames(1)
gen byte muslim = lower(subinstr(religion, "-", "_", .)) == "muslim"
gen byte area_order = cond(area == "low", 1, 2)
label define density_label 1 "Low density" 2 "High density"
label values area_order density_label
label define religion_label 0 "Non-Muslim" 1 "Muslim"
label values muslim religion_label
sort area_order muslim

graph hbar (asis) outside_market_value endogamy_preferences, stack ///
    over(muslim) over(area_order) ///
    ytitle("Marriage Migration (%)") ///
    legend(order(1 "Outside market value" 2 "Endogamy preferences") rows(1)) ///
    graphregion(color(white)) plotregion(color(white))
graph export "`output_dir'\Figure A17 Marriage migration by Muslim population.png", replace width(1600)
display as result "Figure A17 graph and data saved to: `output_dir'"
