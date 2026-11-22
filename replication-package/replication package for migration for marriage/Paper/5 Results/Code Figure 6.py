"""Decompose reduced-form migration rates by religion using model rate ratios.

Observed rates are supplied for each religion. Average the women's and men's
baseline and counterfactual model rates before scaling each observed rate.
"""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RELIGIONS = ("Muslim", "Hindu", "Sikh", "Christian", "No Religion") 

# From data facts: tab sadult_immig if religion == <code> & ethnicityew != 1
# The percentages for sadult_immig == 1 are pooled across women and men.
# Religion codes: Muslim 6, Hindu 4, Sikh 7, Christian 2, No Religion 1.
OBSERVED_MIGRATION_PERCENT = {
    "Muslim": 52.44,
    "Hindu": 29.04,
    "Sikh": 25.5,
    "Christian": 17.2,
    "No Religion": 14.77,
}
GROUP_COUNT = 60


def _load_figure4():
    source = Path(__file__).with_name("Code Figure 4.py")
    spec = spec_from_file_location("figure4_equilibrium", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load the equilibrium solver from {source}.")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_square_matrix(
    frame, row_key, column_key, value_key, groups, name, require_complete=False
):
    if frame.duplicated([row_key, column_key]).any():
        raise ValueError(f"{name} contains duplicate group-pair keys.")
    matrix = frame.pivot(
        index=row_key, columns=column_key, values=value_key
    ).reindex(index=groups, columns=groups)
    if require_complete and matrix.isna().any().any():
        raise ValueError(f"{name} must contain a finite value for all 60-by-60 pairs.")
    values = matrix.fillna(0).to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"{name} contains non-finite values.")
    return values


def _read_model(model_dir):
    required_files = (
        "dist.dta",
        "phi.dta",
        "phi_er.dta",
        "d.dta",
    )
    paths = {name: model_dir / name for name in required_files}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing religion-specific model input(s): "
            + ", ".join(missing)
            + ". Run Code Figures 5.do or Code Table A4.do first."
        )

    distribution = pd.read_stata(paths["dist.dta"]).sort_values("group")
    groups = distribution["group"].to_numpy(dtype=int)
    if len(groups) != GROUP_COUNT or np.unique(groups).size != GROUP_COUNT:
        raise ValueError(f"{paths['dist.dta']} must contain 60 unique model types.")
    nx = distribution["nx"].to_numpy(dtype=float)
    ny = distribution["ny"].to_numpy(dtype=float)
    if (
        not np.isfinite(nx).all()
        or not np.isfinite(ny).all()
        or (nx < 0).any()
        or (ny < 0).any()
    ):
        raise ValueError(f"{paths['dist.dta']} has invalid population counts.")

    preferences = {}
    for name in ("phi", "phi_er"):
        frame = pd.read_stata(paths[f"{name}.dta"])
        if frame[["groupx", "groupy", name]].isna().any().any():
            raise ValueError(f"{paths[f'{name}.dta']} has missing model preferences.")
        preferences[name] = _read_square_matrix(
            frame, "groupx", "groupy", name, groups, str(paths[f"{name}.dta"]),
            require_complete=True,
        )

    outside_frame = pd.read_stata(paths["d.dta"])
    dxy = _read_square_matrix(
        outside_frame, "groupx", "groupy", "D_women", groups, "d.dta D_women"
    )
    dyx = _read_square_matrix(
        outside_frame, "groupx", "groupy", "D_men", groups, "d.dta D_men"
    )
    if (dxy < 0).any() or (dyx < 0).any():
        raise ValueError(f"{paths['d.dta']} contains negative outside-market terms.")

    return (
        groups,
        nx,
        ny,
        preferences["phi"],
        preferences["phi_er"],
        dxy,
        dyx,
    )


def _migration_rate(local, migrant, target_mask, sex, religion):
    if sex == "women":
        local_count = local[target_mask, :].sum()
        migrant_count = migrant[target_mask, :].sum()
    else:
        local_count = local[:, target_mask].sum()
        migrant_count = migrant[:, target_mask].sum()
    total = local_count + migrant_count
    if total <= 0:
        raise ValueError(
            f"No married {sex} are observed for ethnic-minority {religion} "
            "types; Figure 6 cannot be calculated for this subgroup."
        )
    return migrant_count / total


