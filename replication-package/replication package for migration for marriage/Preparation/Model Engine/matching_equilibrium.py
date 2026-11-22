"""Shared readers and solver for the structural matching model."""

from pathlib import Path

import numpy as np
import pandas as pd


def read_matrix(path: Path, value_column: str, groups: list[int]) -> np.ndarray:
    """Read a complete group-pair matrix in model group order."""
    frame = pd.read_stata(path, columns=["groupx", "groupy", value_column])
    if frame.duplicated(["groupx", "groupy"]).any():
        raise ValueError(f"{path} has duplicate group-pair keys.")
    matrix = frame.pivot(index="groupx", columns="groupy", values=value_column)
    matrix = matrix.reindex(index=groups, columns=groups)
    values = matrix.to_numpy(dtype=float)
    if values.shape != (len(groups), len(groups)) or not np.isfinite(values).all():
        raise ValueError(
            f"{path} does not contain a complete finite {value_column} matrix."
        )
    return values


def read_observed_matrix(
    path: Path,
    value_column: str,
    groups: list[int],
) -> np.ndarray:
    """Read a sparse observed match matrix, treating unrecorded pairs as zero."""
    frame = pd.read_stata(path, columns=["group", "sgroup", value_column])
    if frame.duplicated(["group", "sgroup"]).any():
        raise ValueError(f"{path} has duplicate group-pair keys.")
    matrix = frame.pivot(index="group", columns="sgroup", values=value_column)
    matrix = matrix.reindex(index=groups, columns=groups, fill_value=0).fillna(0)
    values = matrix.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError(f"{path} contains invalid {value_column} values.")
    return values


def ipfp(
    phi: np.ndarray,
    nx: np.ndarray,
    ny: np.ndarray,
    dxy: np.ndarray,
    dyx: np.ndarray,
    tolerance: float = 1e-9,
    max_iterations: int = 2000,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Solve the two-sided matching equilibrium and return match masses."""
    if np.any(phi > 1400):
        raise ValueError("Preference values are too large for stable exponentiation.")
    ephi2 = np.exp(phi / 2)
    scale = np.sqrt(1 / (len(nx) + len(ny) + 2 * ephi2.sum()))
    tx = np.full(len(nx), scale)
    ty = np.full(len(ny), scale)

    for _ in range(max_iterations):
        sx = np.sum(ephi2 * ty[np.newaxis, :] + ephi2 * dxy, axis=1)
        next_tx = (np.sqrt(sx**2 + 4 * nx) - sx) / 2
        sy = np.sum(ephi2 * next_tx[:, np.newaxis] + ephi2 * dyx, axis=0)
        next_ty = (np.sqrt(sy**2 + 4 * ny) - sy) / 2
        error = np.max(np.abs(next_tx - tx)) + np.max(np.abs(next_ty - ty))
        tx, ty = next_tx, next_ty
        if error <= tolerance * scale:
            break
    else:
        raise RuntimeError(
            f"IPFP did not converge within {max_iterations} iterations."
        )

    matched = ephi2 * tx[:, np.newaxis] * ty[np.newaxis, :]
    migrant_x = np.divide(
        matched * dxy,
        ty[np.newaxis, :],
        out=np.zeros_like(matched),
        where=ty[np.newaxis, :] != 0,
    )
    migrant_y = np.divide(
        matched * dyx,
        tx[:, np.newaxis],
        out=np.zeros_like(matched),
        where=tx[:, np.newaxis] != 0,
    )
    return matched, migrant_x, migrant_y, tx**2, ty**2
