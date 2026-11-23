# README Review (LLM)

_Generated 2026-11-23T19:55:32.264, reviewed `/Users/floswald/Dropbox/Apps/JPE-packages/JPE/Farahzadi-20241111/1/repo/replication-package/replication package for migration for marriage/README.md`_

One quick note: the task framing says "Review of Financial Studies," but the file path and package content ("Migration for Marriage," ONS/UKDS/NFHS/IPUMS data) indicate a labor/development economics paper, likely under a different journal context (the folder suggests JPE). I'll apply the standard Social Science Data Editors checklist regardless, since it's journal-agnostic, but flagging this mismatch so you can confirm the right venue.

# Critical Review: README.md — "Migration for Marriage" Replication Package

## 1. Title and Overview — **Partially**

**Content (README.md:1–7):** Title is given ("Migration for Marriage: Data and Code"), but **no author names** appear anywhere in the README. The overview states the package contains "analysis code and artificial data," that empirical analyses require restricted/licensed data "not included," and that artificial inputs "allow selected code paths to be tested, but do not reproduce the paper's estimates." Line 7: "The author reports that the analyses have been checked on the secure server."

**Issues:**
- No author byline — a data editor and future replicator cannot match this package to the paper without it.
- No stated entry point or total runtime at the top (entry point `run_all.do` only appears later, and no runtime estimate is given anywhere in the document).
- Line 7 is a critical self-undermining statement: it attributes verification to "the author" via third-party hearsay rather than the README author's own confirmation. This signals the README was **not written or independently verified by the author**, and that the stated "checked on secure server" claim is unverified secondhand reporting, not a documented fact.

**Suggestions:**
- Add paper title + full author list at the top, matching the published/forthcoming paper exactly.
- Add a one-line statement of the workflow (prep → model estimation → tables/figures) and the entry point (`run_all.do`), with an approximate runtime for both the synthetic and real-data runs.
- Either remove line 7's hearsay framing or replace it with a first-person, verifiable statement (e.g., "We verified the full real-data pipeline on the ONS Secure Research Service on [date]").

---

## 2. Data Availability and Provenance — **No**

**Content:** There is a "Data access" table (README.md:15–22) describing *how to obtain* the data, but there is no formal Data Availability Statement (DAS) and no rights certifications anywhere in the document.

**Issues:**
- Missing the standard **legitimate-access certification** ("I certify that the author(s)... have legitimate access to and permission to use the data").
- Missing the **redistribution-permission certification**.
- No explicit **public/restricted/proprietary categorization** per dataset (the table conflates access logistics with availability status).
- No data license statement for any of the six datasets (ONS SRS, UKDS 6614, UKDS 7111, NFHS-2, IPUMS International). IPUMS's terms (README.md:22) are described narratively ("cannot be used commercially or redistributed") but not formalized as a license statement.
- No data preservation/retention commitment for the confidential data (ONS SRS, UKDS). The checklist requires a stated retention period (e.g., "preserved for N years post-publication"); none is given.
- The caveat at README.md:11–13 ("links... are not the author's access history... check each provider's current record") is appropriate hygiene for a living document, but it is not a substitute for a DAS — it tells a reader how to apply for data today, not what rights the authors hold or exercised.

**Suggestions:**
- Add an explicit §2 with: (a) external-data statement, (b) both certification statements, (c) per-dataset license line, (d) a public/restricted/proprietary category per row in the access table, (e) a stated data-preservation period for the restricted data.

---

## 3. Summary and Details of Data Sources — **Partially**

**Content:** The "Data access" table (README.md:15–22) and "Data citations" section (README.md:24–60) together cover six sources reasonably well in terms of *where to apply*, but fall short of the structured per-source fields the checklist requires.

