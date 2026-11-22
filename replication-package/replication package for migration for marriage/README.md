# Migration for Marriage: Data and Code

This package contains analysis code and artificial data for *Migration for
Marriage*. The empirical analyses require access to restricted or licensed datasets
that are **not included**. The artificial inputs allow selected code paths
to be tested, but do not reproduce the paper's estimates. The author reports
that the analyses have been checked on the secure server.

## Data access

The links below describe currently published access routes, not the
author's access history. Requirements, costs and timelines can change, so
check each provider's current record before applying. 

| Dataset | Analysis | Access |
|---|---|---|
| 2011 England and Wales Census household microdata | Main analysis and most appendix results | The cited source is the 10% household secure sample, [ONS SRS record, DOI 10.57906/f56d-r183](https://doi.org/10.57906/f56d-r183). Access is through the [ONS Secure Research Service (SRS)](https://www.ons.gov.uk/aboutus/whatwedo/statistics/requestingstatistics/secureresearchservice): researchers need accreditation and an approved project through PASS; office or home access also requires the organisation's Assured Organisational Connectivity agreement and dataset approval. Current ONS guidance says project applications can take about 10 weeks; its July 2026 figures report a median 26 working days for project approval and a further median 12 working days from approval to data availability. These are indicative, not guarantees. |
| 2001 Census Controlled Access Microdata Sample (CAMS) | Appendix Table A13 and 2001 comparison | The candidate source is [ONS SRS record, DOI 10.57906/019z-3w22](https://doi.org/10.57906/019z-3w22), released 5 August 2005. SRS accreditation and project approval apply. |
| Understanding Society, wave 1 | Appendix Table A9; two-generation model inputs | [UK Data Service Study 6614](https://doc.ukdataservice.ac.uk/doc/6614/read6614.htm). Secure access can be obtained from UK Data Service or Office of National Statistics.
| Citizenship Survey 2010–11 | Appendix Figure A2 | [UK Data Service Study 7111](https://doc.ukdataservice.ac.uk/doc/7111/read7111.htm). Register with the UK Data Service and accept the study's End User Licence; check the study record for any additional conditions. |
| India NFHS-2 1998–99, India Members Recode | Appendix Figure A4 | [IIPS NFHS-2 catalogue record](https://www.iipsdata.ac.in/datacatalog_detail/1/33/dataset) lists the All-India files as free. A data request/authorization is required through the [NFHS data request portal](https://www.nfhsiips.in/nfhsuser/datarequest.php). |
| Pakistan 1998 and Bangladesh 2001 population censuses, IPUMS samples `586199801` and `50200101` | Appendix Figure A4 | Request extracts from [IPUMS International](https://international.ipums.org/) under its [terms of use](https://international.ipums.org/international/terms.shtml). Each team member must register and be individually licensed; extracts are for scholarly/educational use, cannot be used commercially or redistributed, and require citation of the relevant statistical agencies.  |

## Data citations

The following dataset and source-report citations are included in
`Paper text\References.bib`. 

- Office for National Statistics. 2005. *Census 2001 Household - UK* [dataset].
  ONS SRS Metadata Catalogue. https://doi.org/10.57906/019z-3w22. The
  original code refers to `ukhhdcam050805.dta`; confirm the exact CAMS file
  and citation from the acquisition record.
- Office for National Statistics. 2016. *Census 2011 Household - England and
  Wales* [dataset], 10% secure household sample. ONS SRS Metadata Catalogue,
  released 12 July 2016. https://doi.org/10.57906/f56d-r183.
- University of Essex, Institute for Social and Economic Research. 2024.
  *Understanding Society: Waves 1-14, 2009-2023 and Harmonised BHPS: Waves
  1-18, 1991-2009*. 19th Edition. UK Data Service, SN 6614.
  https://doi.org/10.5255/UKDA-SN-6614-20. The current catalogue lists the
  21st Edition (2026), DOI https://doi.org/10.5255/UKDA-SN-6614-22; confirm
  which edition matches the wave 1 extract used.
- Department for Communities and Local Government and Ipsos MORI. 2012.
  *Citizenship Survey, 2010-2011* [data collection]. UK Data Service, SN
  7111. https://doi.org/10.5255/UKDA-SN-7111-1.
- International Institute for Population Sciences (IIPS) and ORC Macro.
  2000. *National Family Health Survey (NFHS-2), 1998-99: India*. Mumbai:
  IIPS. The IIPS catalogue lists the All-India NFHS-2 files as free, but the
  exact India Members Recode release used should be confirmed from its
  acquisition record.
- Ruggles et al. 2025. *Integrated Public Use Microdata Series,
  International*: Version 7.7. IPUMS. https://doi.org/10.18128/D020.V7.7.
  Samples `586199801` (Pakistan 1998) and `50200101` (Bangladesh 2001).
  Version 7.7 is the current citation recorded in this package, not a
  verified version of the author's extracts; recover the original extract
  citation and statistical-agency acknowledgements before final deposit.
- Office of the Chief Statistician. 2005. *Analysis of Religion in the 2001
  Census*. Scottish Executive.
  https://www.gov.scot/publications/analysis-religion-2001-census/. This is
  the official source report for the Scotland Census evidence, not a
  microdata release.

## Software

Local checks were performed on Windows with StataNow 19 and Python 3.12.7,
NumPy 1.26.4, pandas 2.2.2, SciPy 1.13.1 and Matplotlib 3.9.2. These are
the versions used for the checks, not necessarily those used for the
original analysis. Stata requires a license. Model estimation, particularly Table A12, can be slow.

Set the Python executable in `run_all.do` to an installation containing
the libraries above. Paths and commands below assume Windows and that the
working directory is the package root. On Windows, use a short extraction
path, for example `C:\replication`: the current deep folder location can
exceed Stata's path-length limit.

## Package contents

| Folder or file | Contents |
|---|---|
| `run_all.do` | Configurable driver for selected preparation and analyses. |
| `Preparation` | Census cleaning, reduced-form sample construction and shared model code. |
| `Paper` | Main-text analysis programs and default output locations. |
| `Online Appendix` | Appendix analysis programs and supporting model code. |
| `Synthetic Data` | Artificial inputs, generators and tests. |
| `Data cleaning code` | Historical reference cleaning code. The current driver uses the cleaner in `Preparation`. |

Individual scripts accept paths or use package-relative defaults. Check their
headers and supply input and output arguments when running them separately.
Outputs and intermediates are written in several folders, including the
package tree; ensure those locations are permitted for the chosen data.

## Run with artificial data

The supplied Census CSVs and survey-shaped DTA/CSV files are artificial.
The synthetic 2011 Census fixture includes two local authorities with a
higher Muslim share so the high- and low-share groups required by Figure A17
are both represented; this design is for software checks, not a population-
representative simulation. The Census, Understanding Society and Citizenship
files are generated test fixtures. The India and IPUMS records were independently invented using
`Synthetic Data\generate_artificial_survey_inputs.py`, with seed 20261119;
they were not sampled from those surveys. The older separate India and
IPUMS generators require original data and were not used for the supplied
fixtures.

The following example checks Census cleaning, reduced-form preparation
and Table 1 execution. From the package root in PowerShell, using a Python
installation with the dependencies above:

```powershell
python "Preparation\Data Cleaning\census_cleaning.py" `
  --input-csv "Synthetic Data\Census\synthetic_census_ew_2011.csv" `
  --output-dta "Synthetic Data\Census\synthetic_cleaned.dta"
```

In Stata, set the working directory to the package root and run:

```stata
cd "C:\replication"
do "Preparation\Reduced Form Sample\Code Prepare Reduced Form Data.do" ///
    "Synthetic Data\Census\synthetic_cleaned.dta" ///
    "Preparation\Reduced Form Sample\data_facts.dta"
do "Paper\2 Data & Reduced-Form Evidence\Code Table 1.do" ///
    "Preparation\Reduced Form Sample\data_facts.dta" "Paper\Output"
```

The example assumes the package was placed in `C:\replication`. The
result is `Paper\Output\Table 1.csv`; it is a software check, not an
empirical replication. 

To run other selected stages, edit `run_all.do`: leave `use_synthetic = 1`,
set the desired `run_*` switches to 1, set the others to 0, and run
`do "run_all.do"` in Stata. Later stages depend on cleaned data and model
outputs from earlier stages. The default switches select more than the
verified example above; they do not guarantee a successful complete run.
Regeneration is optional: `run_synthetic = 1` regenerates fixtures, and
can overwrite supplied files. The Census generator default seeds are 2011
and 2001; the Monte Carlo program defaults to seed 20261108.

## Run with authorized data

1. Obtain the required datasets and arrange a permitted computing
   environment. The Census cleaning programs expect CSV extracts with the
   variables and coding used by their respective cleaners, not arbitrary
   downloads from the catalogues above. Check the cleaner and the data
   documentation against the authorized extract.
2. Set Stata's working directory to the package root. Open `run_all.do`
   and set `use_synthetic = 0`, `global python` to the Python executable,
   and the `real_*` data and working paths in the settings block to the
   relevant authorized locations. Create writable parent directories.
   Paths for the 2011 and 2001 Census CSVs, Understanding Society,
   Citizenship, India and IPUMS inputs are separate.
3. Choose stages with the `run_*` switches. Run cleaning and preparation
   before the reduced-form analyses; generate baseline model outputs before
   model-dependent analyses. Consult the exhibit index and individual script
   headers for arguments and dependencies.
4. Run `do "run_all.do"` from the package root. Inspect the Stata log,
   Python error messages and output files for each stage. The final
   `run_all.do finished` message does **not** establish that every Python
   command succeeded. Existing files can be overwritten, and some programs
   reuse existing model results; use fresh work directories for a new run.

By default, the driver writes reduced-form data to
`Preparation\Reduced Form Sample\data_facts.dta`, main tables to
`Paper\Output` for main-paper tables and figures, and `Online Appendix\Output`
for appendix tables and figures. Model files and other intermediate data remain
in their configured model/work directories. Individual scripts also allow
their output locations to be overridden. These locations can contain sensitive derived data when real
inputs are used. Review all outputs under the data provider's rules before
copying or publishing them. The manuscript tables are manually typeset,
and generated CSVs or plots are not automatically inserted into the PDFs.

The historical reference cleaning programs in `Data cleaning code` are
not used by `run_all.do`. If needed, pass `--input-csv` and `--output-csv`
to `census_cleaning.py`; then pass the intermediate CSV and destination
DTA to `cleaning_census.do`. For the current workflow use
`Preparation\Data Cleaning\census_cleaning.py` instead.

### Main paper

| Exhibit | Code or asset |
|---|---|
| Table 1 | `Paper\2 Data & Reduced-Form Evidence\Code Table 1.do`; see the limitations above. |
| Figure 1; Tables 2–3 | Correspondingly named `.do` files in `Paper\2 Data & Reduced-Form Evidence`. |
| Figures 2–3 | Diagrams in the manuscript sources and assets; no generation script identified. |
| Table 4 | `Paper\5 Results\Code Table 4.do`. |
| Figure 4 | `Paper\5 Results\Code Figure 4.py`, using baseline model outputs. |
| Figure 5 | `Paper\5 Results\Code Figure 5.do`, using or generating religion-specific model results. |
| Figure 6 | `Paper\5 Results\Code Figure 6.py`, using religion-specific model results. |
| Figures 7–8 | `Paper\6 Policy Analysis\Code Figure 7.py` and `Code Figure 8.py`, using model outputs. |

### Online appendix

| Exhibit | Code or asset |
|---|---|
| Figures A1–A7 | `Online Appendix\A Appendix Figures & Tables\Code Figure A1.do` through `Code Figure A7.do`, respectively. |
| Tables A1–A4 | Correspondingly named files in `Online Appendix\A Appendix Figures & Tables`. |
| Figure A8 | Supplied diagram `Paper text\fig\simulation.png`. |
| Figures A9–A12 | `Online Appendix\F Toy Model\Code Figures A9-A12.py`. |
| Figure A13 | `Online Appendix\H Monte-Carlo Simulations\Code Figure A13.py`. |
| Table A5 | `Online Appendix\I Model Fit\Table A5 observed.do` computes observed moments from cleaned data; `Code Table A5.py` combines them with model-based simulated moments. |
| Table A6 | `Online Appendix\I Model Fit\Code Table A6.do`. |
| Tables A7–A8 | Correspondingly named scripts in `Online Appendix\J Measurement Error and Robustness of Definition\J2 Alternative Definitions of Marriage Migration`. |
| Table A9 | `Online Appendix\J Measurement Error and Robustness of Definition\J3 Measurement Error\Code Table A9.do`, with its Understanding Society `cleaning.do` and `analysis.do` inputs in the same folder. |
| Table A10 | `Online Appendix\J Measurement Error and Robustness of Definition\J3 Measurement Error\Code Table A10.py`. |
| Table A11 | `Online Appendix\K Robustness to Cohabitation\Code Table A11.do` and `table_a11_migration.py`. |
| Table A12 | `Online Appendix\L Heterogeneity\L1 Heterogeneity by Cohort and Period\Code Table A12.do`. |
| Table A13 | `Online Appendix\L Heterogeneity\L1 Heterogeneity by Cohort and Period\Code Table A13.do`. It processes both Census years and can take a long time. For easier monitoring, run the script incrementally by complete sections in Stata's Do-file Editor and check the log between sections; later sections depend on files and state created earlier. |
| Figure A14; Table A14 | `Online Appendix\L Heterogeneity\L2 Heterogeneity by Nativity Status\Code Figure A14.do` and `Code Table A14.do`. |
| Figure A15 | Supplied asset `Paper text\fig\muslim_dis.png`. |
| Figures A16–A17; Table A15 | `Online Appendix\L Heterogeneity\L3 Heterogeneity by Local Market Population\Code Figure A16.do`, `Code Figure A17.do`, and `Code Table A15.do`, respectively. |
| Tables A16–A17 | Correspondingly named Python scripts in `Online Appendix\M Model Extensions\M1 Nested Matching`. |
| Figures A18–A19 | `Online Appendix\M Model Extensions\M2 Two-Generation Matching\Code Figure A18.py` and `Code Figure A19.py`; each figure's two panels are saved as `Figure A18a.png` / `Figure A18b.png` and `Figure A19a.png` / `Figure A19b.png`. |
| Figure A20 | `Online Appendix\M Model Extensions\M3 Two-Generation Matching with Endogeneous Preferences\Code Figure A20.py`; its panels are saved as `Figure A20a.png` and `Figure A20b.png`. |

