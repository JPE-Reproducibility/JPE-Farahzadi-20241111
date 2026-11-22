*==============================================================================
* run_all.do  -  Master script for the replication package
*
* Runs preparation and analysis scripts for "Migration for Marriage".
* Most results require restricted data;
* see README.md before interpreting the outputs.
*
* HOW TO USE
*   1. Set Stata's working directory to the package root.
*   2. Edit the SETTINGS block below (paths to your data and to Python).
*   3. Set the switches (run_*) to 1 for the parts you want to run.
*   4. Run:  do run_all.do
*
* Every sub-script can also be run on its own: the first comment lines of each
* file show its arguments. All sub-scripts expect the package root as the
* working directory.
*
* To test the pipeline without the restricted Census data, set
* use_synthetic = 1: the scripts then run on the files in "Synthetic Data".
* Synthetic results only prove that the code runs; they are not real results.
*==============================================================================

clear all
set more off

*------------------------------------------------------------------------------
* SETTINGS  (edit these)
*------------------------------------------------------------------------------
* Start Stata in the package root (the folder containing this file).
global root "`c(pwd)'"

* Python executable used by the Python steps
global python "python"

* 1 = run on the synthetic data in "Synthetic Data"; 0 = run on the real data
local use_synthetic = 1

* Example paths only: configure authorized inputs and existing writable parent
* directories before setting use_synthetic = 0. Keep restricted data secure.
global real_census2011_csv  "Data\census_ew_2011.csv"
global real_census2001_csv  "Data\census_ew_2001.csv"
global real_cleaned_dta     "Work\data.dta"
global real_model_dir       "Work\Model Estimation"
global real_nomig_dir       "Work\Model Estimation - Without Migration"
global real_sens_dir        "Work\Model Estimation - Sensitivity"
global real_a7_model_root   "Work\Table A7"
global real_a8_model_root   "Work\Table A8"
global real_cohab_dir       "Work\Table A11"
global real_ukborn_dta      "Work\data_ukborn.dta"
global real_ukborn_dir      "Work\Table A14"
global real_geo_dta         "Work\data_geography.dta"
global real_geo_dir         "Work\Table A15"
global real_ukhls_dta       "Data\indresp.dta"
global real_citizenship_dta "Data\citizenship_survey.dta"
global real_india_dta       "Data\IAPR42FL.dta"
global real_ipums_dta       "Data\ipumsi.dta"

* Which parts to run (1 = yes)
local run_synthetic   = 0   // regenerate the synthetic data
local run_cleaning    = 1   // clean the raw Census extract
local run_prepare     = 1   // build the reduced-form sample
local run_main_data   = 1   // Main Paper, Section 1 (Data): Figure 1, Tables 1-3
local run_main_result = 1   // Main Paper, Section 2 (Results): Table 4, Figures 4-8
local run_appendix    = 1   // Appendix tables and figures

*------------------------------------------------------------------------------
* Derived paths (do not edit)
*------------------------------------------------------------------------------
cd "$root"
local sd "Synthetic Data"
if `use_synthetic' {
    global census2011_csv "`sd'\Census\synthetic_census_ew_2011.csv"
    global census2001_csv "`sd'\Census\synthetic_census_ew_2001.csv"
    global cleaned_dta    "`sd'\Census\synthetic_cleaned.dta"
    global model_dir      "`sd'\model_out"
    global nomig_dir      "`sd'\model_out\Muslim - No Migration"
    global sens_dir       "`sd'\model_out"
    global a7_model_root  "`sd'\model_out\Table A7"
    global a8_model_root  "`sd'\model_out\Table A8"
    global cohab_dir      "`sd'\model_out\Table A11"
    global ukborn_dir     "`sd'\model_out\Table A14"
    global geo_dir        "`sd'\model_out\Table A15"
    global ukhls_dta      "$root\Synthetic Data\Understanding Society\indresp.dta"
    global citizenship_dta "`sd'\Citizenship Survey\citizenship survey synthetic.dta"
    global india_dta       "`sd'\DHS India\IAPR42FL synthetic.dta"
    global ipums_dta       "`sd'\IPUMS\ipumsi synthetic.dta"
}
else {
    global census2011_csv "${real_census2011_csv}"
    global census2001_csv "${real_census2001_csv}"
    global cleaned_dta    "${real_cleaned_dta}"
    global model_dir      "${real_model_dir}"
    global nomig_dir      "${real_nomig_dir}"
    global sens_dir       "${real_sens_dir}"
    global a7_model_root  "${real_a7_model_root}"
    global a8_model_root  "${real_a8_model_root}"
    global cohab_dir      "${real_cohab_dir}"
    global ukborn_dir     "${real_ukborn_dir}"
    global geo_dir        "${real_geo_dir}"
    global ukhls_dta      "${real_ukhls_dta}"
    global citizenship_dta "${real_citizenship_dta}"
    global india_dta       "${real_india_dta}"
    global ipums_dta       "${real_ipums_dta}"
}
* Reduced-form sample produced by the preparation step
global rf_dta "Preparation\Reduced Form Sample\data_facts.dta"

