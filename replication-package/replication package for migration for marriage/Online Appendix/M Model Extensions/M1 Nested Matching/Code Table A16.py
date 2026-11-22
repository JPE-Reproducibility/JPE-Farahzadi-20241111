"""Produce the spreadsheet-ready parameter estimates for Table A16."""

import argparse
import csv
import importlib.util
import math
from pathlib import Path


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Python module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _baseline_parameters(matches):
    log = math.log
    parameters = {
        "Phi_MM": log(matches["MM"] / matches["M0"]) + log(matches["MM"] / matches["0M"]),
        "Phi_MN": log(matches["MN"] / matches["M0"]) + log(matches["MN"] / matches["0N"]),
        "Phi_NM": log(matches["NM"] / matches["N0"]) + log(matches["NM"] / matches["0M"]),
        "Phi_NN": log(matches["NN"] / matches["N0"]) + log(matches["NN"] / matches["0N"]),
    }
    parameters["B_x"] = (
        log(matches["MM_x"] / matches["M0"])
        + log(matches["MM_x"])
        - parameters["Phi_MM"]
    )
    parameters["B_y"] = (
        log(matches["MM_y"])
        + log(matches["MM_y"] / matches["0M"])
        - parameters["Phi_MM"]
    )
    return parameters


def build_table():
    source = Path(__file__).with_name("estimation_nested.py")
    estimator = _load_module("a16_nested_estimator", source)
    baseline = _baseline_parameters(estimator.OBSERVED_MATCHES)
    nested = estimator.estimate_nested()
    parameter_order = (
        "Phi_MM", "Phi_MN", "Phi_NM", "Phi_NN", "B_x", "B_y", "rho", "delta"
    )
    return [
        {
            "Parameter": name,
            "Baseline": f"{baseline[name]:.2f}" if name in baseline else "",
            "Nested": f"{nested[name]:.2f}",
        }
        for name in parameter_order
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "Output",
        help="Directory for Table A16.csv (default: Online Appendix\\Output)",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "Table A16.csv"
    with output_path.open("w", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=("Parameter", "Baseline", "Nested"))
        writer.writeheader()
        writer.writerows(build_table())
    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
