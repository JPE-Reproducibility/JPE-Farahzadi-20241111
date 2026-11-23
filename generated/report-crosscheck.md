### Paper vs. Code/Data Crosscheck

_Generated on 2026-11-23T17:32:16.948_

**Caveats (read before using this report):**
- **Static plausibility only, not a reproducibility check.** No code was executed.
  This cannot catch logic bugs, wrong coefficients, or silently incorrect results.
- **File-level citations only, not line-level.** The model did not see code file
  contents -- only Stage A/B's pre-computed findings and file listings. Any
  "supporting file" below is a plausibility signal, not a verified line reference.
- **Coverage is relative to what Stage C extracted from the paper**, not to the
  paper's true full content. A claim Stage C missed is invisible to this score.

#### Coverage

| Category | Coverage | n claims |
|----------|----------|----------|
| figure | 71.4% | 28 |
| table | 85.7% | 21 |
| data_source | 64.3% | 7 |
| **Overall** | **75.9%** | 56 |

#### Per-Claim Detail

✅ **table: tab:summary** — Matched
- Folder 'Paper/2 Data & Reduced-Form Evidence' contains 'Code Table 1.do', the first table in that section, matching the claim's title 'Summary Statistics' which is the natural first table of a Census-based paper.
- supporting files: `Paper/2 Data & Reduced-Form Evidence/Code Table 1.do`

✅ **table: tab:sorting** — Matched
- Same folder contains 'Code Table 2.do', consistent with the second table of the Data section covering the sorting/education regression.
- supporting files: `Paper/2 Data & Reduced-Form Evidence/Code Table 2.do`

✅ **table: tab:tradeoff** — Matched
- 'Code Table 3.do' is the third table in the same section, consistent with the spouse-education trade-off table following the sorting table.
- supporting files: `Paper/2 Data & Reduced-Form Evidence/Code Table 3.do`

✅ **table: tab:preferences** — Matched
- 'Paper/5 Results/Code Table 4.do' is the only numbered table in the Results section, matching the structural minimum-distance preference estimates.
- supporting files: `Paper/5 Results/Code Table 4.do`

🟡 **table: tab:religionest** — Plausible
- The claim says this table corresponds to fig:prefrelig (by-religion estimates). 'Preparation/Model Engine/By Religion.do' is filename-plausible for re-estimating by religious group, but no Stage A trace confirms it produces this specific table; could also be bundled into one of the Results-folder figure scripts.
- supporting files: `Preparation/Model Engine/By Religion.do`

✅ **table: tab:sorting_logit** — Matched
- 'Online Appendix/A Appendix Figures & Tables/Code Table A3.py' is the only Appendix-A table script of Python type, consistent with the logit robustness table (tab:sorting_logit) being computed differently from the surrounding .do table/figure scripts.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Table A3.py`

🟡 **table: tab:tradeoff_age** — Plausible
- Appendix A contains three otherwise-unassigned table scripts (Table A1, A2, A4.do); the age-gap trade-off table plausibly sits among these, but no direct trace ties a specific one to this claim.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Table A1.do`, `Online Appendix/A Appendix Figures & Tables/Code Table A2.do`, `Online Appendix/A Appendix Figures & Tables/Code Table A4.do`

✅ **table: tab:counterfactuals** — Matched
- Folder 'Paper/6 Policy Analysis' (Figure 7.py, Figure 8.py) and 'Preparation/Model Engine/counterfactual.py' directly match the policy counterfactual tax/population scenarios described.
- supporting files: `Paper/6 Policy Analysis/Code Figure 7.py`, `Paper/6 Policy Analysis/Code Figure 8.py`, `Preparation/Model Engine/counterfactual.py`

✅ **table: tab:simmatching** — Matched
- Folder 'Online Appendix/I Model Fit' (Code Table A6.do, Table A5 observed.do, Code Table A5.py) matches the claim's title 'Model Fit: Predicted vs. Observed Matching Patterns' directly.
- supporting files: `Online Appendix/I Model Fit/Code Table A6.do`, `Online Appendix/I Model Fit/Table A5 observed.do`, `Online Appendix/I Model Fit/Code Table A5.py`

