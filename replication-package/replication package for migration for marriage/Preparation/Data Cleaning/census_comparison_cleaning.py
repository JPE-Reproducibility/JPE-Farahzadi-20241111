"""Person and spouse records for the 2001 vs 2011 census comparison (Table A13).

Unlike the main cleaning pipeline, these records keep the couple link only
for present, married spouses. `Code Table A13.do` uses the spouse's
foreign-born status to define marriage migration and reads this output.

Usage:
    python census_comparison_cleaning.py --year 2001 input_2001.(csv|dta) data2001.csv
    python census_comparison_cleaning.py --year 2011 input_2011.csv data2011.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

UK_BORN_2001 = (640, 2200, 1520, 1790)
UK_BORN_2011 = (921, 926)
OUTPUT_PERSON_COLUMNS = (
    "ID", "age", "sex", "immigrant", "single", "married",
    "ethnicity", "religion", "tertiary_education",
)
SPOUSE_COLUMNS = (
    "age", "tertiary_education", "religion", "ethnicity", "immigrant",
)


def read_input(path):
    path = Path(path)
    if path.suffix.lower() == ".dta":
        return pd.read_stata(path, convert_categoricals=False)
    return pd.read_csv(path)


def clean_2001(df):
    df = df.copy()
    df["ID"] = df.ukhhid.astype(str) + df.persid.astype(str)

    ethewx = df.ethewx
    df["ethnicity"] = -9
    df.loc[ethewx == 1, "ethnicity"] = 0  # White British
    df.loc[(ethewx == 2) | (ethewx == 3), "ethnicity"] = 1  # other White
    df.loc[(ethewx >= 4) & (ethewx <= 7), "ethnicity"] = 2  # mixed
    df.loc[ethewx == 8, "ethnicity"] = 3  # Indian
    df.loc[ethewx == 9, "ethnicity"] = 4  # Pakistani
    df.loc[ethewx == 10, "ethnicity"] = 5  # Bangladeshi
    df.loc[(ethewx == 11) | (ethewx == 15), "ethnicity"] = 6  # other Asian
    df.loc[(ethewx >= 12) & (ethewx <= 14), "ethnicity"] = 7  # Black
    df.loc[ethewx == 16, "ethnicity"] = 9  # other

    ukborn = df.cobpuk.isin(UK_BORN_2001)
    df["immigrant"] = (~ukborn).astype(int)
    df.loc[df.cobpuk == -9, "immigrant"] = -9

    df["single"] = (df.marstat == 1).astype(int)
    df["married"] = df.marstat.isin((2, 3)).astype(int)

    df["tertiary_education"] = (df.qualvewn == 5).astype(int)
    df.loc[df.qualvewn == -9, "tertiary_education"] = -9

    df = df.rename(columns={"age0x": "age", "relgew": "religion"})
    couples = df[df.reltohr.isin((1, 2)) & (df.married == 1)].copy()
    couples["coupleid"] = couples.hhid.astype(str)
    return df, couples


def clean_2011(df):
    df = df.copy()
    df["ID"] = df.HHID.astype(str) + df.PERSID.astype(str)

    eth = df.ETHNICITYEW
    df["ethnicity"] = -9
    df.loc[eth == 1, "ethnicity"] = 0  # White British
    df.loc[(eth >= 2) & (eth <= 4), "ethnicity"] = 1  # other White
    df.loc[(eth >= 5) & (eth <= 8), "ethnicity"] = 2  # mixed
    df.loc[eth == 9, "ethnicity"] = 3  # Indian
    df.loc[eth == 10, "ethnicity"] = 4  # Pakistani
    df.loc[eth == 11, "ethnicity"] = 5  # Bangladeshi
    df.loc[(eth >= 12) & (eth <= 13), "ethnicity"] = 6  # other Asian
    df.loc[(eth >= 14) & (eth <= 16), "ethnicity"] = 7  # Black
    df.loc[eth == 17, "ethnicity"] = 8  # Arab
    df.loc[eth == 18, "ethnicity"] = 9  # other

    df["immigrant"] = ((df.COB < UK_BORN_2011[0]) | (df.COB > UK_BORN_2011[1])).astype(int)
    df["single"] = (df.MARSTAT == 1).astype(int)
    df["married"] = df.MARSTAT.isin((2, 6)).astype(int)

    df["tertiary_education"] = (df.ISCED > 4).astype(int)
    df.loc[df.ISCED == -9, "tertiary_education"] = -9

    df = df.rename(columns={"AGEC": "age", "SEX": "sex", "RELIGIONEW": "religion"})

    couples = df[df.HSPOUSE == 2].copy()
    spouse_position = np.zeros(len(couples), dtype=int)
    for index in range(1, 16):
        spouse_position += (couples[f"REL{index}"] == 1).to_numpy() * index
    couples["SPOUID"] = spouse_position
    hhid = couples.HHID.astype(str)
    persid = couples.PERSID.astype(str)
    spouid = couples.SPOUID.astype(str)
    couples["coupleid"] = ""
    men = (couples.sex == 1) & (couples.SPOUID > 0)
    women = (couples.sex == 2) & (couples.SPOUID > 0)
    couples.loc[men, "coupleid"] = hhid[men] + persid[men] + spouid[men]
    couples.loc[women, "coupleid"] = hhid[women] + spouid[women] + persid[women]
    couples = couples[couples.coupleid != ""]
    return df, couples


def add_spouse_values(couples, column):
    """Spouse's value of `column`: the wife's for men, the husband's for women."""
    couples = couples.sort_values(["coupleid", "sex"])
    first = couples.groupby("coupleid")[column].first()
    last = couples.groupby("coupleid")[column].last()
    from_wife = couples.coupleid.map(last)
    from_husband = couples.coupleid.map(first)
    name = f"s{column}"
    couples[name] = np.where(couples.sex == 1, from_wife, from_husband)
    return couples


def build_records(people, couples):
    size = couples.groupby("coupleid").coupleid.transform("size")
    couples = couples[size == 2].copy()
    couples = couples[["ID", "coupleid", "sex", *SPOUSE_COLUMNS]]
    for column in SPOUSE_COLUMNS:
        couples = add_spouse_values(couples, column)
    spouse_info = couples[
        ["ID", "coupleid", "sage", "simmigrant", "sethnicity", "sreligion",
         "stertiary_education"]
    ]
    return pd.merge(people[list(OUTPUT_PERSON_COLUMNS)], spouse_info,
                    how="outer", on="ID")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, choices=(2001, 2011), required=True)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    raw = read_input(args.input)
    people, couples = clean_2001(raw) if args.year == 2001 else clean_2011(raw)
    records = build_records(people, couples)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    records.to_csv(args.output, index=False)
    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
