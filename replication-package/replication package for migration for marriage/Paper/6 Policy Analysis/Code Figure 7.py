"""Create main-text Figure 7: equilibrium effects of a marriage migration tax."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

GROUP_COUNT = 60
TOLERANCE = 1e-9
MAX_ITERATIONS = 2_000


def _read_matrix(frame, value_column, groups):
    matrix = frame.pivot(
        index="groupx", columns="groupy", values=value_column
    ).reindex(index=groups, columns=groups)
    if matrix.isna().any().any():
        raise ValueError(f"{value_column} does not cover all 60-by-60 group pairs.")
    values = matrix.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"{value_column} contains missing or non-finite values.")
    return values


def load_model_inputs(input_dir):
    """Read and validate the baseline distributions and estimated model terms."""
    dist_path = input_dir / "dist.dta"
    phi_path = input_dir / "phi.dta"
    d_path = input_dir / "d.dta"
    for path in (dist_path, phi_path, d_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Required input not found: {path}. Run Code Table 4.do first."
            )

    distribution = pd.read_stata(dist_path).sort_values("group")
    groups = distribution["group"].astype(int).to_numpy()
    if len(groups) != GROUP_COUNT or len(np.unique(groups)) != GROUP_COUNT:
        raise ValueError(
            f"dist.dta must contain exactly {GROUP_COUNT} unique model groups; "
            f"found {len(groups)} rows and {len(np.unique(groups))} unique groups."
        )

    nx = distribution["nx"].to_numpy(dtype=float)
    ny = distribution["ny"].to_numpy(dtype=float)
    if (
        not np.isfinite(nx).all()
        or not np.isfinite(ny).all()
        or (nx < 0).any()
        or (ny < 0).any()
    ):
        raise ValueError("Population counts must be finite and non-negative.")

    phi = _read_matrix(pd.read_stata(phi_path), "phi", groups)
    outside_terms = pd.read_stata(d_path)
    dxy = _read_matrix(outside_terms, "D_women", groups)
    dyx = _read_matrix(outside_terms, "D_men", groups)
    if (dxy < 0).any() or (dyx < 0).any():
        raise ValueError("Outside-market terms must be non-negative.")

    return groups, nx, ny, phi, dxy, dyx


def solve_equilibrium(phi, nx, ny, dxy, dyx):
    """Solve local and migration matches for one set of outside-market terms."""
    ephi = np.exp(phi / 2)
    if not np.isfinite(ephi).all():
        raise ValueError("Estimated preferences overflowed while exponentiating.")

    scale = np.sqrt(1 / (len(nx) + len(ny) + 2 * ephi.sum()))
    tx = np.full(len(nx), scale)
    ty = np.full(len(ny), scale)

    for _ in range(MAX_ITERATIONS):
        sx = np.sum(ephi * (ty[np.newaxis, :] + dxy), axis=1)
        root_x = np.sqrt(sx**2 + 4 * nx)
        next_tx = np.divide(
            2 * nx,
            root_x + sx,
            out=np.zeros_like(nx),
            where=(root_x + sx) != 0,
        )

        sy = np.sum(ephi * (next_tx[:, np.newaxis] + dyx), axis=0)
        root_y = np.sqrt(sy**2 + 4 * ny)
        next_ty = np.divide(
            2 * ny,
            root_y + sy,
            out=np.zeros_like(ny),
            where=(root_y + sy) != 0,
        )

        difference = np.max(np.abs(next_tx - tx)) + np.max(np.abs(next_ty - ty))
        tx, ty = next_tx, next_ty
        if difference <= TOLERANCE * scale:
            break
    else:
        raise RuntimeError(
            f"Equilibrium solver did not converge in {MAX_ITERATIONS} iterations."
        )

    local_matches = ephi * tx[:, np.newaxis] * ty[np.newaxis, :]
    x_migration = np.divide(
        local_matches * dxy,
        ty[np.newaxis, :],
        out=np.zeros_like(local_matches),
        where=ty[np.newaxis, :] != 0,
    )
    y_migration = np.divide(
        local_matches * dyx,
        tx[:, np.newaxis],
        out=np.zeros_like(local_matches),
        where=tx[:, np.newaxis] != 0,
    )
    return local_matches, tx**2, ty**2, x_migration, y_migration


def _rate(numerator, denominator):
    total = denominator.sum()
    if total == 0:
        return np.nan
    return numerator.sum() / total


def summarize_equilibrium(groups, nx, ny, outcomes):
    """Calculate the five religious-group rates shown in Figure 7."""
    local, single_x, single_y, x_migration, y_migration = outcomes
    ethnic = (groups // 100) % 10
    religion = (groups // 10) % 10
    education = groups % 10
    rates = {}

    for religion_code, label in ((0, "non_muslim"), (1, "muslim")):
        x_mask = (religion == religion_code) & (ethnic != 0)
        y_mask = (religion == religion_code) & (ethnic != 0)

        x_local = local[x_mask, :]
        y_local = local[:, y_mask]
        x_migrant = x_migration[x_mask, :]
        y_migrant = y_migration[:, y_mask]
        rates[f"migration_{label}"] = 100 * np.nanmean(
            (
                _rate(x_migrant, x_local + x_migrant),
                _rate(y_migrant, y_local + y_migrant),
            )
        )

        x_religion_differs = religion[:, np.newaxis] != religion[np.newaxis, :]
        x_ethnicity_differs = (
            ethnic[:, np.newaxis] != ethnic[np.newaxis, :]
        )
        x_education_differs = (
            education[:, np.newaxis] != education[np.newaxis, :]
        )

        rates[f"interreligious_{label}"] = 100 * np.nanmean(
            (
                _rate(
                    (local * x_religion_differs)[x_mask, :]
                    + (x_migration * x_religion_differs)[x_mask, :],
                    x_local + x_migrant,
                ),
                _rate(
                    (local * x_religion_differs)[:, y_mask]
                    + (y_migration * x_religion_differs)[:, y_mask],
                    y_local + y_migrant,
                ),
            )
        )
        rates[f"interethnic_{label}"] = 100 * np.nanmean(
            (
                _rate(
                    (local * x_ethnicity_differs)[x_mask, :]
                    + (x_migration * x_ethnicity_differs)[x_mask, :],
                    x_local + x_migrant,
                ),
                _rate(
                    (local * x_ethnicity_differs)[:, y_mask]
                    + (y_migration * x_ethnicity_differs)[:, y_mask],
                    y_local + y_migrant,
                ),
            )
        )
        rates[f"intereducation_{label}"] = 100 * np.nanmean(
            (
                _rate(
                    (local * x_education_differs)[x_mask, :]
                    + (x_migration * x_education_differs)[x_mask, :],
                    x_local + x_migrant,
                ),
                _rate(
                    (local * x_education_differs)[:, y_mask]
                    + (y_migration * x_education_differs)[:, y_mask],
                    y_local + y_migrant,
                ),
            )
        )

        rates[f"single_{label}"] = 100 * np.nanmean(
            (
                _rate(single_x[x_mask], nx[x_mask]),
                _rate(single_y[y_mask], ny[y_mask]),
            )
        )

    return rates


def create_figure(results, output_path):
    """Plot migration, intermarriage, and singlehood rates over the tax grid."""
    tax = np.arange(0,5,0.01)
    figure = plt.figure(figsize=(6.4, 5.4))
    axes = (
        plt.subplot2grid((3, 8), (0, 0), colspan=4),
        plt.subplot2grid((3, 8), (0, 4), colspan=4),
        plt.subplot2grid((3, 8), (1, 0), colspan=4),
        plt.subplot2grid((3, 8), (1, 4), colspan=4),
        plt.subplot2grid((3, 8), (2, 2), colspan=4),
    )
    panels = (
        ("migration", "marriage migration (%)"),
        ("interreligious", "inter-religious marriage (%)"),
        ("interethnic", "inter-ethnic marriage (%)"),
        ("intereducation", "inter-education marriage (%)"),
        ("single", "single (%)"),
    )

    for axis, (measure, ylabel) in zip(axes, panels):
        axis.plot(
            tax,
            results[f"{measure}_non_muslim"],
            color="darkred",
            linestyle="dashed",
            label="Non-Muslim",
        )
        axis.plot(
            tax,
            results[f"{measure}_muslim"],
            color="darkblue",
            label="Muslim",
        )
        axis.set_ylabel(ylabel, fontsize=7)
        axis.tick_params(axis="both", labelsize=6)

    axes[-1].set_xlabel("marriage migration tax", fontsize=7)
    figure.legend(
        ["Non-Muslim", "Muslim"],
        ncol=2,
        fontsize=8,
        loc="upper center",
        borderaxespad=1.5,
        edgecolor="k",
    )
    figure.subplots_adjust(wspace=2, hspace=0.38)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close(figure)


def main():
    package_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=package_root / "Synthetic Data" / "model_out",
        help="Directory containing dist.dta, phi.dta, and d.dta from Code Table 4.do.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=package_root
        / "Paper"
        / "Output"
        / "Figure 7.png",
        help="Output PNG path (defaults to Paper\\Output).",
    )
    args = parser.parse_args()

    groups, nx, ny, phi, dxy, dyx = load_model_inputs(args.input_dir)
    results = []
    for tax in np.exp(np.arange(0,5,0.01)/2):
        # The paper subtracts T from migration utility, scaling exp(B) by exp(-T).
        equilibrium = solve_equilibrium(
            phi, nx, ny, np.divide(dxy,tax), np.divide(dyx,tax)
        )
        results.append(
            {"tax": tax, **summarize_equilibrium(groups, nx, ny, equilibrium)}
        )

    create_figure(pd.DataFrame(results), args.output)
    print(f"Figure 7 saved to {args.output}")


if __name__ == "__main__":
    main()