🟡 **table: tab:nomig** — Plausible
- Appendix table numbering (A1–A17) is otherwise fully accounted for by other claims; this leaves one of the unassigned Appendix A table scripts (A1/A2/A4) as the likely home for the closed-market robustness table, though no direct trace confirms which.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Table A1.do`, `Online Appendix/A Appendix Figures & Tables/Code Table A2.do`, `Online Appendix/A Appendix Figures & Tables/Code Table A4.do`

🟡 **table: tab:noedu** — Plausible
- Folder 'Online Appendix/J Measurement Error and Robustness of Definition/J3 Measurement Error' (Code Table A9.do, Code Table A10.py, analysis.do, cleaning.do) matches the measurement-error/reclassification theme, but it is ambiguous which specific file produces this table versus tab:sensitivity.
- supporting files: `Online Appendix/J Measurement Error and Robustness of Definition/J3 Measurement Error/Code Table A9.do`, `Online Appendix/J Measurement Error and Robustness of Definition/J3 Measurement Error/Code Table A10.py`, `Online Appendix/J Measurement Error and Robustness of Definition/J3 Measurement Error/analysis.do`, `Online Appendix/J Measurement Error and Robustness of Definition/J3 Measurement Error/cleaning.do`

🟡 **table: tab:sensitivity** — Plausible
- Same J3 Measurement Error folder plausibly houses the age-threshold sensitivity table alongside tab:noedu, but no direct trace distinguishes the two files.
- supporting files: `Online Appendix/J Measurement Error and Robustness of Definition/J3 Measurement Error/Code Table A9.do`, `Online Appendix/J Measurement Error and Robustness of Definition/J3 Measurement Error/Code Table A10.py`

✅ **table: tab:mm_lowerbound_rates** — Matched
- Folder name 'J2 Alternative Definitions of Marriage Migration' directly matches the baseline-vs-lower-bound rate comparison, with both a .do and .py script present.
- supporting files: `Online Appendix/J Measurement Error and Robustness of Definition/J2 Alternative Definitions of Marriage Migration/Code Table A7.do`, `Online Appendix/J Measurement Error and Robustness of Definition/J2 Alternative Definitions of Marriage Migration/table_a7_migration.py`

✅ **table: tab:lowerbound** — Matched
- Same J2 folder's second table script (A8) directly matches the baseline/lower-bound outside-market-value estimates, paired with tab:mm_lowerbound_rates's A7.
- supporting files: `Online Appendix/J Measurement Error and Robustness of Definition/J2 Alternative Definitions of Marriage Migration/Code Table A8.do`, `Online Appendix/J Measurement Error and Robustness of Definition/J2 Alternative Definitions of Marriage Migration/table_a8_migration.py`

✅ **table: tab:nocohab** — Matched
- Folder name 'K Robustness to Cohabitation' directly matches the claim title and content, with both .do and .py implementations present.
- supporting files: `Online Appendix/K Robustness to Cohabitation/Code Table A11.do`, `Online Appendix/K Robustness to Cohabitation/table_a11_migration.py`

✅ **table: tab:estcohort** — Matched
- Folder 'L1 Heterogeneity by Cohort and Period' directly matches the age-cohort heterogeneity claim.
- supporting files: `Online Appendix/L Heterogeneity/L1 Heterogeneity by Cohort and Period/Code Table A12.do`, `Online Appendix/L Heterogeneity/L1 Heterogeneity by Cohort and Period/Code Table A13.do`

🟡 **table: tab:estyear** — Plausible
- The 2001-vs-2011 comparison requires the 2001 CAMS cleaning pipeline; 'census_comparison_cleaning.py' and 'generate_synthetic_census_2001.py' are filename-plausible data prerequisites, and the L1 folder's two table scripts are candidates for the actual estimation, but no direct trace confirms the link.
- supporting files: `Preparation/Data Cleaning/census_comparison_cleaning.py`, `Synthetic Data/Census/generate_synthetic_census_2001.py`, `Online Appendix/L Heterogeneity/L1 Heterogeneity by Cohort and Period/Code Table A12.do`, `Online Appendix/L Heterogeneity/L1 Heterogeneity by Cohort and Period/Code Table A13.do`

✅ **table: tab:firstgen** — Matched
- Folder name 'L2 Heterogeneity by Nativity Status' directly matches the UK-born vs UK-raised robustness claim.
- supporting files: `Online Appendix/L Heterogeneity/L2 Heterogeneity by Nativity Status/Code Table A14.do`

✅ **table: tab:geolim** — Matched
- Folder name 'L3 Heterogeneity by Local Market Population' directly matches the geographic restriction claim.
- supporting files: `Online Appendix/L Heterogeneity/L3 Heterogeneity by Local Market Population/Code Table A15.do`

✅ **table: tab:nestedparam** — Matched
- Folder name 'M1 Nested Matching' and file 'Code Table A16.py' directly match the nested-logit parameter estimates, with estimation_nested.py as a supporting module.
- supporting files: `Online Appendix/M Model Extensions/M1 Nested Matching/Code Table A16.py`, `Online Appendix/M Model Extensions/M1 Nested Matching/estimation_nested.py`

✅ **table: tab:nestedcounter** — Matched
- Same M1 folder's 'Code Table A17.py' plus counterfactual_baseline.py/counterfactual_nested.py directly match the nested-logit counterfactual claim.
- supporting files: `Online Appendix/M Model Extensions/M1 Nested Matching/Code Table A17.py`, `Online Appendix/M Model Extensions/M1 Nested Matching/counterfactual_baseline.py`, `Online Appendix/M Model Extensions/M1 Nested Matching/counterfactual_nested.py`

🟡 **figure: fig:intermarriage** — Plausible
- 'Paper/2 Data & Reduced-Form Evidence/Code Figure 1.do' is the only figure script in the data section; it plausibly produces multiple panels including this one, but file-listing evidence cannot confirm which panel.
- supporting files: `Paper/2 Data & Reduced-Form Evidence/Code Figure 1.do`

🟡 **figure: fig:marriage-migration** — Plausible
- Same single Figure 1.do script in the data section plausibly bundles this panel alongside fig:intermarriage; no direct trace distinguishes panels.
- supporting files: `Paper/2 Data & Reduced-Form Evidence/Code Figure 1.do`

🟡 **figure: fig:edu_origin_combined** — Plausible
- One of the seven Appendix A figure scripts (A1-A7) is plausibly this figure comparing migrant vs. origin-country education, but no file is explicitly named for it.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Figure A1.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A2.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A3.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A4.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A5.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A6.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A7.do`

