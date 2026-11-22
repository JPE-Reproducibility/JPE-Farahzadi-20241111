"""Run the preserved nested-parameter solver on the supplied aggregate counts.

The two included feasibility residuals are zero for these hard-coded counts.
Consequently, rho and delta are not separately identified by this system; the
reported solution depends on the solver's starting point and bounds.
"""

import numpy as np
from scipy.optimize import least_squares


OBSERVED_MATCHES = {
    "NN": 345174,
    "NM": 1200,
    "MN": 322,
    "MM": 5936,
    "N0": 332028,
    "0N": 344888,
    "M0": 6579,
    "0M": 6799,
    "MM_x": 6755,
    "MM_y": 6246,
}

COUNTS = {
    "n_M": 19592,
    "m_M": 20181,
    "n_N": 678402,
    "m_N": 690384,
}

PARAMETER_NAMES = (
    "Phi_MM",
    "Phi_MN",
    "Phi_NM",
    "Phi_NN",
    "B_x",
    "B_y",
    "rho",
    "delta",
)


def _equations(parameters):
    phi_mm, phi_mn, phi_nm, phi_nn, b_x, b_y, rho, delta = parameters
    mu = OBSERVED_MATCHES
    return np.array(
        [
            phi_mm
            - rho * np.log(mu["MM"] / mu["M0"])
            - (1 - rho) * np.log((mu["MM"] + mu["MM_x"]) / mu["M0"])
            - delta * np.log(mu["MM"] / mu["0M"])
            - (1 - delta) * np.log((mu["MM"] + mu["MM_y"]) / mu["0M"]),
            phi_mm
            + b_x
            - rho * np.log(mu["MM_x"] / mu["M0"])
            - (1 - rho) * np.log((mu["MM"] + mu["MM_x"]) / mu["M0"])
            - np.log(mu["MM_x"]),
            phi_mm
            + b_y
            - np.log(mu["MM_y"])
            - delta * np.log(mu["MM_y"] / mu["0M"])
            - (1 - delta) * np.log((mu["MM"] + mu["MM_y"]) / mu["0M"]),
            phi_mn
            - np.log(mu["MN"] / mu["M0"])
            - np.log(mu["MN"] / mu["0N"]),
            phi_nm
            - np.log(mu["NM"] / mu["N0"])
            - np.log(mu["NM"] / mu["0M"]),
            phi_nn
            - np.log(mu["NN"] / mu["N0"])
            - np.log(mu["NN"] / mu["0N"]),
            COUNTS["n_M"]
            - (mu["M0"] + mu["MM"] + mu["MN"] + mu["MM_x"]),
            COUNTS["m_M"]
            - (mu["0M"] + mu["MM"] + mu["NM"] + mu["MM_y"]),
        ],
        dtype=float,
    )


def estimate_nested():
    """Return parameter estimates from the nested-model system in the source."""
    initial = np.array([0.1] * 6 + [0.5] * 2)
    lower = np.array([-np.inf] * 6 + [0.01] * 2)
    upper = np.array([np.inf] * 6 + [0.99] * 2)
    result = least_squares(_equations, initial, bounds=(lower, upper))
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"Nested parameter estimation failed: {result.message}")
    if np.max(np.abs(_equations(result.x))) > 1e-7:
        raise RuntimeError(
            "Nested parameter estimation reported success but did not satisfy "
            "the model equations."
        )
    return dict(zip(PARAMETER_NAMES, result.x))
