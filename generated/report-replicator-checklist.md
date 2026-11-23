# Replicator Checklist

_Generated 2026-11-23T19:57:42.228 -- a deterministic summary of what the automated checks flagged. This doesn't replace reading the full reports in `generated/`; it's a starting point for where to look first._

## Crosscheck: claims vs. package (Stage D)

Coverage: 75.9% (56 claims checked).

Claims worth a closer look:

- **[Missing]** data_source `Scotland 2001 Census, religion/marriage tables (scotlandreligion2001)`: No file in code_manifest.txt or data_dependencies.md contains any reference to Scotland or a Scottish census; no plausible code file exists for this data source.
- **[Missing]** data_source `Self-authored Muslim marriage biographies collected from Instagram event-affiliated accounts, 2022-2024 (n=195, author-collected)`: No scraper, text-coding, or keyword-scheme script exists in the manifest. 'generate_artificial_survey_inputs.py' sits at the top level of 'Synthetic Data/', as a sibling to the per-source subfolders (Census, Understanding Society, Citizenship Survey, DHS India, IPUMS), suggesting it is a shared synthetic-data helper rather than a biography-coding script; no table or figure claim consumes a 'relocation score' variable either.
- **[Plausible]** table `tab:religionest`: The claim says this table corresponds to fig:prefrelig (by-religion estimates). 'Preparation/Model Engine/By Religion.do' is filename-plausible for re-estimating by religious group, but no Stage A trace confirms it produces this specific table; could also be bundled into one of the Results-folder figure scripts.
- **[Plausible]** table `tab:tradeoff_age`: Appendix A contains three otherwise-unassigned table scripts (Table A1, A2, A4.do); the age-gap trade-off table plausibly sits among these, but no direct trace ties a specific one to this claim.
- **[Plausible]** table `tab:nomig`: Appendix table numbering (A1–A17) is otherwise fully accounted for by other claims; this leaves one of the unassigned Appendix A table scripts (A1/A2/A4) as the likely home for the closed-market robustness table, though no direct trace confirms which.
- **[Plausible]** table `tab:noedu`: Folder 'Online Appendix/J Measurement Error and Robustness of Definition/J3 Measurement Error' (Code Table A9.do, Code Table A10.py, analysis.do, cleaning.do) matches the measurement-error/reclassification theme, but it is ambiguous which specific file produces this table versus tab:sensitivity.
- **[Plausible]** table `tab:sensitivity`: Same J3 Measurement Error folder plausibly houses the age-threshold sensitivity table alongside tab:noedu, but no direct trace distinguishes the two files.
- **[Plausible]** table `tab:estyear`: The 2001-vs-2011 comparison requires the 2001 CAMS cleaning pipeline; 'census_comparison_cleaning.py' and 'generate_synthetic_census_2001.py' are filename-plausible data prerequisites, and the L1 folder's two table scripts are candidates for the actual estimation, but no direct trace confirms the link.
- **[Plausible]** figure `fig:intermarriage`: 'Paper/2 Data & Reduced-Form Evidence/Code Figure 1.do' is the only figure script in the data section; it plausibly produces multiple panels including this one, but file-listing evidence cannot confirm which panel.
- **[Plausible]** figure `fig:marriage-migration`: Same single Figure 1.do script in the data section plausibly bundles this panel alongside fig:intermarriage; no direct trace distinguishes panels.

> **Note**: This list contains 93 entries (0.0 MB) — too large to embed in the report.
> The full list is available here: <https://www.dropbox.com/scl/fo/i50sc2awg2hkxdctpe3ty/AEEJKvb2qctxybLYLfVLl5U?rlkey=e63xgydj5omin76hx0p3vpy08&dl=0&preview=report-replicator-checklist.md>
