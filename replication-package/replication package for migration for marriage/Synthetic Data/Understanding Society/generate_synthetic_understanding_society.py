"""Create a synthetic Understanding Society wave 1 ``indresp.dta``.

Only the variables used by ``Online Appendix\\Understanding Society`` are
generated (UKHLS main survey user guide, study 6614; wave-1 prefix ``a_``):

    a_hidp, a_pno, a_ppno, a_sex_dv, a_age_dv, a_birthy, a_yr2uk4,
    a_lcmary4, a_ukborn, a_mlstat, a_oprlg, a_oprlg1, a_racel, a_indinus_xw

Coding follows the conventions used by the analysis script: ``a_ukborn``
1-4 = UK nations, 5 = born outside the UK; ``a_yr2uk4`` and ``a_lcmary4`` are
calendar years with -8 for inapplicable; ``a_mlstat`` 2 = married, 10 = living
as a couple; ``a_oprlg`` 1/2 = has/does not have a religion and ``a_oprlg1``
the religion (12 = Muslim); ``a_racel`` follows the UKHLS ethnic-group list.
The data are random and only check that the pipeline runs.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "indresp.dta"

# Ethnic-group codes and the probability of being born in the UK.
GROUPS = {
    "white": ([1] * 30 + [2, 3, 4], 0.93),
    "indian": ([9], 0.65),
    "pakbang": ([10, 11], 0.6),
    "other": ([12, 13, 14, 15, 16, 17, 97], 0.5),
}
GROUP_WEIGHTS = {"white": 0.78, "indian": 0.06, "pakbang": 0.07, "other": 0.09}
COLUMNS = [
    "a_hidp", "a_pno", "a_ppno", "a_sex_dv", "a_age_dv", "a_birthy",
    "a_yr2uk4", "a_lcmary4", "a_ukborn", "a_mlstat", "a_oprlg",
    "a_oprlg1", "a_racel", "a_indinus_xw",
]


def draw_person(rng: np.random.Generator, group: str, sex: int) -> dict:
    racel_pool, uk_probability = GROUPS[group]
    uk_born = rng.random() < uk_probability
    age = int(rng.integers(22, 66))
    birthy = 2009 - age
    person = {
        "a_sex_dv": sex,
        "a_age_dv": age,
        "a_birthy": birthy,
        "a_racel": int(rng.choice(racel_pool)),
        "a_ukborn": int(rng.integers(1, 5)) if uk_born else 5,
        "a_yr2uk4": -8,
        "a_indinus_xw": round(float(rng.uniform(0.4, 2.0)), 4),
    }
    if not uk_born:
        person["a_yr2uk4"] = int(birthy + rng.integers(0, 40))
    muslim_probability = {"pakbang": 0.9, "other": 0.2}.get(group, 0.01)
    muslim = rng.random() < muslim_probability
    has_religion = muslim or rng.random() < 0.5
    person["a_oprlg"] = 1 if has_religion else 2
    if muslim:
        person["a_oprlg1"] = 12
    elif has_religion:
        person["a_oprlg1"] = int(rng.choice([2, 3, 6, 9, 10, 13]))
    else:
        person["a_oprlg1"] = -8
    return person


def build(n_couples: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    names = list(GROUP_WEIGHTS)
    probabilities = list(GROUP_WEIGHTS.values())
    rows = []
    for hidp in range(1, n_couples + 1):
        group = str(rng.choice(names, p=probabilities))
        endogamous = group == "white" or rng.random() < 0.9
        wife = draw_person(rng, group, 2)
        husband = draw_person(rng, group if endogamous else "white", 1)
        married = rng.random() < 0.88
        marriage_year = min(
            2009,
            int(max(wife["a_birthy"], husband["a_birthy"]) + rng.integers(20, 33)),
        )
        for person in (wife, husband):
            if person["a_yr2uk4"] > 0:
                if rng.random() < 0.55:
                    # Migrant spouse arriving after the wedding.
                    person["a_yr2uk4"] = min(
                        2009, marriage_year + int(rng.integers(0, 4))
                    )
                else:
                    person["a_yr2uk4"] = min(person["a_yr2uk4"], marriage_year)
        for pno, (person, partner_pno) in enumerate(((husband, 2), (wife, 1)), start=1):
            person.update(
                a_hidp=hidp,
                a_pno=pno,
                a_ppno=partner_pno,
                a_mlstat=2 if married else 10,
                a_lcmary4=marriage_year if married else -8,
            )
            rows.append(person)
    for hidp in range(n_couples + 1, n_couples + 1 + n_couples // 4):
        group = str(rng.choice(names, p=probabilities))
        person = draw_person(rng, group, int(rng.integers(1, 3)))
        person.update(a_hidp=hidp, a_pno=1, a_ppno=-8, a_mlstat=1, a_lcmary4=-8)
        rows.append(person)
    return pd.DataFrame(rows)[COLUMNS]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--couples", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=2009)
    args = parser.parse_args()
    data = build(args.couples, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_stata(args.output, write_index=False, version=118)
    print(f"Wrote {len(data):,} synthetic respondents to {args.output}")


if __name__ == "__main__":
    main()