* Output folders (created if missing)
global out_data "Paper\Output"
global out_res  "Paper\Output"
global out_app  "Online Appendix\Output"
global baseline_table_dir "$model_dir"
foreach d in "$out_data" "$out_res" "$out_app" {
    capture mkdir "`d'"
}

*==============================================================================
* 0. SYNTHETIC DATA (optional)  -  folder "Synthetic Data"
*==============================================================================
if `run_synthetic' {
    shell "$python" "`sd'\Census\generate_synthetic_census.py"
    shell "$python" "`sd'\Census\generate_synthetic_census_2001.py"
    shell "$python" "`sd'\Understanding Society\generate_synthetic_understanding_society.py"
    shell "$python" "`sd'\generate_artificial_survey_inputs.py"
    do "`sd'\Citizenship Survey\Code Create Synthetic Citizenship Survey.do"
}

*==============================================================================
* 1. PREPARATION  -  folder "Preparation"
*==============================================================================
* 1a. Data cleaning: raw Census extract -> analysis file (Python)
*     Also runs on the synthetic files when use_synthetic = 1. Table A11
*     creates its cohabitation variants from the raw CSV in its own workflow.
if `run_cleaning' {
    shell "$python" "Preparation\Data Cleaning\census_cleaning.py" ///
        --input-csv "$census2011_csv" --output-dta "$cleaned_dta"
}

* 1b. Reduced-form sample used by the descriptive figures and tables
if `run_prepare' {
    do "Preparation\Reduced Form Sample\Code Prepare Reduced Form Data.do" ///
        "$cleaned_dta" "$rf_dta"
}

* 1c. The structural model itself is estimated by
*     "Preparation\Model Engine\By Religion.do" and "Paper\5 Results\Code Table 4.do"
*     (the matching-equilibrium solver is matching_equilibrium.py).
*     Estimation is slow; the model_dir folders above hold its output.

*==============================================================================
* 2. MAIN PAPER: DATA AND REDUCED-FORM EVIDENCE
*==============================================================================
if `run_main_data' {
    do "Paper\2 Data & Reduced-Form Evidence\Code Figure 1.do" "$rf_dta" "$out_data"
    do "Paper\2 Data & Reduced-Form Evidence\Code Table 1.do" "$rf_dta" "$out_data"
    do "Paper\2 Data & Reduced-Form Evidence\Code Table 2.do" "$rf_dta" "$out_data"
    do "Paper\2 Data & Reduced-Form Evidence\Code Table 3.do" "$rf_dta" "$out_data"
}

*==============================================================================
* 3. MAIN PAPER: RESULTS AND POLICY ANALYSIS
*==============================================================================
if `run_main_result' {
    * Table 4: estimated model (Muslim, religion code 6 by default)
    do "Paper\5 Results\Code Table 4.do" "$cleaned_dta" "$model_dir" "$out_res"

    * Figures 5 and 6 (religion-specific estimates; runs By Religion.do)
    do "Paper\5 Results\Code Figure 5.do" "$cleaned_dta" "$model_dir"

    * Figures 4, 6, 7, 8 are drawn from the model output in Python
    shell "$python" "Paper\5 Results\Code Figure 4.py" --input-dir "$model_dir"
    shell "$python" "Paper\5 Results\Code Figure 6.py" --model-root "$model_dir"
    shell "$python" "Paper\6 Policy Analysis\Code Figure 7.py" --input-dir "$model_dir"
    shell "$python" "Paper\6 Policy Analysis\Code Figure 8.py" --input-dir "$model_dir"
}