def decompose_religion(model_dir, religion, observed_rates, figure4):
    """Scale the supplied observed rate by the ratio of average model rates."""
    (
        groups,
        nx,
        ny,
        phi_original,
        phi_without_endogamy,
        dxy,
        dyx,
    ) = _read_model(model_dir)
    (
        baseline_local,
        baseline_migrant_women,
        baseline_migrant_men,
    ) = figure4.solve_equilibrium(phi_original, nx, ny, dxy, dyx)
    (
        counterfactual_local,
        counterfactual_migrant_women,
        counterfactual_migrant_men,
    ) = figure4.solve_equilibrium(phi_without_endogamy, nx, ny, dxy, dyx)

    ethnicity = (groups // 100) % 10
    target_religion = (groups // 10) % 10
    target_mask = (ethnicity != 0) & (target_religion == 1)
    if not target_mask.any():
        raise ValueError(f"No ethnic-minority target types in {model_dir}.")

    baseline_rates = {}
    counterfactual_rates = {}
    model_details = {}
    for sex, baseline_migrant, counterfactual_migrant in (
        ("women", baseline_migrant_women, counterfactual_migrant_women),
        ("men", baseline_migrant_men, counterfactual_migrant_men),
    ):
        baseline_rates[sex] = _migration_rate(
            baseline_local, baseline_migrant, target_mask, sex, religion
        )
        counterfactual_rates[sex] = _migration_rate(
            counterfactual_local,
            counterfactual_migrant,
            target_mask,
            sex,
            religion,
        )
        model_details[f"{sex}_baseline_model_migration_percent"] = 100 * baseline_rates[sex]
        model_details[f"{sex}_counterfactual_model_migration_percent"] = (
            100 * counterfactual_rates[sex]
        )

    observed_rate = observed_rates[religion]
    baseline_average = (baseline_rates["women"] + baseline_rates["men"]) / 2
    counterfactual_average = (
        counterfactual_rates["women"] + counterfactual_rates["men"]
    ) / 2
    outside_average, endogamy, ratio = figure4.scale_observed_rate(
        observed_rate, baseline_average, counterfactual_average, religion
    )
    return {
        "religion": religion,
        "observed_migration_percent": observed_rate,
        "outside_market_value_percent": outside_average,
        "endogamy_preferences_percent": endogamy,
        "average_baseline_model_migration_percent": 100 * baseline_average,
        "average_counterfactual_model_migration_percent": 100 * counterfactual_average,
        "average_counterfactual_to_baseline_ratio": ratio,
        **model_details,
    }


def create_figure(results, output_path):
    """Save the stacked Figure 6 bars and a CSV containing plotted values."""
    results = results.set_index("religion").reindex(RELIGIONS)
    if results.isna().any().any():
        raise ValueError("Figure 6 requires complete estimates for all five religions.")
    outside = results["outside_market_value_percent"].to_numpy(dtype=float)
    endogamy = results["endogamy_preferences_percent"].to_numpy(dtype=float)
    if not np.isfinite(np.column_stack((outside, endogamy))).all():
        raise ValueError("Figure 6 contains non-finite decomposition values.")

    positions = np.arange(len(RELIGIONS))
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.barh(
        positions,
        outside,
        color="#17365D",
        height=0.62,
        label="Outside market value",
    )
    ax.barh(
        positions,
        endogamy,
        left=outside,
        color="#8DB9E2",
        height=0.62,
        label="Endogamy preferences",
    )
    ax.set_yticks(positions, RELIGIONS)
    ax.invert_yaxis()
    ax.set_xlabel("Marriage Migration (%)")
    observed = outside + endogamy
    lower = min(0.0, float(outside.min()), float(observed.min()))
    upper = max(0.0, float(outside.max()), float(observed.max()))
    padding = max((upper - lower) * 0.05, 0.5)
    ax.set_xlim(lower - padding, upper + padding)
    ax.grid(axis="x", color="0.85", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2, frameon=False)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    results.reset_index().to_csv(output_path.with_suffix(".csv"), index=False)
    plt.close(fig)


def main():
    package_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-root",
        type=Path,
        default=package_root / "Synthetic Data" / "model_out",
        help="Directory with one By Religion.do output subfolder per religion.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=package_root
        / "Paper"
        / "Output"
        / "Figure 6.png",
        help="Figure path; a CSV with values is saved alongside it.",
    )
    args = parser.parse_args()

    figure4 = _load_figure4()
    rows = [
        decompose_religion(
            args.model_root / religion, religion, OBSERVED_MIGRATION_PERCENT, figure4
        )
        for religion in RELIGIONS
    ]
    results = pd.DataFrame(rows)
    create_figure(results, args.output)
    print(f"Figure 6 saved to {args.output}")
    print(f"Figure 6 data saved to {args.output.with_suffix('.csv')}")
    print(results[["religion", "outside_market_value_percent",
                   "endogamy_preferences_percent"]].to_string(index=False))


if __name__ == "__main__":
    main()
