"""Create the analysis-ready person/spouse dataset from Census records.

It expects the secure 2011 Census household-level extract;
the included synthetic CSV is only for checking that the pipeline runs.
"""

import argparse
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    PACKAGE_ROOT / "Synthetic Data" / "Census" / "synthetic_census_ew_2011.csv"
)
DEFAULT_OUTPUT = PACKAGE_ROOT / "Synthetic Data" / "Census" / "synthetic_cleaned.dta"

QUALIFICATION_COLUMNS = [f"QUALS{number:02}" for number in range(1, 15)]

# Source variable -> spouse variable in the output dataset.
SPOUSE_VARIABLES = {
    "age": "sage",
    "immigrant": "simmigrant",
    "immigrant18": "simmigrant18",
    "ethnicity": "sethnicity",
    "religion": "sreligion",
    "edu_level": "sedu_level",
    "tertiary_education": "stertiary_education",
    "employed": "semployed",
    "lang_prof": "slang_prof",
    "ETHNICITYEW": "sETHNICITYEW",
    "ETHNIC_INDEX": "sETHNIC_INDEX",
    "COB": "sCOB",
    "IDENTITY": "sIDENTITY",
    "ISCO": "sISCO",
    **{column: f"s{column}" for column in QUALIFICATION_COLUMNS},
}

PERSON_OUTPUT_COLUMNS = [
    "ID",
    "region",
    "age",
    "sex",
    "immigrant",
    "immigrant18",
    "single",
    "cohabiting",
    "married",
    "divorced",
    "widowed",
    "ethnicity",
    "religion",
    "edu_level",
    "tertiary_education",
    "employed",
    "unemployed",
    "health",
    "lang_prof",
    "ETHNICITYEW",
    "ETHNIC_INDEX",
    "COB",
    "IDENTITY",
    "ISCO",
    *QUALIFICATION_COLUMNS,
    "LA",
    "MOVEREGION",
]

SPOUSE_OUTPUT_COLUMNS = [
    "ID",
    "coupleid",
    *SPOUSE_VARIABLES.values(),
]

BOOLEAN_COLUMNS = [
    "immigrant",
    "single",
    "cohabiting",
    "married",
    "divorced",
    "widowed",
    "employed",
    "unemployed",
]

ANALYSIS_VARIABLES = [
    "age",
    "sage",
    "sex",
    "lang_prof",
    "slang_prof",
    "ethnicity",
    "sethnicity",
    "religion",
    "sreligion",
    "edu_level",
    "sedu_level",
    "tertiary_education",
    "stertiary_education",
    "health",
]


def parse_args() -> argparse.Namespace:
    """Parse paths for the raw person file and final Stata dataset."""
    parser = argparse.ArgumentParser(
        description="Build the analysis-ready Census person/spouse dataset."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=DEFAULT_INPUT,
        help=(
            "Raw person-level Census CSV. The default is the included "
            "synthetic fixture, not the secure Census data."
        ),
    )
    parser.add_argument(
        "--output-dta",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the final analysis dataset in Stata format.",
    )
    parser.add_argument(
        "--age-threshold",
        type=int,
        default=18,
        help=(
            "Arrival-age threshold defining adult migrants (default 18), "
            "used for the Table A8 sensitivity datasets. The output "
            "variable keeps the name immigrant18."
        ),
    )
    parser.add_argument(
        "--cohabitation-as-marriage",
        action="store_true",
        help=(
            "Treat cohabiting couples (HPARTNER == 2) as married couples, "
            "as in the Table A11 sensitivity analysis."
        ),
    )
    args = parser.parse_args()
    if args.output_dta.suffix.lower() != ".dta":
        parser.error("--output-dta must have a .dta extension")
    return args


