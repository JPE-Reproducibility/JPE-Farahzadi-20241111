"""Generate a deterministic, wholly artificial Census-shaped test dataset."""

import argparse
import csv
import random
from pathlib import Path


REGIONS = tuple(range(1, 11))
REGION_WEIGHTS = (4.6, 12.6, 9.4, 8.0, 10.0, 10.5, 14.7, 15.3, 9.5, 5.5)
LOCAL_AUTHORITIES = (
    "E06000001",
    "E06000002",
    "E06000003",
    "E06000004",
    "E06000005",
    "E06000006",
    "E06000007",
    "E06000008",
    "E06000009",
    "E06000010",
)
HIGH_MUSLIM_SHARE_AUTHORITIES = frozenset(LOCAL_AUTHORITIES[:2])
ETHNICITY_CODES = tuple(range(1, 19))
ETHNICITY_WEIGHTS = (
    80.4, 0.9, 0.1, 4.5, 0.8, 0.3, 0.6, 0.5, 2.5,
    2.0, 0.8, 0.7, 1.5, 1.8, 1.1, 0.5, 0.4, 0.6,
)
RELIGION_CODES = tuple(range(1, 10))
RELIGION_WEIGHTS = (25.1, 59.3, 0.4, 1.5, 0.5, 4.9, 0.8, 0.4, 7.1)
# Synthetic high-share authorities use a larger Muslim population so Figure
# A17 has observations on both sides of its 10% local-authority cutoff.
HIGH_SHARE_RELIGION_WEIGHTS = (20.0, 33.0, 0.4, 1.5, 0.5, 37.0, 0.8, 0.4, 6.4)
# Religion weights (codes 1-9) for South Asian ethnic groups, so that minority
# Hindu, Sikh and Muslim couples exist in sufficient numbers.
RELIGION_WEIGHTS_BY_ETHNICITY = {
    9: (3, 5, 0.5, 45, 0, 15, 27, 0.5, 4),  # Indian
    10: (1, 2, 0, 0, 0, 92, 0.5, 0, 4.5),  # Pakistani
    11: (1, 2, 0, 0, 0, 92, 0, 0, 5),  # Bangladeshi
}
HEALTH_CODES = (1, 2, 3, 4, 5)
HEALTH_WEIGHTS = (47.4, 34.2, 13.0, 4.2, 1.2)
LANGUAGE_CODES = (1, 2, 3, 4)
LANGUAGE_WEIGHTS = (39.9, 36.8, 17.9, 5.4)
ACTIVITY_CODES = (1, 2, 3, 4, 5, 6, 7)
ACTIVITY_WEIGHTS = (59.4, 4.7, 4.9, 21.1, 3.8, 4.0, 2.1)
EDUCATION_CODES = (2, 3, 4, 5, 6)
EDUCATION_WEIGHTS = (36.8, 33.4, 0.1, 29.2, 0.5)
MARITAL_CODES = tuple(range(1, 10))
MARITAL_WEIGHTS = (47.3, 37.8, 2.1, 7.2, 5.2, 0.2, 0.05, 0.05, 0.1)
OCCUPATION_CODES = (1111, 1112, 1113, 1114, 1120, 1211, 1212)
UK_COUNTRY_CODES = (921, 922, 923, 924, 925, 926)
ORIGIN_CODES_BY_ETHNICITY = {
    9: 356,  # India
    10: 586,  # Pakistan
    11: 50,  # Bangladesh
    12: 156,  # China
    17: 12,  # Algeria
}
INPUT_COLUMNS = (
    "HHID",
    "PERSID",
    "AGEC",
    "SEX",
    "ETHNICITYEW",
    "ETHNIC_INDEX",
    "COB",
    "YRARR_YEAR",
    "MARSTAT",
    "ISCED",
    "ACTLWO",
    "RELIGIONEW",
    "HEALTH",
    "REGION",
    "LANGPRF",
    "HSPOUSE",
    "HPARTNER",
    *(f"REL{i}" for i in range(1, 16)),
    "IDENTITY",
    "ISCO",
    *(f"QUALS{i:02}" for i in range(1, 15)),
    "LA",
    "MOVEREGION",
)


def weighted_choice(rng, values, weights):
    return rng.choices(values, weights=weights, k=1)[0]


