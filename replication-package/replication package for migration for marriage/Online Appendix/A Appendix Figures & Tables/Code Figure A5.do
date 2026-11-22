* Online Appendix Figure A5: baseline (no-control) average marginal effects of
* marriage migration on spouse's tertiary education, by sex and Muslim status
* among non-white-British respondents:
*   logit stertiary_edu sadult_immig##tertiary_edu ///
*       if sex == `s' & white != 1 & muslim == `m'
*   margins sadult_immig#tertiary_edu
* Writes a combined 2-by-2 Figure A5 PNG.

args input_dta output_dir
if `"`input_dta'"' == "" local input_dta "Preparation\Reduced Form Sample\data_facts.dta"
if `"`output_dir'"' == "" local output_dir "Online Appendix\Output"
capture mkdir "`output_dir'"

use "`input_dta'", clear
capture confirm variable white
if _rc {
    gen byte white = ethnicityew == 1 if ethnicity != .
}

local panels_created = 0
forvalues sex_id = 1/2 {
    forvalues muslim_id = 0/1 {
        local religion_name "nonmuslim"
        local religion_label "Non-Muslim"
        if `muslim_id' == 1 local religion_name "muslim"
        if `muslim_id' == 1 local religion_label "Muslim"
        local sex_name "men"
        if `sex_id' == 2 local sex_name "women"

        capture quietly logit stertiary_edu sadult_immig##tertiary_edu ///
            if sex == `sex_id' & white != 1 & muslim == `muslim_id'
        if _rc {
            display as error "No estimable no-control logit for sex=`sex_id', muslim=`muslim_id'; panel skipped."
            continue
        }
        capture quietly margins sadult_immig#tertiary_edu
        if _rc {
            display as error "Margins unavailable for sex=`sex_id', muslim=`muslim_id'; panel skipped."
            continue
        }
        marginsplot, legend(position(12) rows(1)) ///
            ytitle("Spouse's Education") xtitle("Marriage Migration") title("") ///
            note("`religion_label' `sex_name'", position(6)) ///
            name(panel_`religion_name'_`sex_name', replace)
        local panels_created = `panels_created' + 1
    }
}

if `panels_created' != 4 {
    display as error "Figure A5 requires all four panels; combined figure was not created."
    exit 498
}

graph combine panel_muslim_men panel_muslim_women ///
    panel_nonmuslim_men panel_nonmuslim_women, ///
    cols(2) imargin(small) graphregion(color(white))
graph export "`output_dir'\Figure A5.png", replace width(2000)
display as result "Combined Figure A5 saved to: `output_dir'\Figure A5.png"