def add_person_variables(
    raw: pd.DataFrame, age_threshold: int = 18
) -> pd.DataFrame:
    """Create person identifiers and analysis variables from raw Census codes."""
    data = raw.copy()
    data["ID"] = data["HHID"].astype(str) + data["PERSID"].astype(str)

    # Collapse the detailed England/Wales ethnicity categories into the
    # nine-category classification used in the paper. Unmapped codes retain
    # the original -9 sentinel until the final missing-value conversion.
    ethnicity_map = {
        **{code: 1 for code in range(1, 5)},
        **{code: 2 for code in range(5, 9)},
        9: 3,
        10: 4,
        11: 5,
        12: 6,
        13: 6,
        14: 7,
        15: 7,
        16: 7,
        17: 8,
        18: 9,
    }
    data["ethnicity"] = data["ETHNICITYEW"].map(ethnicity_map).fillna(-9)

    # A person is an immigrant if their country-of-birth code is outside the
    # UK code range. Adult arrival is initially missing for unknown arrival
    # year (-9), so that sentinel remains distinguishable until sample
    # restrictions are applied.
    data["immigrant"] = (data["COB"] < 921) | (data["COB"] > 926)
    data["immigrant18"] = (
        (data["AGEC"] - (2011 - data["YRARR_YEAR"]) >= age_threshold)
        & data["immigrant"]
    ).astype(object)
    unknown_arrival = data["immigrant"] & data["YRARR_YEAR"].eq(-9)
    data.loc[unknown_arrival, "immigrant18"] = -9

    data["single"] = data["MARSTAT"].eq(1)
    data["cohabiting"] = data["HPARTNER"].eq(2)
    data["married"] = data["MARSTAT"].isin((2, 6))
    data["divorced"] = (
        data["MARSTAT"].between(3, 4) | data["MARSTAT"].between(7, 8)
    )
    data["widowed"] = data["MARSTAT"].isin((5, 9))

    data["edu_level"] = data["ISCED"]
    data["tertiary_education"] = data["ISCED"].gt(4).astype(object)
    data.loc[data["ISCED"].eq(-9), "tertiary_education"] = -9

    data["employed"] = data["ACTLWO"].eq(1)
    data["unemployed"] = data["ACTLWO"].eq(2)

    return data.rename(
        columns={
            "AGEC": "age",
            "SEX": "sex",
            "HEALTH": "health",
            "RELIGIONEW": "religion",
            "REGION": "region",
            "LANGPRF": "lang_prof",
        }
    )


def build_spouse_records(
    people: pd.DataFrame, cohabitation_as_marriage: bool = False
) -> pd.DataFrame:
    """Identify current partners and attach each partner's selected variables.

    Partners are legally married spouses (HSPOUSE == 2, relationship code 1);
    with cohabitation_as_marriage, household partners (HPARTNER == 2,
    relationship code 3) are linked in the same way.
    """
    is_spouse = people["HSPOUSE"].eq(2)
    is_cohabiting = pd.Series(False, index=people.index)
    if cohabitation_as_marriage:
        is_cohabiting = people["HPARTNER"].eq(2) & ~is_spouse
    married = people.loc[is_spouse | is_cohabiting].copy()
    relationship_code = is_spouse.loc[married.index].map({True: 1, False: 3})

    # REL1...REL15 identify the partner's person number within the household.
    married["SPOUID"] = sum(
        married[f"REL{number}"].eq(relationship_code).astype(int) * number
        for number in range(1, 16)
    )

    # Build the same ordered couple identifier from either partner's record.
    married["coupleid"] = ""
    husband = married["sex"].eq(1) & married["SPOUID"].gt(0)
    wife = married["sex"].eq(2) & married["SPOUID"].gt(0)
    married.loc[husband, "coupleid"] = (
        married.loc[husband, "HHID"].astype(str)
        + married.loc[husband, "PERSID"].astype(str)
        + married.loc[husband, "SPOUID"].astype(str)
    )
    married.loc[wife, "coupleid"] = (
        married.loc[wife, "HHID"].astype(str)
        + married.loc[wife, "SPOUID"].astype(str)
        + married.loc[wife, "PERSID"].astype(str)
    )

    married = married.loc[married["coupleid"].ne("")].copy()
    couple_size = married.groupby("coupleid").size()
    married = married.loc[
        married["coupleid"].map(couple_size).eq(2)
    ].copy()
    married = married.sort_values(["coupleid", "sex"]).copy()

    # Sex is coded 1=husband and 2=wife. After sorting, first/last values are
    # therefore husband/wife values. Assign the opposite partner's value to
    # each record.
    for source, spouse in SPOUSE_VARIABLES.items():
        by_couple = married.groupby("coupleid", sort=False)[source]
        husband_value = by_couple.transform("first")
        wife_value = by_couple.transform("last")
        married[spouse] = wife_value * (2 - married["sex"]) + (
            husband_value * (married["sex"] - 1)
        )

    return married[SPOUSE_OUTPUT_COLUMNS]


