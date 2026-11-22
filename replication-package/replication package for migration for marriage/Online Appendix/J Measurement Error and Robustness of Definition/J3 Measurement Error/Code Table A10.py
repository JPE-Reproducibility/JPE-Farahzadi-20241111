"""Appendix Table A10: baseline and lower-bound outside market value.

The preference and benefit parameters are estimated from observed matches,
and equilibrium is solved with a counterfactual cross-group surplus. Outside market value
is the share of each side's married population matched with a migrant spouse in
the counterfactual:

    women: mu_MM_x / (n_M - mu_M0)      men: mu_MM_y / (m_M - mu_0M)

The observed match counts (muslim M / non-Muslim N; x = women, y = men) are the
fixed aggregate Census counts. They differ between
definitions only in the migrant-marriage counts MM_x, MM_y and the Muslim
population totals n_M, m_M.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

# Cross-group surplus used in the counterfactual scripts.
PHI_CROSS_COUNTERFACTUAL = -0.09945

# Fixed counts for the baseline and lower-bound definitions.
DEFINITIONS = {
    "Baseline": {
        "mu": {
            "NN": 345174, "NM": 1200, "MN": 322, "MM": 5936,
            "N0": 332028, "0N": 344888, "M0": 6579, "0M": 6799,
            "MM_x": 6755, "MM_y": 6246,
        },
        "counts": {"n_M": 19592, "m_M": 20181, "n_N": 678402, "m_N": 690384},
    },
    "Lower bound": {
        "mu": {
            "NN": 345174, "NM": 1200, "MN": 322, "MM": 5936,
            "N0": 332028, "0N": 344888, "M0": 6579, "0M": 6799,
            "MM_x": 5143, "MM_y": 5840,
        },
        "counts": {"n_M": 17980, "m_M": 19775, "n_N": 678402, "m_N": 690384},
    },
}


def estimate_parameters(mu: dict) -> dict:
    """Solve the stability equations for the surplus and benefit parameters."""

    def equations(v):
        phi_mm, phi_mn, phi_nm, phi_nn, b_x, b_y = v
        return [
            phi_mm - np.log(mu["MM"] / mu["M0"]) - np.log(mu["MM"] / mu["0M"]),
            phi_mm + b_x - np.log(mu["MM_x"] / mu["M0"]) - np.log(mu["MM_x"]),
            phi_mm + b_y - np.log(mu["MM_y"]) - np.log(mu["MM_y"] / mu["0M"]),
            phi_mn - np.log(mu["MN"] / mu["M0"]) - np.log(mu["MN"] / mu["0N"]),
            phi_nm - np.log(mu["NM"] / mu["N0"]) - np.log(mu["NM"] / mu["0M"]),
            phi_nn - np.log(mu["NN"] / mu["N0"]) - np.log(mu["NN"] / mu["0N"]),
        ]

    result = least_squares(equations, [0.1] * 6, bounds=([-np.inf] * 6, [np.inf] * 6))
    if not result.success:
        raise RuntimeError(f"Estimation failed: {result.message}")
    names = ("phi_mm", "phi_mn", "phi_nm", "phi_nn", "b_x", "b_y")
    return dict(zip(names, result.x))


def counterfactual(params: dict, counts: dict) -> dict:
    """Solve the equilibrium with the counterfactual cross-group surplus."""
    phi_mm, phi_nn = params["phi_mm"], params["phi_nn"]
    phi_mn = phi_nm = PHI_CROSS_COUNTERFACTUAL
    b_x, b_y = params["b_x"], params["b_y"]

    def equations(v):
        mm, mn, nm, nn, mm_x, mm_y, m0, zm, n0, zn = v
        return [
            phi_mm - np.log(mm / m0) - np.log(mm / zm),
            phi_mm + b_x - np.log(mm_x / m0) - np.log(mm_x),
            phi_mm + b_y - np.log(mm_y) - np.log(mm_y / zm),
            phi_mn - np.log(mn / m0) - np.log(mn / zn),
            phi_nm - np.log(nm / n0) - np.log(nm / zm),
            phi_nn - np.log(nn / n0) - np.log(nn / zn),
            counts["n_M"] - (m0 + mm + mn + mm_x),
            counts["m_M"] - (zm + mm + nm + mm_y),
            counts["n_N"] - (n0 + nn + nm),
            counts["m_N"] - (zn + nn + mn),
        ]

    result = least_squares(equations, [0.1] * 10, bounds=([0] * 10, [np.inf] * 10))
    if not result.success:
        raise RuntimeError(f"Counterfactual failed: {result.message}")
    names = ("MM", "MN", "NM", "NN", "MM_x", "MM_y", "M0", "0M", "N0", "0N")
    return dict(zip(names, result.x))


def main() -> None:
    package_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=package_root
        / "Online Appendix"
        / "Output"
        / "Table A10.csv",
    )
    args = parser.parse_args()

    rows = []
    for definition, inputs in DEFINITIONS.items():
        params = estimate_parameters(inputs["mu"])
        mu = counterfactual(params, inputs["counts"])
        counts = inputs["counts"]
        rows.append(
            {
                "definition": definition,
                "women": mu["MM_x"] / (counts["n_M"] - mu["M0"]),
                "men": mu["MM_y"] / (counts["m_M"] - mu["0M"]),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False, float_format="%.3f")
    print(f"Appendix Table A10 saved to: {args.output}")


if __name__ == "__main__":
    main()
