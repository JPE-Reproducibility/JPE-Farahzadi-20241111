"""Two-generation sensitivity calculations for Figures A18 and A19."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "M3 Two-Generation Matching with Endogeneous Preferences"
    / "Code Figure A20.py"
)


def _load_model():
    spec = spec_from_file_location("figure21_model", MODEL_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load two-generation model from {MODEL_PATH}.")
    model = module_from_spec(spec)
    spec.loader.exec_module(model)
    return model


_model = _load_model()
load_params = _model.load_params


def _outcomes(params):
    first = _model.solve_matching(params, _model.COUNTS_BASE)
    inter1, migration1 = _model.rates_from_match(first)
    second_counts = _model.next_generation_counts(first)
    second = _model.solve_matching(params, second_counts)
    inter2, migration2 = _model.rates_from_match(second)
    return {
        "intermarriage_generation_1": inter1,
        "intermarriage_generation_2": inter2,
        "marriage_migration_generation_1": migration1,
        "marriage_migration_generation_2": migration2,
    }


def endogamy_sensitivity(params):
    alpha_sum = params["alpha_M"] + params["alpha_N"]
    if alpha_sum - params["gamma_MN"] >= 0 or alpha_sum - params["gamma_NM"] >= 0:
        raise ValueError("Baseline inter-religious surplus values must be negative.")
    rows = []
    for level in np.linspace(1.0, 0.0, 21):
        trial = dict(params)
        trial["gamma_MN"] *= level
        trial["gamma_NM"] *= level
        rows.append({"endogamy_penalty_percent": 100 * level, **_outcomes(trial)})
    return rows


def outside_market_sensitivity(params):
    rows = []
    for level in np.linspace(1.0, 0.0, 21):
        trial = dict(params)
        trial["B_x"] *= level
        trial["B_y"] *= level
        rows.append({"outside_market_value_percent": 100 * level, **_outcomes(trial)})
    return rows