**Issues, dataset by dataset:**
- None of the six entries states: format (CSV/DTA/SAV?), whether original data are included (implicitly "No" throughout, but never stated per-row), or download method (automatic vs. manual) in the structured way the checklist expects.
- **Unresolved author TODOs embedded in citations**, which is a serious internal-consistency red flag:
  - README.md:31–32: "confirm the exact CAMS file and citation from the acquisition record" — the citation is not actually confirmed.
  - README.md:39–41: "confirm which edition matches the wave 1 extract used" — UKDS edition is ambiguous (19th ed. cited vs. 21st ed. current).
  - README.md:47–49: "the exact India Members Recode release used should be confirmed."
  - README.md:53–55: "Version 7.7 is the current citation recorded in this package, not a verified version of the author's extracts; recover the original extract citation... **before final deposit**."
  These are not completed citations — they are open action items. A replication package submitted with "before final deposit" language still in the text means final deposit has not actually happened.
- **Orphaned citation**: the Scotland "Analysis of Religion in the 2001 Census" source report (README.md:56–60) appears in Data Citations but is not tied to any dataset in the access table or any exhibit in §7's mapping. It's unclear what it supports.
- **Pseudo-data success is explicitly disclaimed, not confirmed.** The checklist asks "is it stated that the pseudo-data successfully run the code?" Here the opposite is stated: README.md:131–133, "Later stages depend on cleaned data and model outputs from earlier stages... they do not guarantee a successful complete run," and README.md:155–159, the final "finished" message "does **not** establish that every Python command succeeded." Only one narrow path (Census cleaning → reduced-form prep → Table 1) is explicitly verified (README.md:104–127). This is a hard blocker: the synthetic-data pipeline, as documented, is not confirmed to run end-to-end.
- Pseudo-data location is stated (`Synthetic Data/`, README.md:83, 91–102) and is good practice — but their fidelity to the real data's structure is only asserted for the Census/Understanding Society/Citizenship fixtures ("generated test fixtures," README.md:97) and explicitly *not* for India/IPUMS, which were "independently invented... not sampled from those surveys" (README.md:98–99). This is a reasonable disclosure, but it means these two fixtures cannot be relied on as structural stand-ins for a codebook.
- No summary table mapping each data *file* to source/format/inclusion status as recommended by the checklist (the access table is source-level, not file-level).
- "Proprietary data removed from public upload" — satisfied in spirit (no real restricted data appears in the package), but never explicitly stated as a compliance assertion.

**Suggestions:**
- Resolve every "confirm X" / "recover the original extract citation... before final deposit" item before submission — these cannot ship as open questions.
- Add a file-level summary table (file → source → format → included Y/N → license).
- Add an explicit statement: "The replication package does not violate any data provider's license agreements" (once actually verified).
- State a preservation period for confidential data.

---

## 4. Computational Requirements — **No**

**Content (README.md:62–73):** Software versions are given fairly well: "Windows with StataNow 19 and Python 3.12.7, NumPy 1.26.4, pandas 2.2.2, SciPy 1.13.1 and Matplotlib 3.9.2" — but immediately qualified as "the versions used for the checks, not necessarily those used for the original analysis" (README.md:65–66).

**Issues:**
- No Stata user-written package (ado) dependencies listed at all, despite multiple `.do` files presumably using them.
- No dependency manifest referenced (no `requirements.txt`/`environment.yml` found alongside the README; confirmed absent by direct check).
- **No runtime estimate anywhere**, quantitative or otherwise — only qualitative warnings: "Model estimation, particularly Table A12, can be slow" (README.md:67) and Table A13 "can take a long time" (README.md:206).
- **No storage, RAM, or CPU figures at all**, for either the pseudo-data run or the real-data run — the checklist explicitly asks for both, separately.
- No description of the machine used for the last real execution (only "local checks" on an unspecified Windows machine, README.md:64).
- Randomness is only partly addressed: fixture-generation seeds are given (2011/2001 Census defaults, Monte Carlo default 20261108, IPUMS/India generator seed 20261119 — README.md:99, 135–136), but nothing is said about random-number use *within estimation* (e.g., simulated moments, bootstrap, Monte Carlo robustness in the actual model).
- **Paths are not OS-agnostic**: backslashes are used throughout (`run_all.do`, README examples), the README states "Paths and commands below assume Windows" (README.md:70), and the one worked example is PowerShell-only (README.md:108–123). Checklist item explicitly fails.
- Line 72–73 flags its own path-length risk ("the current deep folder location can exceed Stata's path-length limit") — this is a known defect being shipped rather than fixed; folder names also contain spaces and an ampersand (`Paper\2 Data & Reduced-Form Evidence`), which is fragile for shell invocation on any platform.

