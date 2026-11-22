"""Marriage-migration decomposition for Figure A17 using the Figure 4 implementation."""

import argparse
import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd

FIGURE4 = Path(__file__).resolve().parents[3] / "Paper" / "5 Results" / "Code Figure 4.py"


def load_figure4():
    cwd = os.getcwd()
    spec = spec_from_file_location("figure4_equilibrium", FIGURE4)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Figure 4 implementation from {FIGURE4}.")
    module = module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        os.chdir(cwd)
    return module


def decompose(figure4, model_dir, area, observed):
    groups, nx, ny, phi, phi_er, dxy, dyx = figure4.load_inputs(Path(model_dir))
    baseline = figure4.solve_equilibrium(phi, nx, ny, dxy, dyx)
    counterfactual = figure4.solve_equilibrium(phi_er, nx, ny, dxy, dyx)
    results = figure4.decompose_migration(groups, *baseline, *counterfactual)
    for (religion, sex), percent in observed.items():
        mask = (results["religion"] == religion) & (results["sex"] == sex)
        ratio = results.loc[mask, "counterfactual_to_baseline_ratio"]
        results.loc[mask, "observed_migration_percent"] = percent
        results.loc[mask, "outside_market_value_percent"] = percent * ratio
        results.loc[mask, "endogamy_preferences_percent"] = percent * (1 - ratio)
    rates = results.groupby("religion", sort=False)[
        [
            "observed_migration_percent",
            "outside_market_value_percent",
            "endogamy_preferences_percent",
        ]
    ].mean()
    rates = rates.rename(
        columns={
            "observed_migration_percent": "overall",
            "outside_market_value_percent": "outside_market_value",
            "endogamy_preferences_percent": "endogamy_preferences",
        }
    ).reset_index()
    rates.insert(0, "area", area)
    return rates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--high-dir", type=Path, required=True)
    parser.add_argument("--low-dir", type=Path, required=True)
    parser.add_argument(
        "--observed",
        type=Path,
        required=True,
        help="CSV with area, religion, sex, observed_percent.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    observed = pd.read_csv(args.observed)
    expected = {
        (area, religion, sex)
        for area in ("high", "low")
        for religion in ("Muslim", "Non-Muslim")
        for sex in ("Men", "Women")
    }
    columns = ["area", "religion", "sex"]
    if not set(columns + ["observed_percent"]).issubset(observed.columns):
        raise ValueError("Observed CSV must contain area, religion, sex, and observed_percent.")
    if (
        observed.duplicated(columns).any()
        or set(map(tuple, observed[columns].to_numpy())) != expected
    ):
        raise ValueError("Observed CSV must contain exactly one row for each area, religion, and sex.")
    observed["observed_percent"] = pd.to_numeric(observed["observed_percent"], errors="raise")
    if (
        not np.isfinite(observed["observed_percent"]).all()
        or not observed["observed_percent"].between(0, 100).all()
    ):
        raise ValueError("Observed migration percentages must be finite values between 0 and 100.")
    figure4 = load_figure4()

    def rates_for(area):
        part = observed[observed["area"] == area]
        return {
            (r.religion, r.sex): r.observed_percent for r in part.itertuples()
        }

    results = pd.concat(
        [
            decompose(figure4, args.high_dir, "high", rates_for("high")),
            decompose(figure4, args.low_dir, "low", rates_for("low")),
        ],
        ignore_index=True,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output, index=False)
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