def clean_analysis_dataset(data: pd.DataFrame) -> pd.DataFrame:
    """Apply the former Stata cleaning stage and standardize output types."""
    data = data.copy()
    for column in BOOLEAN_COLUMNS:
        data[column] = data[column].astype("int8")

    data["immigrant18"] = pd.to_numeric(data["immigrant18"])
    data["tertiary_education"] = pd.to_numeric(data["tertiary_education"])

    # Compute the local-authority Muslim share before restricting the sample.
    # Missing and non-Muslim religion codes remain in the LA denominator.
    muslim = data["religion"].eq(6).astype("float64")
    muslim.loc[data["religion"].isna() | data["religion"].eq(9)] = pd.NA
    authority = data.groupby("LA", dropna=False)["ID"]
    authority_size = authority.transform("size")
    authority_muslims = muslim.groupby(
        data["LA"], dropna=False
    ).transform("sum")
    data["la_muslim_share"] = authority_muslims.div(authority_size)

    data["ukborn"] = 1 - data["immigrant"]

    # Exclude immigrants known to have arrived at age 18 or older and those
    # whose arrival age cannot be classified. UK-born people are retained.
    in_analysis_sample = data["immigrant18"].eq(0) | data["ukborn"].eq(1)
    data = data.loc[in_analysis_sample].copy()

    # Convert negative category sentinels to Stata/Pandas missing values only
    # for the variables used in the paper's analyses.
    for column in ANALYSIS_VARIABLES:
        values = pd.to_numeric(data[column], errors="raise")
        data[column] = values.mask(values < 0)

    # Convert selected raw Census fields to numeric for Stata export; keep IDs
    # and local-authority codes as strings to preserve leading zeros.
    for column in data.select_dtypes(include="object").columns:
        if column not in {"ID", "coupleid", "LA"}:
            data[column] = pd.to_numeric(data[column], errors="raise")

    if data["ID"].str.fullmatch(r"\d+").all():
        data["ID"] = pd.to_numeric(data["ID"], errors="raise")

    couple_ids = data["coupleid"].replace("", pd.NA)
    if couple_ids.dropna().str.fullmatch(r"\d+").all():
        data["coupleid"] = pd.to_numeric(couple_ids, errors="raise")

    data.columns = data.columns.str.lower()
    return data


def build_analysis_dataset(
    raw: pd.DataFrame,
    age_threshold: int = 18,
    cohabitation_as_marriage: bool = False,
) -> pd.DataFrame:
    """Run person coding, spouse linking, merging, and final sample cleaning."""
    people = add_person_variables(raw, age_threshold)
    spouse_records = build_spouse_records(people, cohabitation_as_marriage)

    person_records = people[PERSON_OUTPUT_COLUMNS]
    merged = pd.merge(
        person_records,
        spouse_records,
        how="outer",
        on="ID",
    )
    return clean_analysis_dataset(merged)


def main() -> None:
    """Read the raw CSV, construct analysis data, and write a Stata file."""
    args = parse_args()
    raw = pd.read_csv(args.input_csv)
    cleaned = build_analysis_dataset(
        raw, args.age_threshold, args.cohabitation_as_marriage
    )

    args.output_dta.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_stata(args.output_dta, write_index=False, version=118)
    print(
        f"Wrote {len(cleaned):,} analysis records and "
        f"{len(cleaned.columns):,} variables to {args.output_dta}"
    )


if __name__ == "__main__":
    main()