def draw_age(rng, child=False):
    if child:
        return rng.randint(0, 19)
    ages = tuple(range(18, 61))
    weights = tuple(max(1, 18 - abs(age - 34)) for age in ages)
    return weighted_choice(rng, ages, weights)


def draw_religion(rng, ethnicity, local_authority):
    weights = RELIGION_WEIGHTS_BY_ETHNICITY.get(ethnicity, RELIGION_WEIGHTS)
    if (
        ethnicity not in RELIGION_WEIGHTS_BY_ETHNICITY
        and local_authority in HIGH_MUSLIM_SHARE_AUTHORITIES
    ):
        weights = HIGH_SHARE_RELIGION_WEIGHTS
    return weighted_choice(rng, RELIGION_CODES, weights)


def draw_origin(rng, ethnicity):
    if rng.random() < 0.84:
        return weighted_choice(rng, UK_COUNTRY_CODES, (72, 3, 5, 6, 3, 11))
    return ORIGIN_CODES_BY_ETHNICITY.get(
        ethnicity,
        rng.choice((4, 50, 124, 156, 250, 276, 356, 586, 826, 840)),
    )


def make_person(rng, household_id, person_id, region, local_authority, age=None,
                sex=None, ethnicity=None, religion=None, married=False,
                spouse_person_id=None, family_group=None):
    age = draw_age(rng) if age is None else age
    sex = rng.choice((1, 2)) if sex is None else sex
    ethnicity = (
        weighted_choice(rng, ETHNICITY_CODES, ETHNICITY_WEIGHTS)
        if ethnicity is None
        else ethnicity
    )
    religion = (
        draw_religion(rng, ethnicity, local_authority)
        if religion is None
        else religion
    )

    immigrant = rng.random() < 0.16
    if immigrant:
        country_of_birth = draw_origin(rng, ethnicity)
        age_at_arrival = rng.randint(18, age) if age >= 18 and rng.random() < 0.65 else rng.randint(0, max(0, age - 1))
        arrival_year = 2011 - (age - age_at_arrival)
    else:
        country_of_birth = weighted_choice(rng, UK_COUNTRY_CODES, (72, 3, 5, 6, 3, 11))
        arrival_year = -9

    row = {
        "HHID": household_id,
        "PERSID": person_id,
        "AGEC": age,
        "SEX": sex,
        "ETHNICITYEW": ethnicity,
        "ETHNIC_INDEX": rng.randint(1, 28),
        "COB": country_of_birth,
        "YRARR_YEAR": arrival_year,
        "MARSTAT": 2 if married else weighted_choice(rng, MARITAL_CODES, MARITAL_WEIGHTS),
        "ISCED": weighted_choice(rng, EDUCATION_CODES, EDUCATION_WEIGHTS) if age >= 16 else -9,
        "ACTLWO": weighted_choice(rng, ACTIVITY_CODES, ACTIVITY_WEIGHTS) if age >= 16 else -9,
        "RELIGIONEW": religion,
        "HEALTH": weighted_choice(rng, HEALTH_CODES, HEALTH_WEIGHTS),
        "REGION": region,
        "LANGPRF": weighted_choice(rng, LANGUAGE_CODES, LANGUAGE_WEIGHTS),
        "HSPOUSE": 2 if spouse_person_id is not None else 1,
        "HPARTNER": 1,
        "IDENTITY": rng.randint(1, 53),
        "ISCO": rng.choice(OCCUPATION_CODES) if age >= 16 else -9,
        "LA": local_authority,
        "MOVEREGION": 1 if immigrant else -9,
    }
    for index in range(1, 16):
        row[f"REL{index}"] = int(index == spouse_person_id)
    for index in range(1, 15):
        row[f"QUALS{index:02}"] = (
            rng.choices((1, 2), weights=(66.2, 33.8), k=1)[0]
            if age >= 16
            else -9
        )

    if family_group is not None:
        row["ETHNIC_INDEX"] = family_group["ethnic_index"]
    return row


