"""Compute the pooled Table A11 migration decomposition."""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd


HELPER = (
    Path(__file__).resolve().parents[1]
    / "J Measurement Error and Robustness of Definition"
    / "J2 Alternative Definitions of Marriage Migration"
    / "table_a7_migration.py"
)


def load_helper():
    spec = spec_from_file_location("table_a7_migration", HELPER)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load pooled decomposition helper from {HELPER}.")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marriage-dir", type=Path, required=True)
    parser.add_argument("--single-dir", type=Path, required=True)
    parser.add_argument(
        "--marriage-observed", type=float, nargs=2, required=True,
        metavar=("NON_MUSLIM", "MUSLIM"),
    )
    parser.add_argument(
        "--single-observed", type=float, nargs=2, required=True,
        metavar=("NON_MUSLIM", "MUSLIM"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if any(not 0 <= rate <= 100 for rate in args.marriage_observed + args.single_observed):
        parser.error("Observed migration percentages must be between 0 and 100.")
    helper = load_helper()
    figure4 = helper.load_figure4()
    labels = ("Non-Muslim", "Muslim")
    results = pd.concat(
        [
            helper.decompose_pooled(
                figure4, args.marriage_dir, "marriage",
                dict(zip(labels, args.marriage_observed)),
            ),
            helper.decompose_pooled(
                figure4, args.single_dir, "single",
                dict(zip(labels, args.single_observed)),
            ),
        ],
        ignore_index=True,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output, index=False)
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
