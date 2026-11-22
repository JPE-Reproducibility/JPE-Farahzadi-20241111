"""Reproduce Figure A20: sensitivity to Muslim population share."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares


COUNTS_BASE = {
    "n_M": 19592.0,
    "m_M": 20181.0,
    "n_N": 678402.0,
    "m_N": 690384.0,
}
FERTILITY = {"MM": 3.07, "MN": 2.78, "NM": 2.46, "NN": 2.36}
P_MUSLIM = {"MM": 0.978, "MN": 0.976, "NM": 0.238, "NN": 0.001}
PARAMETER_NAMES = ("alpha_M", "alpha_N", "gamma_MN", "gamma_NM", "B_x", "B_y")


def load_params(path):
    with path.open(encoding="utf-8") as parameter_file:
        params = json.load(parameter_file)
    if not isinstance(params, dict):
        raise ValueError(f"Expected a JSON object in parameter file: {path}")
    missing = [name for name in PARAMETER_NAMES if name not in params]
    if missing:
        raise ValueError(f"Missing parameters in {path}: {', '.join(missing)}")
    for name in PARAMETER_NAMES:
        try:
            params[name] = float(params[name])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Parameter {name} must be numeric in {path}") from error
        if not np.isfinite(params[name]):
            raise ValueError(f"Parameter {name} must be finite in {path}")
    return params


def solve_matching(params, counts):
    alpha_m, alpha_n = params["alpha_M"], params["alpha_N"]
    phi_mm = 2 * alpha_m
    phi_nn = 2 * alpha_n
    phi_mn = alpha_m + alpha_n - params["gamma_MN"]
    phi_nm = alpha_m + alpha_n - params["gamma_NM"]

    def equations(masses):
        m0, zero_m, n0, zero_n, mm, mn, nm, nn, mm_x, mm_y = masses
        residuals = np.zeros(10)
        residuals[0] = (
            phi_mm - np.log(mm / m0) - np.log((mm + mn) / m0)
            - np.log(mm / zero_m) - np.log((mm + nm) / zero_m)
        )
        residuals[1] = (
            phi_mn - np.log(mn / m0) - np.log((mn + mm) / m0)
            - np.log(mn / zero_n) - np.log((mn + nn) / zero_n)
        )
        residuals[2] = (
            phi_nm - np.log(nm / n0) - np.log((nm + nn) / n0)
            - np.log(nm / zero_m) - np.log((nm + mm) / zero_m)
        )
        residuals[3] = (
            phi_nn - np.log(nn / n0) - np.log((nn + nm) / n0)
            - np.log(nn / zero_n) - np.log((nn + mn) / zero_n)
        )
        residuals[4] = phi_mm + params["B_x"] - np.log(mm_x**2 / m0)
        residuals[5] = phi_mm + params["B_y"] - np.log(mm_y**2 / zero_m)
        residuals[6] = m0 + mm + mn + mm_x - counts["n_M"]
        residuals[7] = zero_m + mm + nm + mm_y - counts["m_M"]
        residuals[8] = n0 + nn + nm - counts["n_N"]
        residuals[9] = zero_n + nn + mn - counts["m_N"]
        return residuals

    result = least_squares(
        equations,
        np.ones(10),
        bounds=(np.full(10, 1e-6), np.full(10, np.inf)),
    )
    if not result.success:
        raise RuntimeError(f"Matching equilibrium solver failed: {result.message}")
    if not np.all(np.isfinite(result.x)):
        raise RuntimeError("Matching equilibrium solver returned non-finite match masses.")
    residuals = equations(result.x)
    if np.max(np.abs(residuals[:6])) > 1e-6:
        raise RuntimeError("Matching equilibrium stability equations did not converge.")
    for residual, count_name in zip(residuals[6:], ("n_M", "m_M", "n_N", "m_N")):
        if abs(residual) > max(1e-4, counts[count_name] * 1e-8):
            raise RuntimeError(
                f"Matching equilibrium feasibility equation did not converge for {count_name}."
            )

    mass_names = ("M0", "0M", "N0", "0N", "MM", "MN", "NM", "NN", "MM_x", "MM_y")
    return dict(zip(mass_names, result.x))


def rates_from_match(masses):
    denominator_women = masses["MM"] + masses["MM_x"] + masses["MN"]
    denominator_men = masses["MM"] + masses["MM_y"] + masses["NM"]
    intermarriage = 0.5 * (
        masses["MN"] / denominator_women + masses["NM"] / denominator_men
    )
    migration = 0.5 * (
        masses["MM_x"] / denominator_women + masses["MM_y"] / denominator_men
    )
    return intermarriage, migration


def next_generation_counts(masses):
    all_muslim_matches = masses["MM"] + masses["MM_x"] + masses["MM_y"]
    muslim_children = 0.5 * (
        FERTILITY["MM"] * all_muslim_matches * P_MUSLIM["MM"]
        + FERTILITY["MN"] * masses["MN"] * P_MUSLIM["MN"]
        + FERTILITY["NM"] * masses["NM"] * P_MUSLIM["NM"]
        + FERTILITY["NN"] * masses["NN"] * P_MUSLIM["NN"]
    )
    non_muslim_children = 0.5 * (
        FERTILITY["MM"] * all_muslim_matches * (1 - P_MUSLIM["MM"])
        + FERTILITY["MN"] * masses["MN"] * (1 - P_MUSLIM["MN"])
        + FERTILITY["NM"] * masses["NM"] * (1 - P_MUSLIM["NM"])
        + FERTILITY["NN"] * masses["NN"] * (1 - P_MUSLIM["NN"])
    )
    return {
        "n_M": muslim_children,
        "m_M": muslim_children,
        "n_N": non_muslim_children,
        "m_N": non_muslim_children,
    }


def build_figure_data(params):
    base_counts = COUNTS_BASE
    base_muslim_count = base_counts["n_M"] + base_counts["m_M"]
    base_population = base_muslim_count + base_counts["n_N"] + base_counts["m_N"]
    base_muslim_share = base_muslim_count / base_population
    gamma_mn_base = params["gamma_MN"] * base_muslim_share
    gamma_nm_base = params["gamma_NM"] * base_muslim_share

    rows = []
    for step in range(11):
        scale = 1 + step * 0.1
        counts_g1 = dict(base_counts)
        counts_g1["n_M"] *= scale
        counts_g1["m_M"] *= scale
        muslim_share_g1 = (
            counts_g1["n_M"] + counts_g1["m_M"]
        ) / sum(counts_g1.values())

        endogenous_g1_params = dict(params)
        endogenous_g1_params["gamma_MN"] = gamma_mn_base / muslim_share_g1
        endogenous_g1_params["gamma_NM"] = gamma_nm_base / muslim_share_g1

        endogenous_g1_matches = solve_matching(endogenous_g1_params, counts_g1)
        endogenous_g1_inter, endogenous_g1_migration = rates_from_match(endogenous_g1_matches)
        counts_g2 = next_generation_counts(endogenous_g1_matches)
        muslim_share_g2 = (
            counts_g2["n_M"] + counts_g2["m_M"]
        ) / sum(counts_g2.values())

        endogenous_g2_params = dict(params)
        endogenous_g2_params["gamma_MN"] = gamma_mn_base / muslim_share_g2
        endogenous_g2_params["gamma_NM"] = gamma_nm_base / muslim_share_g2
        endogenous_g2_matches = solve_matching(endogenous_g2_params, counts_g2)
        endogenous_g2_inter, endogenous_g2_migration = rates_from_match(endogenous_g2_matches)

        exogenous_g1_matches = solve_matching(params, counts_g1)
        exogenous_g1_inter, exogenous_g1_migration = rates_from_match(exogenous_g1_matches)
        exogenous_counts_g2 = next_generation_counts(exogenous_g1_matches)
        exogenous_g2_matches = solve_matching(params, exogenous_counts_g2)
        exogenous_g2_inter, exogenous_g2_migration = rates_from_match(exogenous_g2_matches)

        rows.append(
            {
                "muslim_population_scale": scale,
                "muslim_share_generation_1": muslim_share_g1,
                "muslim_share_generation_2_endogenous": muslim_share_g2,
                "intermarriage_generation_1_endogenous": endogenous_g1_inter,
                "intermarriage_generation_2_endogenous": endogenous_g2_inter,
                "intermarriage_generation_1_exogenous": exogenous_g1_inter,
                "intermarriage_generation_2_exogenous": exogenous_g2_inter,
                "marriage_migration_generation_1_endogenous": endogenous_g1_migration,
                "marriage_migration_generation_2_endogenous": endogenous_g2_migration,
                "marriage_migration_generation_1_exogenous": exogenous_g1_migration,
                "marriage_migration_generation_2_exogenous": exogenous_g2_migration,
            }
        )
    return rows


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _plot_outcome(rows, outcome, ylabel, output_path):
    x = [row["muslim_population_scale"] for row in rows]
    fig, axis = plt.subplots()
    for generation, color in ((1, "tab:blue"), (2, "tab:orange")):
        axis.plot(
            x,
            [row[f"{outcome}_generation_{generation}_endogenous"] for row in rows],
            color=color,
            linestyle="-",
            label=f"Generation {generation} - Endogenous",
        )
        axis.plot(
            x,
            [row[f"{outcome}_generation_{generation}_exogenous"] for row in rows],
            color=color,
            linestyle="--",
            label=f"Generation {generation} - Exogenous",
        )
    axis.set_xlabel("Muslim Population Scale Factor")
    axis.set_ylabel(ylabel)
    axis.grid(True)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--params",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "M2 Two-Generation Matching"
        / "params.json",
        help="JSON file containing the estimated two-generation model parameters",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "Output",
        help="Directory for Figure A20 plots and CSV data (default: Online Appendix\\Output)",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    rows = build_figure_data(params)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "Figure A20.csv", rows)
    _plot_outcome(
        rows,
        "intermarriage",
        "Intermarriage Rate",
        args.output_dir / "Figure A20a.png",
    )
    _plot_outcome(
        rows,
        "marriage_migration",
        "Marriage Migration Rate",
        args.output_dir / "Figure A20b.png",
    )
    print(f"Created Figure A20 plots and CSV in {args.output_dir}")


if __name__ == "__main__":
    main()