**Suggestions:**
- Add explicit storage/RAM/CPU figures, separately for synthetic and real-data runs.
- Add a quantitative runtime range for both, flagging Table A12/A13 as the long pole.
- List Stata ado dependencies and their versions (or ship them in an `ado/` folder).
- State the exact machine (OS version, CPU, RAM) used for the last real-data run (likely only possible on the secure server — state that explicitly if so).
- Either fix the path-length/ folder-naming issue or document the required workaround as a hard prerequisite, not an aside.

---

## 5. Description of Programs — **Partially**

**Content (README.md:75–89, 128):** `run_all.do` is identified as the "configurable driver" and its structure is explained in reasonable detail, including folder roles (`Preparation`, `Paper`, `Online Appendix`, `Synthetic Data`, `Data cleaning code`). Confirmed by direct inspection: `run_all.do` matches the README's description (settings block, `use_synthetic` switch, `run_*` switches, shell calls to Python, `.do` calls to Stata sub-scripts).

**Issues:**
- **No code license is stated anywhere** in the README, and no `LICENSE`/`LICENSE.txt` file exists in the package root (confirmed absent).
- Ordering dependencies are described narratively but not systematically: README.md:151–152 says "Run cleaning and preparation before the reduced-form analyses; generate baseline model outputs before model-dependent analyses," which requires the user to infer the DAG rather than being given it directly (e.g., as a diagram or ordered list).
- `Data cleaning code` is explicitly dead code (README.md:84, 171–175: "not used by `run_all.do`... For the current workflow use `Preparation\Data Cleaning\census_cleaning.py` instead") yet still ships in the package, inviting a replicator to run the wrong script.
- Three exhibits have **no generating code at all**: Figures 2–3 ("Diagrams in the manuscript sources and assets; no generation script identified," README.md:183), Figure A8 (supplied PNG, README.md:196), Figure A15 (supplied PNG, README.md:208). For a package meant to allow full reproduction, undocumented-provenance images are a reproducibility gap, not just a formatting note.

**Suggestions:**
- Add a code license (e.g., MIT/BSD) and a `LICENSE.txt` file; state it explicitly in the README.
- Either remove `Data cleaning code` or move it to a clearly-labeled `deprecated/` or `historical/` folder, with a note that it is not part of any current workflow.
- For Figures 2–3, A8, A15: state explicitly how these were produced (hand-drawn diagram? exported from software X? simulation output copied in manually?) even if no automatic regeneration script exists.

---

## 6. Instructions to Replicators — **Partially**

**Content:** Two clear workflows are given: "Run with artificial data" (README.md:91–136) with a fully worked PowerShell/Stata example (README.md:104–123), and "Run with authorized data" (README.md:138–175) as a 4-step procedure.

