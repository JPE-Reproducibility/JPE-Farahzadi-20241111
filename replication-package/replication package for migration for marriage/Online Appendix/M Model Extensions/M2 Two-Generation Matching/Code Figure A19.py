"""Reproduce Figure A19: sensitivity to outside market values."""

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

from two_generation_model import load_params, outside_market_sensitivity


def _write_csv(path, rows):
    fields = (
        "outside_market_value_percent",
        "intermarriage_generation_1",
        "intermarriage_generation_2",
        "marriage_migration_generation_1",
        "marriage_migration_generation_2",
    )
    with path.open("w", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--params",
        type=Path,
        default=Path(__file__).with_name("params.json"),
        help="JSON file containing the estimated two-generation model parameters",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "Output",
        help="Directory for Figure A19 plots and CSV data (default: Online Appendix\\Output)",
    )
    args = parser.parse_args()
    rows = outside_market_sensitivity(load_params(args.params))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "Figure A19.csv", rows)

    x = [row["outside_market_value_percent"] for row in rows]
    fig, axis = plt.subplots()
    axis.plot(
        x,
        [row["intermarriage_generation_1"] for row in rows],
        label="Generation 1",
    )
    axis.plot(
        x,
        [row["intermarriage_generation_2"] for row in rows],
        label="Generation 2",
    )
    axis.invert_xaxis()
    axis.set_xlabel("B as % of original level")
    axis.set_ylabel("Inter-marriage rate")
    axis.legend()
    axis.grid(True)
    fig.savefig(args.output_dir / "Figure A19a.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    fig, axis = plt.subplots()
    axis.plot(
        x,
        [row["marriage_migration_generation_1"] for row in rows],
        label="Generation 1",
    )
    axis.plot(
        x,
        [row["marriage_migration_generation_2"] for row in rows],
        label="Generation 2",
    )
    axis.invert_xaxis()
    axis.set_xlabel("B as % of original level")
    axis.set_ylabel("Marriage migration rate")
    axis.legend()
    axis.grid(True)
    fig.savefig(
        args.output_dir / "Figure A19b.png", dpi=300, bbox_inches="tight"
    )
    plt.close(fig)
    print(f"Created Figure A19 plots and CSV in {args.output_dir}")


if __name__ == "__main__":
    main()
