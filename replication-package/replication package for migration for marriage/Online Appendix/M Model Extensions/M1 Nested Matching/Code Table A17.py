"""Produce the spreadsheet-ready counterfactual rates for Table A17."""

import argparse
import csv
import importlib.util
from pathlib import Path


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Python module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rates(matches):
    women_total = matches["MM"] + matches["MN"] + matches["MM_x"]
    men_total = matches["MM"] + matches["NM"] + matches["MM_y"]
    return {
        ("Intermarriage rate", "Women"): 100 * matches["MN"] / women_total,
        ("Intermarriage rate", "Men"): 100 * matches["NM"] / men_total,
        ("Marriage migration rate", "Women"): 100 * matches["MM_x"] / women_total,
        ("Marriage migration rate", "Men"): 100 * matches["MM_y"] / men_total,
    }


def build_table():
    folder = Path(__file__).parent
    baseline_solver = _load_module(
        "a17_baseline_solver", folder / "counterfactual_baseline.py"
    )
    nested_solver = _load_module(
        "a17_nested_solver", folder / "counterfactual_nested.py"
    )
    estimator = _load_module(
        "a16_observed_counts",
        folder / "estimation_nested.py",
    )
    original = _rates(estimator.OBSERVED_MATCHES)
    baseline = _rates(baseline_solver.solve_counterfactual())
    nested = _rates(nested_solver.solve_counterfactual())

    rows = []
    for outcome, group in (
        ("Intermarriage rate", "Women"),
        ("Intermarriage rate", "Men"),
        ("Marriage migration rate", "Women"),
        ("Marriage migration rate", "Men"),
    ):
        rows.append(
            {
                "Outcome": outcome,
                "Group": group,
                "Original": f"{original[(outcome, group)]:.1f}",
                "Baseline": f"{baseline[(outcome, group)]:.1f}",
                "Nested": f"{nested[(outcome, group)]:.1f}",
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "Output",
        help="Directory for Table A17.csv (default: Online Appendix\\Output)",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "Table A17.csv"
    with output_path.open("w", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=("Outcome", "Group", "Original", "Baseline", "Nested"),
        )
        writer.writeheader()
        writer.writerows(build_table())
    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
