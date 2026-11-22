"""Decompose observed marriage migration using original and restricted preferences.

For each sex and religion, the outside-market component is the observed rate
multiplied by the restricted-model rate divided by the original-model rate.
The endogamy component is the remainder. Both models use the same populations
and outside-market terms.
"""

import argparse
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

GROUP_COUNT = 60
TOLERANCE = 1e-9
MAX_ITERATIONS = 2_000

# Reduced-form observed rates from:
# collapse (mean) sadult_immig if ethnicityew != 1, by(muslim sex)
# In the reduced-form data, muslim is 0/1 and sex is 1 (men)/2 (women).
OBSERVED_MIGRATION_PERCENT = {
    ("Non-Muslim", "Men"): 22.80,
    ("Non-Muslim", "Women"): 19.46,
    ("Muslim", "Men"): 51.16,
    ("Muslim", "Women"): 53.68,
}


def _read_pair_matrix(frame, row_column, column_column, value_column, groups):
    matrix = frame.pivot(
        index=row_column, columns=column_column, values=value_column
    ).reindex(index=groups, columns=groups, fill_value=0)
    values = matrix.fillna(0).to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"{value_column} contains non-finite values.")
    return values


def _read_preference_matrix(path, value_column, groups):
    frame = pd.read_stata(path)
    matrix = frame.pivot(
        index="groupx", columns="groupy", values=value_column
    ).reindex(index=groups, columns=groups)
    if matrix.isna().any().any():
        raise ValueError(
            f"{path.name} must contain one value for every model group pair."
        )
    values = matrix.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"{value_column} contains non-finite values.")
    return values


def load_inputs(input_dir):
    """Read population counts, original and restricted preferences, and outside terms."""
    required = ("dist.dta", "phi.dta", "phi_er.dta", "d.dta")
    paths = {name: input_dir / name for name in required}
    missing = [path for path in paths.values() if not path.is_file()]
    if missing:
        missing_paths = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(
            f"Required input file(s) not found: {missing_paths}. "
            "Run Code Table 4.do first."
        )

    distribution = pd.read_stata(paths["dist.dta"]).sort_values("group")
    groups = distribution["group"].astype(int).to_numpy()
    if len(groups) != GROUP_COUNT or len(np.unique(groups)) != GROUP_COUNT:
        raise ValueError(
            f"dist.dta must contain exactly {GROUP_COUNT} unique groups."
        )
    nx = distribution["nx"].to_numpy(dtype=float)
    ny = distribution["ny"].to_numpy(dtype=float)
    if (
        not np.isfinite(nx).all()
        or not np.isfinite(ny).all()
        or (nx < 0).any()
        or (ny < 0).any()
    ):
        raise ValueError("Population counts must be finite and non-negative.")

    phi_original = _read_preference_matrix(paths["phi.dta"], "phi", groups)
    phi_no_ethnicity_religion = _read_preference_matrix(
        paths["phi_er.dta"], "phi_er", groups
    )
    outside = pd.read_stata(paths["d.dta"])
    dxy = _read_pair_matrix(outside, "groupx", "groupy", "D_women", groups)
    dyx = _read_pair_matrix(outside, "groupx", "groupy", "D_men", groups)
    if (dxy < 0).any() or (dyx < 0).any():
        raise ValueError("Outside-market terms must be non-negative.")

    return (
        groups,
        nx,
        ny,
        phi_original,
        phi_no_ethnicity_religion,
        dxy,
        dyx,
    )


def solve_equilibrium(phi, nx, ny, dxy, dyx):
    """Solve the matching equilibrium for the specified preferences."""
    exp_phi = np.exp(phi / 2)
    if not np.isfinite(exp_phi).all():
        raise ValueError("Preference values overflowed while exponentiating.")

    scale = np.sqrt(1 / (len(nx) + len(ny) + 2 * exp_phi.sum()))
    tx = np.full(len(nx), scale)
    ty = np.full(len(ny), scale)

    for _ in range(MAX_ITERATIONS):
        sx = np.sum(exp_phi * (ty[np.newaxis, :] + dxy), axis=1)
        root_x = np.sqrt(sx**2 + 4 * nx)
        next_tx = np.divide(
            2 * nx,
            root_x + sx,
            out=np.zeros_like(nx),
            where=(root_x + sx) != 0,
        )

        sy = np.sum(exp_phi * (next_tx[:, np.newaxis] + dyx), axis=0)
        root_y = np.sqrt(sy**2 + 4 * ny)
        next_ty = np.divide(
            2 * ny,
            root_y + sy,
            out=np.zeros_like(ny),
            where=(root_y + sy) != 0,
        )

        difference = np.max(np.abs(next_tx - tx)) + np.max(np.abs(next_ty - ty))
        tx, ty = next_tx, next_ty
        if difference <= TOLERANCE * scale:
            break
    else:
        raise RuntimeError(
            f"Equilibrium solver did not converge in {MAX_ITERATIONS} iterations."
        )

    local = exp_phi * tx[:, np.newaxis] * ty[np.newaxis, :]
    migrant_women = np.divide(
        local * dxy,
        ty[np.newaxis, :],
        out=np.zeros_like(local),
        where=ty[np.newaxis, :] != 0,
    )
    migrant_men = np.divide(
        local * dyx,
        tx[:, np.newaxis],
        out=np.zeros_like(local),
        where=tx[:, np.newaxis] != 0,
    )
    return local, migrant_women, migrant_men


