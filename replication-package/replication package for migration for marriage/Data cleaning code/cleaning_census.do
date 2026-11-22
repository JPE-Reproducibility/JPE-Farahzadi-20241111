* Supply the intermediate CSV and destination DTA as arguments.
args input_csv output_dta
if `"`input_csv'"' == "" | `"`output_dta'"' == "" {
    display as error "Pass the intermediate Census CSV and output DTA paths."
    exit 198
}
import delimited using `"`input_csv'"', clear

local vars = "immigrant immigrant18 single married tertiary_education employed unemployed"

foreach x of varlist `vars'{ 
	replace `x' = "1" if `x' == "True"
	replace `x' = "0" if `x' == "False"
	destring `x', replace
}

gen muslim = religion == 6
replace muslim = . if religion == . | religion == 9

gen N = 1
bys la: egen la_total = total(N)
bys la: egen la_muslim_total = total(muslim)
gen la_muslim_share = la_muslim_total/la_total

drop N la_muslim_total la_total muslim

gen ukborn = 1 - immigrant
keep if immigrant18 == 0 | ukborn == 1

local vars = "age sage sex lang_prof slang_prof ethnicity sethnicity religion sreligion edu_level sedu_level tertiary_education stertiary_education health"

foreach x of varlist `vars'{ 
	replace `x' = . if `x' < 0
}

save `"`output_dta'"', replace