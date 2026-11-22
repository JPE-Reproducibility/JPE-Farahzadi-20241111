"""Solve the nested matching model without endogamy preferences."""

import numpy as np
from scipy.optimize import least_squares


COUNTS = {
    "n_M": 19592,
    "m_M": 20181,
    "n_N": 678402,
    "m_N": 690384,
}

PARAMETERS = {
    "Phi_MM": 1.1154,
    "Phi_MN": 0.57755,
    "Phi_NM": 0.57755,
    "Phi_NN": 0.0397,
    "B_x": 8.3530,
    "B_y": 8.0990,
    "rho": 0.0106,
    "delta": 0.1624,
}

MATCH_NAMES = ("MM", "MN", "NM", "NN", "MM_x", "MM_y", "M0", "0M", "N0", "0N")


def _equations(matches):
    mm, mn, nm, nn, mm_x, mm_y, m0, zero_m, n0, zero_n = matches
    p = PARAMETERS
    rho = p["rho"]
    delta = p["delta"]
    return np.array(
        [
            p["Phi_MM"]
            - rho * np.log(mm / m0)
            - (1 - rho) * np.log((mm + mm_x) / m0)
            - delta * np.log(mm / zero_m)
            - (1 - delta) * np.log((mm + mm_y) / zero_m),
            p["Phi_MM"]
            + p["B_x"]
            - rho * np.log(mm_x / m0)
            - (1 - rho) * np.log((mm + mm_x) / m0)
            - np.log(mm_x),
            p["Phi_MM"]
            + p["B_y"]
            - np.log(mm_y)
            - delta * np.log(mm_y / zero_m)
            - (1 - delta) * np.log((mm + mm_y) / zero_m),
            p["Phi_MN"] - np.log(mn / m0) - np.log(mn / zero_n),
            p["Phi_NM"] - np.log(nm / n0) - np.log(nm / zero_m),
            p["Phi_NN"] - np.log(nn / n0) - np.log(nn / zero_n),
            COUNTS["n_M"] - (m0 + mm + mn + mm_x),
            COUNTS["m_M"] - (zero_m + mm + nm + mm_y),
            COUNTS["n_N"] - (n0 + nn + nm),
            COUNTS["m_N"] - (zero_n + nn + mn),
        ],
        dtype=float,
    )


def solve_counterfactual():
    """Return equilibrium match counts using the published nested parameters."""
    initial = np.full(10, 0.1)
    result = least_squares(_equations, initial, bounds=(0, np.inf))
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"Nested counterfactual failed: {result.message}")
    if np.max(np.abs(_equations(result.x))) > 1e-5:
        raise RuntimeError(
            "Nested counterfactual reported success but did not satisfy "
            "the equilibrium equations."
        )
    return dict(zip(MATCH_NAMES, result.x))
