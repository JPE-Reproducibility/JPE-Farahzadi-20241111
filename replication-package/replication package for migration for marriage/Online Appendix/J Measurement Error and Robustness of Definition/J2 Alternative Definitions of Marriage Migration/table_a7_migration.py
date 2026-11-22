"""Marriage-migration decomposition for Table A7, using the Figure 4 code.

For Table A7, average the women's and men's model rates before scaling each
specification's pooled observed rate. A sex-specific mode is retained for
other tables that use this helper.
"""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd

FIGURE4 = Path(__file__).resolve().parents[3] / "Paper" / "5 Results" / "Code Figure 4.py"


def load_figure4():
    source = FIGURE4.resolve()
    spec = spec_from_file_location("figure4_equilibrium", source)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decompose_by_sex(figure4, model_dir, specification, observed_rates):
    groups, nx, ny, phi, phi_er, dxy, dyx = figure4.load_inputs(Path(model_dir))
    baseline = figure4.solve_equilibrium(phi, nx, ny, dxy, dyx)
    counterfactual = figure4.solve_equilibrium(phi_er, nx, ny, dxy, dyx)
    results = figure4.decompose_migration(
        groups, *baseline, *counterfactual
    )
    for (religion, sex), observed in observed_rates.items():
        mask = (results["religion"] == religion) & (results["sex"] == sex)
        if mask.sum() != 1:
            raise ValueError(f"Expected one Figure 4 result for {religion} {sex}.")
        ratio = results.loc[mask, "counterfactual_to_baseline_ratio"]
        results.loc[mask, "observed_migration_percent"] = observed
        results.loc[mask, "outside_market_value_percent"] = observed * ratio
        results.loc[mask, "endogamy_preferences_percent"] = observed * (1 - ratio)
    average = results.groupby("religion", sort=False)[
        [
            "observed_migration_percent",
            "outside_market_value_percent",
            "endogamy_preferences_percent",
        ]
    ].mean()
    average = average.rename(
        columns={
            "observed_migration_percent": "overall",
            "outside_market_value_percent": "outside_market_value",
            "endogamy_preferences_percent": "endogamy_preferences",
        }
    ).reset_index()
    average.insert(0, "specification", specification)
    return average


def decompose_pooled(figure4, model_dir, specification, observed_rates):
    groups, nx, ny, phi, phi_er, dxy, dyx = figure4.load_inputs(Path(model_dir))
    baseline = figure4.solve_equilibrium(phi, nx, ny, dxy, dyx)
    counterfactual = figure4.solve_equilibrium(phi_er, nx, ny, dxy, dyx)
    ethnic = (groups // 100) % 10
    religion = (groups // 10) % 10
    rows = []
    for code, label in ((0, "Non-Muslim"), (1, "Muslim")):
        mask = (ethnic != 0) & (religion == code)
        original_rates = [
            figure4._migration_rate(baseline[0], baseline[1], mask, "women"),
            figure4._migration_rate(baseline[0], baseline[2], mask, "men"),
        ]
        restricted_rates = [
            figure4._migration_rate(counterfactual[0], counterfactual[1], mask, "women"),
            figure4._migration_rate(counterfactual[0], counterfactual[2], mask, "men"),
        ]
        observed = observed_rates[label]
        outside, endogamy, _ = figure4.scale_observed_rate(
            observed, sum(original_rates) / 2, sum(restricted_rates) / 2, label
        )
        rows.append({
            "specification": specification,
            "religion": label,
            "overall": observed,
            "outside_market_value": outside,
            "endogamy_preferences": endogamy,
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", required=True)
    parser.add_argument("--sensitivity-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--baseline-observed", type=float, nargs=2,
        metavar=("NON_MUSLIM", "MUSLIM"),
        help="Pooled baseline percentages; selects pooled A7 calculation.",
    )
    parser.add_argument(
        "--sensitivity-observed", type=float, nargs="+", required=True,
        metavar="PERCENT",
        help="Pooled non-Muslim and Muslim percentages for A7, or four sex-specific percentages for other tables.",
    )
    args = parser.parse_args()

    all_rates = args.sensitivity_observed + (args.baseline_observed or [])
    if any(not 0 <= rate <= 100 for rate in all_rates):
        parser.error("Observed migration percentages must be between 0 and 100.")
    figure4 = load_figure4()
    if args.baseline_observed is not None:
        if len(args.sensitivity_observed) != 2:
            parser.error("Pooled mode requires two sensitivity percentages: non-Muslim, Muslim.")
        labels = ["Non-Muslim", "Muslim"]
        baseline_rates = dict(zip(labels, args.baseline_observed))
        sensitivity_rates = dict(zip(labels, args.sensitivity_observed))
        decompose = decompose_pooled
    else:
        if len(args.sensitivity_observed) != 4:
            parser.error("Sex-specific mode requires four sensitivity percentages: non-Muslim men, non-Muslim women, Muslim men, Muslim women.")
        labels = [
            ("Non-Muslim", "Men"), ("Non-Muslim", "Women"),
            ("Muslim", "Men"), ("Muslim", "Women"),
        ]
        baseline_rates = figure4.OBSERVED_MIGRATION_PERCENT
        sensitivity_rates = dict(zip(labels, args.sensitivity_observed))
        decompose = decompose_by_sex
    rates = pd.concat(
        [
            decompose(figure4, args.baseline_dir, "baseline", baseline_rates),
            decompose(figure4, args.sensitivity_dir, "sensitivity", sensitivity_rates),
        ],
        ignore_index=True,
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    rates.to_csv(args.output, index=False)
    print(rates.to_string(index=False))


if __name__ == "__main__":
    main()
