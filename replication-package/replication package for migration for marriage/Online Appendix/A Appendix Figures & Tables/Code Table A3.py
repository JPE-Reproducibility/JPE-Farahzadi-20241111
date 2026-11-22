
from __future__ import annotations

import argparse
from itertools import product
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Preparation" / "Model Engine"))
from matching_equilibrium import ipfp, read_matrix


SCENARIOS = (
    ("Original", "phi.dta", "phi"),
    ("No Ethnic Preferences", "phi_e.dta", "phi_e"),
    ("No Religious Preferences", "phi_r.dta", "phi_r"),
    ("No Ethnic or Religious Preferences", "phi_er.dta", "phi_er"),
)
RELIGIONS = ((0, "Non-Muslims"), (1, "Muslims"))
ETHNICITIES = (
    (0, "White British"),
    (1, "Other White"),
    (2, "Indian"),
    (3, "Pakistani/Bangladeshi"),
    (4, "Other"),
)


def share(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return float("nan")
    return numerator / denominator


def calculate_scenario(
    phi: np.ndarray,
    nx: np.ndarray,
    ny: np.ndarray,
    dxy: np.ndarray,
    dyx: np.ndarray,
    groups: list[int],
) -> dict[tuple[str, str, str], float]:
    matched, migrant_x, migrant_y, _, _ = ipfp(phi, nx, ny, dxy, dyx)

    # The source model orders cells by age, ethnicity, religion, education.
    cells = pd.DataFrame(
        product((1, 2, 3), (0, 1, 2, 3, 4), (0, 1), (0, 1)),
        columns=["age", "ethnicity", "religion", "education"],
    )
    cell_groups = (
        cells["age"] * 1000
        + cells["ethnicity"] * 100
        + cells["religion"] * 10
        + cells["education"]
    ).astype(int)
    if cell_groups.tolist() != groups:
        raise ValueError("The distribution file group order is not the model's 60-cell order.")

    ethnicity = cells["ethnicity"].to_numpy()
    religion = cells["religion"].to_numpy()
    result: dict[tuple[str, str, str], float] = {}

    for religion_id, religion_name in RELIGIONS:
        x_mask = (ethnicity != 0) & (religion == religion_id)
        y_mask = (ethnicity != 0) & (religion == religion_id)

        migration_x = share(
            migrant_x[x_mask, :].sum(),
            matched[x_mask, :].sum() + migrant_x[x_mask, :].sum(),
        )
        migration_y = share(
            migrant_y[:, y_mask].sum(),
            matched[:, y_mask].sum() + migrant_y[:, y_mask].sum(),
        )
        result[(religion_name, "Marriage Migration", "")] = (
            migration_x + migration_y
        ) / 2 * 100

        # Restrict inter-religious marriage shares to ethnic minorities, and
        # average female- and male-respondent rates equally.
        rel_diff = religion[:, np.newaxis] != religion[np.newaxis, :]
        interrelig_x = share(
            (matched[x_mask, :] * rel_diff[x_mask, :]).sum()
            + (migrant_x[x_mask, :] * rel_diff[x_mask, :]).sum(),
            matched[x_mask, :].sum() + migrant_x[x_mask, :].sum(),
        )
        interrelig_y = share(
            (matched[:, y_mask] * rel_diff[:, y_mask]).sum()
            + (migrant_y[:, y_mask] * rel_diff[:, y_mask]).sum(),
            matched[:, y_mask].sum() + migrant_y[:, y_mask].sum(),
        )
        result[(religion_name, "Inter-religious Marriage", "")] = (
            interrelig_x + interrelig_y
        ) / 2 * 100

        eth_diff = ethnicity[:, np.newaxis] != ethnicity[np.newaxis, :]
        for ethnicity_id, ethnicity_name in ETHNICITIES:
            x_ethnicity = (ethnicity == ethnicity_id) & (religion == religion_id)
            y_ethnicity = (ethnicity == ethnicity_id) & (religion == religion_id)
            intereth_x = share(
                (matched[x_ethnicity, :] * eth_diff[x_ethnicity, :]).sum()
                + (migrant_x[x_ethnicity, :] * eth_diff[x_ethnicity, :]).sum(),
                matched[x_ethnicity, :].sum() + migrant_x[x_ethnicity, :].sum(),
            )
            intereth_y = share(
                (matched[:, y_ethnicity] * eth_diff[:, y_ethnicity]).sum()
                + (migrant_y[:, y_ethnicity] * eth_diff[:, y_ethnicity]).sum(),
                matched[:, y_ethnicity].sum() + migrant_y[:, y_ethnicity].sum(),
            )
            result[(religion_name, "Inter-ethnic Marriage", ethnicity_name)] = (
                intereth_x + intereth_y
            ) / 2 * 100

    return result


def main() -> None:
    package_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=package_root / "Synthetic Data" / "model_out",
        help="Directory containing dist.dta, d.dta, and the four phi*.dta files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=package_root
        / "Online Appendix"
        / "Output"
        / "Table A3.csv",
        help="Output CSV path.",
    )
    args = parser.parse_args()

    distribution = pd.read_stata(args.input_dir / "dist.dta", columns=["group", "nx", "ny"])
    distribution = distribution.sort_values("group")
    groups = distribution["group"].astype(int).tolist()
    nx = distribution["nx"].to_numpy(dtype=float)
    ny = distribution["ny"].to_numpy(dtype=float)
    if len(groups) != 60 or not np.isfinite(nx).all() or not np.isfinite(ny).all():
        raise ValueError("dist.dta must contain 60 finite model groups.")

    dxy = read_matrix(args.input_dir / "d.dta", "D_women", groups)
    dyx = read_matrix(args.input_dir / "d.dta", "D_men", groups)

    scenario_values: dict[str, dict[tuple[str, str, str], float]] = {}
    for scenario, filename, variable in SCENARIOS:
        phi = read_matrix(args.input_dir / filename, variable, groups)
        scenario_values[scenario] = calculate_scenario(phi, nx, ny, dxy, dyx, groups)

    rows = []
    for religion_id, religion_name in RELIGIONS:
        for measure, ethnicity_name in (
            ("Marriage Migration", ""),
            ("Inter-religious Marriage", ""),
            *[("Inter-ethnic Marriage", label) for _, label in ETHNICITIES],
        ):
            key = (religion_name, measure, ethnicity_name)
            row = {
                "religion": religion_name,
                "measure": measure,
                "ethnicity": ethnicity_name,
            }
            row.update(
                {
                    scenario: scenario_values[scenario].get(key, float("nan"))
                    for scenario, _, _ in SCENARIOS
                }
            )
            rows.append(row)

    output = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False, float_format="%.10g")
    print(f"Appendix Table A3 data saved to: {args.output}")


if __name__ == "__main__":
    main()