def generate_household(rng, household_id):
    region = weighted_choice(rng, REGIONS, REGION_WEIGHTS)
    local_authority = rng.choice(LOCAL_AUTHORITIES)
    has_couple = rng.random() < 0.62
    rows = []

    if has_couple:
        husband_id, wife_id = 1, 2
        husband_age = draw_age(rng)
        wife_age = min(60, max(18, husband_age + rng.randint(-6, 6)))
        ethnicity = weighted_choice(rng, ETHNICITY_CODES, ETHNICITY_WEIGHTS)
        religion = draw_religion(rng, ethnicity, local_authority)
        ethnic_index = rng.randint(1, 28)
        family_group = {"ethnic_index": ethnic_index}
        spouse_ethnicity = ethnicity if rng.random() < 0.88 else None
        spouse_religion = religion if rng.random() < 0.9 else None

        rows.extend(
            [
                make_person(
                    rng, household_id, husband_id, region, local_authority,
                    husband_age, 1, ethnicity, religion, True, wife_id, family_group,
                ),
                make_person(
                    rng, household_id, wife_id, region, local_authority,
                    wife_age, 2, spouse_ethnicity, spouse_religion, True,
                    husband_id, family_group,
                ),
            ]
        )

        for person_id in range(3, 3 + rng.choices((0, 1, 2, 3), (35, 30, 25, 10), k=1)[0]):
            child_age = rng.randint(0, max(1, min(19, husband_age - 18)))
            child_ethnicity = ethnicity if rng.random() < 0.9 else None
            rows.append(
                make_person(
                    rng, household_id, person_id, region, local_authority,
                    age=child_age, ethnicity=child_ethnicity,
                    religion=religion if rng.random() < 0.9 else None,
                    family_group=family_group,
                )
            )
    else:
        member_count = rng.choices((1, 2, 3, 4), (45, 35, 15, 5), k=1)[0]
        for person_id in range(1, member_count + 1):
            rows.append(make_person(rng, household_id, person_id, region, local_authority))

    return rows


def make_cohabiting(rows, share, seed):
    """Turn a share of married couples into cohabiting (never-married) couples.

    Uses its own random stream so the underlying synthetic population is the
    same as when the share is zero.
    """
    if share <= 0:
        return rows
    rng = random.Random(seed + 1)
    by_household = {}
    for row in rows:
        by_household.setdefault(row["HHID"], {})[row["PERSID"]] = row
    for household in by_household.values():
        couple = [row for row in household.values() if row["HSPOUSE"] == 2]
        if len(couple) != 2 or rng.random() >= share:
            continue
        for row in couple:
            row["MARSTAT"] = 1
            row["HSPOUSE"] = 1
            row["HPARTNER"] = 2
            for index in range(1, 16):
                if row[f"REL{index}"] == 1:
                    row[f"REL{index}"] = 3
    return rows


def generate_dataset(households, seed, cohabiting_share=0.15):
    rng = random.Random(seed)
    rows = []
    for household_id in range(1, households + 1):
        rows.extend(generate_household(rng, 10_000_000 + household_id))
    return make_cohabiting(rows, cohabiting_share, seed)


def validate_rows(rows):
    by_household = {}
    for row in rows:
        by_household.setdefault(row["HHID"], {})[row["PERSID"]] = row
    for household in by_household.values():
        for row in household.values():
            if row["HSPOUSE"] != 2:
                continue
            spouse_ids = [
                index for index in range(1, 16)
                if row[f"REL{index}"] == 1
            ]
            if len(spouse_ids) != 1 or spouse_ids[0] not in household:
                raise ValueError("A synthetic spouse link is not reciprocal.")
            spouse = household[spouse_ids[0]]
            if spouse["HSPOUSE"] != 2 or spouse[f"REL{row['PERSID']}"] != 1:
                raise ValueError("A synthetic spouse link is not reciprocal.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--households", type=int, default=300000)
    parser.add_argument("--seed", type=int, default=2011)
    parser.add_argument(
        "--cohabiting-share",
        type=float,
        default=0.15,
        help="Share of couples generated as cohabiting rather than married.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("synthetic_census_ew_2011.csv"),
    )
    args = parser.parse_args()
    if args.households < 1:
        parser.error("--households must be positive")

    rows = generate_dataset(args.households, args.seed, args.cohabiting_share)
    validate_rows(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=INPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"Wrote {len(rows):,} synthetic people in {args.households:,} "
        f"households to {args.output}"
    )


if __name__ == "__main__":
    main()