🟡 **figure: fig:logit_nocontrol_2x2** — Plausible
- Likely produced alongside tab:sorting_logit's Table A3.py or bundled in one of the Appendix A figure scripts, but no file is explicitly named for this 2x2 logit figure.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Table A3.py`

🟡 **figure: fig:logit_control_2x2** — Plausible
- Same reasoning as fig:logit_nocontrol_2x2; plausibly generated by the same logit-related script, no direct trace available.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Table A3.py`

🟡 **figure: fig:determinants** — Plausible
- 'Paper/5 Results' folder contains three figure scripts (Figure 4.py, Figure 5.do, Figure 6.py) for four figure claims in this section; one of them plausibly produces this decomposition figure, but file listing alone cannot identify which.
- supporting files: `Paper/5 Results/Code Figure 4.py`, `Paper/5 Results/Code Figure 5.do`, `Paper/5 Results/Code Figure 6.py`

🟡 **figure: fig:prefrelig** — Plausible
- Plausibly tied to 'By Religion.do' (filename matches 'by religion' estimation) and/or one of the Results-section figure scripts; no direct trace confirms either.
- supporting files: `Preparation/Model Engine/By Religion.do`, `Paper/5 Results/Code Figure 4.py`, `Paper/5 Results/Code Figure 5.do`, `Paper/5 Results/Code Figure 6.py`

🟡 **figure: fig:gainsrelig** — Plausible
- Plausibly one of the three Results-section figure scripts, alongside fig:determinants/fig:prefrelig/fig:mmbyage; cannot distinguish which from file listing alone.
- supporting files: `Paper/5 Results/Code Figure 4.py`, `Paper/5 Results/Code Figure 5.do`, `Paper/5 Results/Code Figure 6.py`

🟡 **figure: fig:mmbyage** — Plausible
- Same Results-section figure-script ambiguity as the other three figures in this section.
- supporting files: `Paper/5 Results/Code Figure 4.py`, `Paper/5 Results/Code Figure 5.do`, `Paper/5 Results/Code Figure 6.py`

✅ **figure: fig:migtax** — Matched
- Folder 'Paper/6 Policy Analysis' with Figure 7.py/Figure 8.py directly matches the migration-tax policy counterfactual figures.
- supporting files: `Paper/6 Policy Analysis/Code Figure 7.py`, `Paper/6 Policy Analysis/Code Figure 8.py`

✅ **figure: fig:changes** — Matched
- Same Policy Analysis folder directly matches the population-share counterfactual figure, paired with fig:migtax.
- supporting files: `Paper/6 Policy Analysis/Code Figure 7.py`, `Paper/6 Policy Analysis/Code Figure 8.py`

🟡 **figure: fig:cohabiting** — Plausible
- Plausibly one of the unassigned Appendix A figure scripts (A1-A7), motivating the cohabitation robustness check in folder K; no direct trace available.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Figure A1.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A7.do`, `Online Appendix/K Robustness to Cohabitation/Code Table A11.do`