*==============================================================================
* 4. ONLINE APPENDIX  -  folder "Online Appendix"
*==============================================================================
if `run_appendix' {

    *--- Figures (descriptive; need the reduced-form sample) ------------------
    foreach n in A3 A5 A6 A7 {
        do "Online Appendix\A Appendix Figures & Tables\Code Figure `n'.do" "$rf_dta" "$out_app"
    }
    do "Online Appendix\L Heterogeneity\L3 Heterogeneity by Local Market Population\Code Figure A16.do" "$rf_dta" "$out_app"
    * Figure A14 uses the cleaned person/spouse data (not the reduced-form sample)
    do "Online Appendix\L Heterogeneity\L2 Heterogeneity by Nativity Status\Code Figure A14.do" "$cleaned_dta" "$out_app"
    * Figure A1 uses the raw 2011 Census person file (cohabitation shares)
    do "Online Appendix\A Appendix Figures & Tables\Code Figure A1.do" "$census2011_csv" "$out_app"
    * Figure A2 uses real or synthetic Citizenship Survey data according to use_synthetic
    do "Online Appendix\A Appendix Figures & Tables\Code Figure A2.do" "$citizenship_dta" "$out_app"
    * Figure A4 compares UK, India (DHS) and IPUMS data
    do "Online Appendix\A Appendix Figures & Tables\Code Figure A4.do" ///
        "$rf_dta" "$india_dta" "$ipums_dta" "$out_app"
    * Toy-model and Monte Carlo figures use fixed seeds or deterministic inputs.
    shell "$python" "Online Appendix\F Toy Model\Code Figures A9-A12.py" ///
        --output-dir "$out_app"
    shell "$python" "Online Appendix\H Monte-Carlo Simulations\Code Figure A13.py" ///
        --output-dir "$out_app"
    * Figures A18-A19: two-generation matching sensitivity analyses
    shell "$python" "Online Appendix\M Model Extensions\M2 Two-Generation Matching\Code Figure A18.py" ///
        --output-dir "$out_app"
    shell "$python" "Online Appendix\M Model Extensions\M2 Two-Generation Matching\Code Figure A19.py" ///
        --output-dir "$out_app"
    * Figure A20: two-generation outcomes with endogenous preferences
    shell "$python" "Online Appendix\M Model Extensions\M3 Two-Generation Matching with Endogeneous Preferences\Code Figure A20.py" ///
        --output-dir "$out_app"

    *--- Reduced-form tables --------------------------------------------------
    do "Online Appendix\A Appendix Figures & Tables\Code Table A1.do" "$rf_dta" "$out_app"
    do "Online Appendix\A Appendix Figures & Tables\Code Table A2.do" "$rf_dta" "$out_app"

    *--- Model-based tables ---------------------------------------------------
    shell "$python" "Online Appendix\A Appendix Figures & Tables\Code Table A3.py" --input-dir "$model_dir"
    do "Online Appendix\A Appendix Figures & Tables\Code Table A4.do" "$cleaned_dta" "$model_dir"
    * A5 combines person-level observed moments with the baseline model.
    do "Online Appendix\I Model Fit\Table A5 observed.do" "$cleaned_dta" "$out_app"
    shell "$python" "Online Appendix\I Model Fit\Code Table A5.py" ///
        --model-dir "$model_dir" --observed-dir "$out_app" --output "$out_app\Table A5.csv"
    do "Online Appendix\I Model Fit\Code Table A6.do" ///
        "$cleaned_dta" "$model_dir" "$nomig_dir" "$out_app"
    * A7 reuses the cleaned Census data and baseline model. The Table 4
    * estimator changes only sadult_immig for the sensitivity specification.
    do "Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration\Code Table A7.do" ///
        "$cleaned_dta" "$model_dir" "$baseline_table_dir" ///
        "$a7_model_root" "$out_app" "$python"
    * A8 reuses the age-18 baseline, estimates age-16/20 models, and assembles
    * the table.
    do "Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration\Code Table A8.do" ///
        "$census2011_csv" "$model_dir" "$baseline_table_dir" ///
        "$a8_model_root" "$out_app" "$python"
    * A9: Understanding Society (own cleaning and analysis files)
    do "Online Appendix\J Measurement Error and Robustness of Definition\J3 Measurement Error\Code Table A9.do" ///
        "$ukhls_dta" "$root\Online Appendix\Output\A9_work" "$out_app"
    shell "$python" "Online Appendix\J Measurement Error and Robustness of Definition\J3 Measurement Error\Code Table A10.py" --output "$out_app\Table A10.csv"

    *--- Robustness tables ----------------------------------------------------
    * A11 builds both cohabitation variants from the raw Census CSV.
    do "Online Appendix\K Robustness to Cohabitation\Code Table A11.do" ///
        "$census2011_csv" "$cohab_dir" "$out_app" "$python"
    * A12 uses the existing baseline model-count files.
    do "Online Appendix\L Heterogeneity\L1 Heterogeneity by Cohort and Period\Code Table A12.do" "$model_dir" "$out_app"
    * A13: comparison with the 2001 Census
    do "Online Appendix\L Heterogeneity\L1 Heterogeneity by Cohort and Period\Code Table A13.do" ///
        "$census2001_csv" "$census2011_csv" "Online Appendix\Output\A13_work" "$out_app" "$python"
    * A14: UK-born sample
    do "Online Appendix\L Heterogeneity\L2 Heterogeneity by Nativity Status\Code Table A14.do" ///
        "$cleaned_dta" "$model_dir" "$ukborn_dir" "$out_app" "$python"
    * A15: geography (regions 4-8)
    do "Online Appendix\L Heterogeneity\L3 Heterogeneity by Local Market Population\Code Table A15.do" ///
        "$cleaned_dta" "$model_dir" "$geo_dir" "$out_app" "$python"
    * A16: baseline and nested-model parameter estimates
    shell "$python" "Online Appendix\M Model Extensions\M1 Nested Matching\Code Table A16.py" ///
        --output-dir "$out_app"
    * A17: observed and counterfactual intermarriage/migration rates
    shell "$python" "Online Appendix\M Model Extensions\M1 Nested Matching\Code Table A17.py" ///
        --output-dir "$out_app"
    * Figure A17: high (la_muslim_share > 0.1) vs low (< 0.1) Muslim population
    do "Online Appendix\L Heterogeneity\L3 Heterogeneity by Local Market Population\Code Figure A17.do" ///
        "$cleaned_dta" "$model_dir\Figure A17" "$out_app" "$python"
}

display as result _n "run_all.do finished."