def _migration_rate(local, migrant, mask, sex):
    if sex == "women":
        local_count = local[mask, :].sum()
        migrant_count = migrant[mask, :].sum()
    else:
        local_count = local[:, mask].sum()
        migrant_count = migrant[:, mask].sum()
    denominator = local_count + migrant_count
    if denominator == 0:
        raise ValueError(
            f"No married {sex} are observed in the requested religion/ethnicity group."
        )
    return migrant_count / denominator


def scale_observed_rate(observed_percent, baseline_rate, counterfactual_rate, group):
    """Scale an observed percentage by the restricted-to-original model rate."""
    if baseline_rate == 0:
        raise ValueError(
            f"Original-model migration rate is zero for {group}; "
            "the counterfactual ratio is undefined."
        )
    ratio = counterfactual_rate / baseline_rate
    outside_percent = observed_percent * ratio
    return outside_percent, observed_percent - outside_percent, ratio


def decompose_migration(
    groups,
    baseline_local,
    baseline_migrant_women,
    baseline_migrant_men,
    counterfactual_local,
    counterfactual_migrant_women,
    counterfactual_migrant_men,
):
    """Scale observed rates by counterfactual-to-baseline model rate ratios."""
    ethnic = (groups // 100) % 10
    religion = (groups // 10) % 10
    rows = []
    for religion_code, religion_label in ((0, "Non-Muslim"), (1, "Muslim")):
        group_mask = (ethnic != 0) & (religion == religion_code)
        for sex, label, baseline_migrant, counterfactual_migrant in (
            (
                "women",
                "Women",
                baseline_migrant_women,
                counterfactual_migrant_women,
            ),
            (
                "men",
                "Men",
                baseline_migrant_men,
                counterfactual_migrant_men,
            ),
        ):
            observed_percent = OBSERVED_MIGRATION_PERCENT[(religion_label, label)]
            baseline_rate = _migration_rate(
                baseline_local, baseline_migrant, group_mask, sex
            )
            counterfactual_rate = _migration_rate(
                counterfactual_local,
                counterfactual_migrant,
                group_mask,
                sex,
            )
            outside_percent, endogamy_percent, ratio = scale_observed_rate(
                observed_percent, baseline_rate, counterfactual_rate,
                f"{religion_label} {label}",
            )
            rows.append(
                {
                    "religion": religion_label,
                    "sex": label,
                    "observed_migration_percent": observed_percent,
                    "outside_market_value_percent": outside_percent,
                    "endogamy_preferences_percent": endogamy_percent,
                    "baseline_model_migration_percent": 100 * baseline_rate,
                    "counterfactual_model_migration_percent": 100 * counterfactual_rate,
                    "counterfactual_to_baseline_ratio": ratio,
                }
            )
    return pd.DataFrame(rows)


def create_figure(results, output_path):
    """Create the stacked horizontal-bar figure and export its plotted values."""
    fig, ax = plt.subplots(figsize=(8, 4.6))
    rows = [
        ("Non-Muslim", "Men"),
        ("Non-Muslim", "Women"),
        ("Muslim", "Men"),
        ("Muslim", "Women"),
    ]
    plotted = results.set_index(["religion", "sex"]).loc[rows]
    y_positions = np.arange(len(rows))
    outside = plotted["outside_market_value_percent"].to_numpy()
    endogamy = plotted["endogamy_preferences_percent"].to_numpy()

    ax.barh(
        y_positions,
        outside,
        color="#17365D",
        label="Outside market value",
        height=0.56,
    )
    ax.barh(
        y_positions,
        endogamy,
        left=outside,
        color="#8DB9E2",
        label="Endogamy preferences",
        height=0.56,
    )

    for y, value in zip(y_positions, outside):
        if value >= 0:
            ax.text(
                value / 2,
                y,
                f"{value:.0f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=9,
            )
    for y, start, value in zip(y_positions, outside, endogamy):
        if value >= 0:
            ax.text(
                start + value / 2,
                y,
                f"{value:.0f}%",
                ha="center",
                va="center",
                color="#17365D",
                fontsize=9,
            )
        else:
            ax.text(
                start + value / 2,
                y,
                f"{value:.0f}%",
                ha="center",
                va="center",
                color="#17365D",
                fontsize=9,
            )

    ax.set_yticks(y_positions, [f"{religion} {sex}" for religion, sex in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Marriage Migration (%)")
    ax.set_xlim(left=0)
    ax.grid(axis="x", color="0.85", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2, frameon=False)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    results.to_csv(output_path.with_suffix(".csv"), index=False)
    plt.close(fig)


def main():
    os.chdir(Path(__file__).resolve().parents[2])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(r"Synthetic Data\model_out"),
        help=(
            "Directory containing outputs from Code Table 4.do "
            "(dist, phi, phi_er, and d)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "Paper"
        / "Output"
        / "Figure 4.png",
        help="Figure output path; a CSV of plotted values is saved alongside it.",
    )
    args = parser.parse_args()

    (
        groups,
        nx,
        ny,
        phi_original,
        phi_no_endogamy,
        dxy,
        dyx,
    ) = load_inputs(args.input_dir)
    baseline = solve_equilibrium(phi_original, nx, ny, dxy, dyx)
    counterfactual_local, counterfactual_migrant_women, counterfactual_migrant_men = (
        solve_equilibrium(phi_no_endogamy, nx, ny, dxy, dyx)
    )
    results = decompose_migration(
        groups,
        *baseline,
        counterfactual_local,
        counterfactual_migrant_women,
        counterfactual_migrant_men,
    )
    create_figure(results, args.output)
    print(f"Figure 4 saved to {args.output}")
    print(f"Figure 4 data saved to {args.output.with_suffix('.csv')}")


if __name__ == "__main__":
    main()