🟡 **figure: fig:practice** — Plausible
- Depends on Citizenship Survey data (Synthetic Data/Citizenship Survey folder) and plausibly one of the Appendix A figure scripts, but no figure-generating file is explicitly named for this claim.
- supporting files: `Synthetic Data/Citizenship Survey/Code Create Synthetic Citizenship Survey.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A1.do`

🟡 **figure: fig:interreligmarriage** — Plausible
- Plausibly one of the unassigned Appendix A figure scripts; described as 'additional appendix data' consistent with that folder, no direct trace.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Figure A1.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A7.do`

🟡 **figure: fig:migrantsorting_southasia** — Plausible
- Plausibly one of the Appendix A figure scripts covering South Asian migrant education sorting; no file is explicitly named for this comparison.
- supporting files: `Online Appendix/A Appendix Figures & Tables/Code Figure A2.do`, `Online Appendix/A Appendix Figures & Tables/Code Figure A3.do`

✅ **figure: fig:montecarlo** — Matched
- Folder 'H Monte-Carlo Simulations' with 'Code Figure A13.py' directly matches the claim.
- supporting files: `Online Appendix/H Monte-Carlo Simulations/Code Figure A13.py`

✅ **figure: fig:migrationgain** — Matched
- Folder 'F Toy Model' file 'Code Figures A9-A12.py' is named to cover exactly four toy-model figures (A9-A12), matching this and three sibling figure claims.
- supporting files: `Online Appendix/F Toy Model/Code Figures A9-A12.py`

✅ **figure: fig:similaritygain** — Matched
- Same 'Code Figures A9-A12.py' script, bundling this toy-model figure with the three siblings.
- supporting files: `Online Appendix/F Toy Model/Code Figures A9-A12.py`

✅ **figure: fig:pricegapend** — Matched
- Same 'Code Figures A9-A12.py' script.
- supporting files: `Online Appendix/F Toy Model/Code Figures A9-A12.py`

✅ **figure: fig:pricegapmig** — Matched
- Same 'Code Figures A9-A12.py' script, completing the four toy-model figures A9-A12.
- supporting files: `Online Appendix/F Toy Model/Code Figures A9-A12.py`

✅ **figure: fig:phi_sensitivity** — Matched
- Folder 'M2 Two-Generation Matching' with 'Code Figure A18.py'; data_dependencies.md confirms this file directly reads params.json, the two-generation model's parameter file.
- supporting files: `Online Appendix/M Model Extensions/M2 Two-Generation Matching/Code Figure A18.py`, `Online Appendix/M Model Extensions/M2 Two-Generation Matching/params.json`

✅ **figure: fig:B_sensitivity** — Matched
- Same M2 folder's 'Code Figure A19.py' and 'two_generation_model.py' match the outside-market-value sensitivity figure.
- supporting files: `Online Appendix/M Model Extensions/M2 Two-Generation Matching/Code Figure A19.py`, `Online Appendix/M Model Extensions/M2 Two-Generation Matching/two_generation_model.py`

✅ **figure: fig:phi_endogeneity** — Matched
- Folder 'M3 Two-Generation Matching with Endogenous Preferences' and file 'Code Figure A20.py' directly match this claim's title and content.
- supporting files: `Online Appendix/M Model Extensions/M3 Two-Generation Matching with Endogeneous Preferences/Code Figure A20.py`

✅ **figure: fig:robust_immigrant** — Matched
- Folder 'L2 Heterogeneity by Nativity Status' with 'Code Figure A14.do' directly matches the nativity-status robustness figure.
- supporting files: `Online Appendix/L Heterogeneity/L2 Heterogeneity by Nativity Status/Code Figure A14.do`

🟡 **figure: fig:muslimbyregion** — Plausible
- Folder 'L3 Heterogeneity by Local Market Population' contains two figure scripts (A16, A17) for three regional figure claims in this section; plausible but not individually traceable.
- supporting files: `Online Appendix/L Heterogeneity/L3 Heterogeneity by Local Market Population/Code Figure A16.do`, `Online Appendix/L Heterogeneity/L3 Heterogeneity by Local Market Population/Code Figure A17.do`

🟡 **figure: fig:mmbyregion** — Plausible
- Same L3 folder figure scripts plausibly cover this regional marriage-migration figure, ambiguous which specific file.
- supporting files: `Online Appendix/L Heterogeneity/L3 Heterogeneity by Local Market Population/Code Figure A16.do`, `Online Appendix/L Heterogeneity/L3 Heterogeneity by Local Market Population/figure_a17_migration.py`

🟡 **figure: fig:determinantsdensity** — Plausible
- Same L3 folder plausibly covers the low- vs high-density decomposition figure, ambiguous which specific file.
- supporting files: `Online Appendix/L Heterogeneity/L3 Heterogeneity by Local Market Population/Code Figure A17.do`, `Online Appendix/L Heterogeneity/L3 Heterogeneity by Local Market Population/figure_a17_migration.py`

✅ **figure: fig:mmage** — Matched
- Folder 'L2 Heterogeneity by Nativity Status' directly matches this UK-born vs UK-raised age-group figure, paired with fig:robust_immigrant via the same folder's Figure A14.do.
- supporting files: `Online Appendix/L Heterogeneity/L2 Heterogeneity by Nativity Status/Code Figure A14.do`

✅ **data_source: 2011 Census for England and Wales (10% sample)** — Matched
- Multiple code files are explicitly named for Census cleaning: 'cleaning_census.do', 'census_cleaning.py' (appearing in two folders), and 'generate_synthetic_census.py'. Note the duplicate census_cleaning.py in both 'Data cleaning code/' and 'Preparation/Data Cleaning/' is worth a human follow-up to confirm which is authoritative.
- supporting files: `Data cleaning code/cleaning_census.do`, `Data cleaning code/census_cleaning.py`, `Preparation/Data Cleaning/census_cleaning.py`, `Synthetic Data/Census/generate_synthetic_census.py`

✅ **data_source: Census 2001 Controlled Access Microdata Sample (CAMS) for England and Wales (ons2001cams)** — Matched
- Code files explicitly named for the 2001 comparison: 'census_comparison_cleaning.py' and 'generate_synthetic_census_2001.py'.
- supporting files: `Preparation/Data Cleaning/census_comparison_cleaning.py`, `Synthetic Data/Census/generate_synthetic_census_2001.py`

✅ **data_source: Understanding Society (UKHLS), Wave 1 (ukhls6614)** — Matched
- Dedicated folder 'Synthetic Data/Understanding Society/' with cleaning.do, analysis.do, and generate_synthetic_understanding_society.py directly matches this data source; note analysis.do/cleaning.do names are duplicated in the J3 Measurement Error folder, worth a human check on whether these are the same pipeline reused or distinct code.
- supporting files: `Synthetic Data/Understanding Society/cleaning.do`, `Synthetic Data/Understanding Society/analysis.do`, `Synthetic Data/Understanding Society/generate_synthetic_understanding_society.py`

✅ **data_source: Citizenship Survey 2010-11 (citizenshipsurvey2011)** — Matched
- Dedicated folder and file 'Synthetic Data/Citizenship Survey/Code Create Synthetic Citizenship Survey.do' directly matches this data source.
- supporting files: `Synthetic Data/Citizenship Survey/Code Create Synthetic Citizenship Survey.do`

❌ **data_source: Scotland 2001 Census, religion/marriage tables (scotlandreligion2001)** — Missing
- No file in code_manifest.txt or data_dependencies.md contains any reference to Scotland or a Scottish census; no plausible code file exists for this data source.

❌ **data_source: Self-authored Muslim marriage biographies collected from Instagram event-affiliated accounts, 2022-2024 (n=195, author-collected)** — Missing
- No scraper, text-coding, or keyword-scheme script exists in the manifest. 'generate_artificial_survey_inputs.py' sits at the top level of 'Synthetic Data/', as a sibling to the per-source subfolders (Census, Understanding Society, Citizenship Survey, DHS India, IPUMS), suggesting it is a shared synthetic-data helper rather than a biography-coding script; no table or figure claim consumes a 'relocation score' variable either.

🟡 **data_source: Country-level educational attainment distributions by gender for India, Pakistan, and Bangladesh (source unspecified in text), underlying Figure A (fig:edu_origin_combined)** — Plausible
- The paper itself leaves this source unspecified. 'Synthetic Data/DHS India/Code Create Synthetic DHS India.do' and 'Synthetic Data/IPUMS/Code Create Synthetic IPUMS.do' are the only candidate files touching cross-country survey/census data, but neither is explicitly named for this claim, so the connection is weak and flagged for human review rather than treated as a confirmed match.
- supporting files: `Synthetic Data/DHS India/Code Create Synthetic DHS India.do`, `Synthetic Data/IPUMS/Code Create Synthetic IPUMS.do`

#### Orphan Code (no traceable connection to any claim)

- `Online Appendix/M Model Extensions/M2 Two-Generation Matching (Synthetic Data) Synthetic Data/IPUMS/Code Create Synthetic IPUMS.do`
- `Synthetic Data/DHS India/Code Create Synthetic DHS India.do`
- `Synthetic Data/generate_artificial_survey_inputs.py`