**Issues:**
- The worked example only verifies **one narrow path** (census cleaning → reduced-form prep → Table 1); the rest of the pipeline under `use_synthetic=1` is explicitly *not* guaranteed to succeed (README.md:131–133).
- Step 2 of "Run with authorized data" (README.md:146–148) requires manually editing `global` paths inside `run_all.do` — this is a manual/non-automated step, which is acceptable, but it should be flagged as such explicitly under a "manual steps" heading per the checklist, not just embedded in prose.
- No statement that the authors verified these instructions in a clean environment (and the opposite is suggested: line 7's hearsay framing and the explicit "does not guarantee a successful complete run" caveats indicate the full real-data pipeline was *not* independently re-verified by whoever wrote this README).
- Internet/credential requirements are implicit (SRS accreditation, UKDS registration, IPUMS individual licensing) but never collected into a single "you will need" prerequisite list at the top of the instructions.
- "Use a short extraction path... can exceed Stata's path-length limit" (README.md:72–73) is an operational workaround presented as an aside rather than a clearly flagged step-0 prerequisite.

**Suggestions:**
- Add an explicit "Prerequisites" subsection before the numbered steps: required accreditations/licenses, required local software, required manual edits.
- State plainly whether the authors (or anyone) ran the full instructions end-to-end in a clean environment, and if not, say so rather than letting the reader infer it from scattered caveats.
- Collapse the path-length workaround into step 1 of both workflows.

---

## 7. List of Tables and Programs — **Partially**

**Content:** Two detailed mapping tables are given (README.md:179–188 for main paper, README.md:192–212 for appendix), covering essentially every table/figure in the paper and online appendix.

**Issues:**
- Coverage claim implicit, not explicit — the README never states "this package reproduces all tables and figures in the main paper and online appendix" (true in spirit, but should be asserted and scoped, especially given the caveats about restricted exhibits).
- **No output filenames** are given for almost any exhibit — only Table 1's output (`Paper\Output\Table 1.csv`, README.md:126) and the A18–A20 panel names are specified. A replicator running Table 4 or Figure 5, say, has no way to know what the output file will be called without opening the script.
- "**Correspondingly named**" is used repeatedly as a shortcut (Figure 1/Tables 2–3 at README.md:182; Tables A1–A4 at README.md:195; A7–A8 at README.md:201; A16–A17 at README.md:210) instead of listing exact filenames — this is imprecise and should be replaced with literal names, especially since file names elsewhere include irregular capitalization and spacing (e.g., "Code Table 1.do" vs. a hypothetical "Code_Table1.do").
- **Mismatch**: the "Data access" table (README.md:21–22) maps NFHS-2 and the IPUMS samples to **Figure A4**, but the appendix mapping table collapses Figures A1–A7 into a single range ("`Code Figure A1.do` through `Code Figure A7.do`, respectively," README.md:194) without flagging that A4 specifically depends on India/IPUMS data, unlike its neighbors. (Confirmed independently: `run_all.do` line 194 does pass `$india_dta` and `$ipums_dta` specifically to Figure A4's script, so the dependency is real but invisible in the README's table.)

**Suggestions:**
- Add literal filenames for every exhibit's output (even if derived mechanically from the table/figure number, state the pattern explicitly, e.g., "`<Exhibit Name>.csv` in `Paper\Output`").
- Replace all "correspondingly named" shortcuts with explicit filenames.
- Annotate Figure A4 in the mapping table with its India/IPUMS data dependency, to match what `run_all.do` actually does.

---

## 8. References — **Partially**

**Content (README.md:24–60):** Six citations given, each with a dataset or source-report reference, several including DOIs.

**Issues:**
- As noted in §3, four of the six citations contain **unresolved verification TODOs** rather than being finalized references (CAMS file ID, UKDS edition, NFHS-2 release, IPUMS extract version/statistical-agency acknowledgements). A reference list with "confirm... before final deposit" language is not a finished reference list.
- The Scotland source-report citation (README.md:56–60) is not linked to any exhibit or dataset elsewhere in the document — its relevance is unclear to a reader.
- No persistent identifier is given for the NFHS-2 citation (unlike the ONS and UKDS entries, which include DOIs).

**Suggestions:**
- Resolve all open citation TODOs before submission; this is likely the single most mechanical fix needed.
- Either tie the Scotland citation explicitly to the exhibit it supports (which table/figure uses the "Analysis of Religion in the 2001 Census" report?) or remove it.
- Add a persistent identifier for the NFHS-2 citation if one exists (IIPS DOI or catalogue permalink).

---

## 9. Acknowledgements — **No**

**Content:** No acknowledgements section exists in the README (it ends at the appendix exhibit table, README.md:212–214).

**Issues:**
- If this README was adapted from the Social Science Data Editors' template (which its structure strongly resembles), that should be acknowledged per the template's own request.
- No funding, data-provider, or disclosure acknowledgements are present (separate from the paper's own acknowledgements section, but conventionally included in READMEs).

**Suggestions:**
- Add a short acknowledgements section crediting the README template source if applicable, and any required data-provider acknowledgement language (e.g., IPUMS requires citation of "relevant statistical agencies," README.md:22 — that specific acknowledgement text should appear here if the provider's terms require it in distributed outputs).

---

## Final Assessment

**Verdict: Needs major revision.**

The most damaging problem is not any single missing section but the **document's own internal admission that it is an unfinished, third-party working draft, not a verified README**:
- README.md:7 attributes the core verification claim to secondhand reporting ("the author reports...") rather than a first-person confirmation by whoever prepared this package for deposit.
- Four separate citations (README.md:31–32, 39–41, 47–49, 53–55) contain explicit "confirm X" / "recover... before final deposit" instructions to the author that have evidently not yet been carried out.
- The synthetic-data pipeline is explicitly *not* confirmed to run end-to-end (README.md:131–133, 155–159); only one narrow sub-path is verified.

A data editor reading this document as-is should conclude it is not ready for deposit — it reads as a review draft with embedded TODOs rather than a finished, author-certified submission.

**Prioritized fixes (blocking, in order):**
1. **Resolve or remove every embedded "confirm/recover before final deposit" TODO** (§3, §8) — citations must be final, not provisional.
2. **Add a Data Availability Statement with both certification statements** (legitimate access; redistribution permission) — currently entirely absent (§2).
3. **Either make the synthetic-data pipeline actually run end-to-end and say so plainly, or scope down the claimed coverage** to match what is genuinely verified — do not ship caveats stating the opposite of what the checklist requires ("does not guarantee a successful complete run," "does not establish that every Python command succeeded").
4. **Replace line 7's hearsay verification claim with a first-person, dated, verifiable statement**, or remove the claim if it cannot be substantiated by whoever is submitting.
5. **Add data licenses, code license (+ `LICENSE.txt`), and a stated preservation period** for the restricted ONS SRS/UKDS data.
6. **Add quantitative runtime, storage, RAM, and CPU figures**, separately for the synthetic and real-data runs, and name the real-execution machine.
7. **Fix OS-dependence**: either generalize paths/scripts beyond Windows/PowerShell, or explicitly scope the package as Windows-only and say why (e.g., Stata path-length issue is itself evidence the package wasn't designed cross-platform).

**Secondary fixes (should fix, not blocking):**
- Add author names and a top-level entry-point/runtime summary (§1).
- Add file-level data summary table and exact output filenames for every exhibit, replacing all "correspondingly named" shortcuts (§3, §7).
- Resolve the Figure A4 ↔ India/IPUMS dependency gap between the access table and the exhibit mapping table.
- Tie or remove the orphaned Scotland citation.
- Remove or clearly quarantine the dead `Data cleaning code` folder.
- Document provenance for the three code-less exhibits (Figures 2–3, A8, A15).
- Fix the broken markdown table row at README.md:19 (missing trailing `|`).
- Add an acknowledgements section (template credit, provider-required acknowledgement text).

**General best-practice suggestion:** Given how many caveats in this README function as hedges against the authors' own uncertainty about what has and hasn't been verified, the package would benefit from a single short "Verification status" subsection stating precisely which paths have been run to completion, by whom, on what data (synthetic/real), and when — rather than scattering that information as inline caveats across six different sections.
