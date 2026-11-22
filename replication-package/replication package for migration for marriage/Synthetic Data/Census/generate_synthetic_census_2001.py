"""Generate a deterministic, wholly artificial 2001 Census-shaped test dataset.

Columns follow what `Preparation/Data Cleaning/census_comparison_cleaning.py --year 2001`
reads from the restricted 2001 household CAM file. The value codes are
placeholders that are consistent with that script only: ETHEWX 1-16, COBPUK
(640/2200/1520/1790 = UK-born), QUALVEWN 5 = degree level, RELGEW 5 = Muslim
(the cleaning script shifts the codes by one so that 6 = Muslim), MARSTAT
1 = single, 2/3 = married, RELTOHR 1/2 = household head / head's spouse.
"""

import argparse
import csv
import random
from pathlib import Path

INPUT_COLUMNS = (
    "ukhhid", "persid", "hhid", "age0x", "sex", "ethewx", "cobpuk",
    "marstat", "qualvewn", "relgew", "reltohr",
)
UK_BORN_CODES = (640, 2200, 1520, 1790)
FOREIGN_BORN_CODES = (1000, 1100, 1200, 3560, 5860, 500)
ETHNIC_CODES = tuple(range(1, 17))
ETHNIC_WEIGHTS = (88.0, 1.3, 0.1, 0.4, 0.3, 0.3, 0.3, 1.9, 1.3, 0.5, 0.3, 0.6,
                  1.1, 0.6, 0.2, 0.4)
RELIGION_CODES = tuple(range(0, 9))
RELIGION_WEIGHTS = (71.0, 0.3, 1.0, 0.5, 1.0, 0.6, 0.3, 7.0, 15.0)
MUSLIM_CODE = 5
PAKISTANI_BANGLADESHI = (9, 10)
SOUTH_ASIAN = (8, 9, 10)
DEGREE = 5
OTHER_QUALIFICATION = (1, 2, 3, 4)


def choice(rng, values, weights):
    return rng.choices(values, weights=weights, k=1)[0]


def draw_age(rng):
    ages = tuple(range(20, 61))
    return choice(rng, ages, tuple(max(1, 18 - abs(age - 38)) for age in ages))


def draw_religion(rng, ethnicity):
    if ethnicity in PAKISTANI_BANGLADESHI and rng.random() < 0.92:
        return MUSLIM_CODE
    if ethnicity == 8 and rng.random() < 0.15:
        return MUSLIM_CODE
    if ethnicity in SOUTH_ASIAN and rng.random() < 0.6:
        return rng.choice((2, 4))
    return choice(rng, RELIGION_CODES, RELIGION_WEIGHTS)


def draw_education(rng):
    return DEGREE if rng.random() < 0.2 else rng.choice(OTHER_QUALIFICATION)


def person(rng, household, person_id, age, sex, ethnicity, religion, education,
           marstat, relation, foreign_born=False):
    return {
        "ukhhid": household,
        "persid": person_id,
        "hhid": household,
        "age0x": age,
        "sex": sex,
        "ethewx": ethnicity,
        "cobpuk": rng.choice(FOREIGN_BORN_CODES if foreign_born else UK_BORN_CODES),
        "marstat": marstat,
        "qualvewn": education,
        "relgew": religion,
        "reltohr": relation,
    }


def couple_rows(rng, household):
    ethnicity = choice(rng, ETHNIC_CODES, ETHNIC_WEIGHTS)
    religion = draw_religion(rng, ethnicity)
    same_ethnicity = rng.random() < (0.97 if ethnicity != 1 else 0.96)
    spouse_ethnicity = ethnicity if same_ethnicity else choice(rng, ETHNIC_CODES, ETHNIC_WEIGHTS)
    same_religion = rng.random() < (0.97 if religion == MUSLIM_CODE else 0.8)
    spouse_religion = religion if same_religion else draw_religion(rng, spouse_ethnicity)
    education = draw_education(rng)
    spouse_education = education if rng.random() < 0.65 else draw_education(rng)

    # Marriage migrants: a foreign-born spouse, far more common in South Asian families.
    migrant_probability = 0.35 if ethnicity in PAKISTANI_BANGLADESHI else 0.08
    migrant_side = rng.choice((1, 2)) if rng.random() < migrant_probability else 0
    husband_age = draw_age(rng)
    wife_age = min(60, max(20, husband_age + rng.randint(-6, 6)))
    marstat = choice(rng, (2, 3), (88, 12))
    return [
        person(rng, household, 1, husband_age, 1, ethnicity, religion, education,
               marstat, 1, foreign_born=migrant_side == 1),
        person(rng, household, 2, wife_age, 2, spouse_ethnicity, spouse_religion,
               spouse_education, marstat, 2, foreign_born=migrant_side == 2),
    ]


def single_row(rng, household):
    ethnicity = choice(rng, ETHNIC_CODES, ETHNIC_WEIGHTS)
    return person(
        rng, household, 1, draw_age(rng), rng.choice((1, 2)), ethnicity,
        draw_religion(rng, ethnicity), draw_education(rng),
        choice(rng, (1, 4, 5, 6), (60, 10, 22, 8)), 1,
        foreign_born=rng.random() < 0.08,
    )


def generate_dataset(households, seed):
    rng = random.Random(seed)
    rows = []
    for index in range(1, households + 1):
        household = 20_000_000 + index
        if rng.random() < 0.55:
            rows.extend(couple_rows(rng, household))
        else:
            rows.append(single_row(rng, household))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--households", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=2001)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("synthetic_census_ew_2001.csv"),
    )
    args = parser.parse_args()
    if args.households < 1:
        parser.error("--households must be positive")

    rows = generate_dataset(args.households, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=INPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic 2001 records to {args.output}")


if __name__ == "__main__":
    main()
