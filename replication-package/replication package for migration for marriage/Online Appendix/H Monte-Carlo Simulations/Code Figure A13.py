"""Reproduce the Monte Carlo exercise underlying Appendix Figure A13.

The exercise varies the number of replications, not the sample size.
Run from any directory; use --output-dir, --seed, or --replications to override
the default output folder, random seed, or replication counts.
"""

import argparse
from itertools import product
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "Output"
PARAMETERS = ("alpha_1", "alpha_2", "alpha_3", "beta_1", "beta_2", "beta_3")
LABELS = (r"$\alpha_1$", r"$\alpha_2$", r"$\alpha_3$",
          r"$\beta_1$", r"$\beta_2$", r"$\beta_3$")
TRUE_VALUES = np.array([0.0, 0.0, 5.0, 1.0, 1.0, 3.0])
LOCAL_WOMEN = np.array([0.95 * 0.6, 0.95 * 0.4, 0.05 * 0.7, 0.05 * 0.3])
LOCAL_MEN = np.array([0.95 * 0.6, 0.95 * 0.4, 0.05 * 0.6, 0.05 * 0.4])
OUTSIDE_WOMEN = np.array([0.0, 0.0, 0.9, 0.1])
OUTSIDE_MEN = np.array([0.0, 0.0, 0.8, 0.2])

TYPES = np.array(list(product((0, 1), repeat=2)))
WOMEN = np.repeat(TYPES, 4, axis=0)
MEN = np.tile(TYPES, (4, 1))
DESIGN = np.column_stack((
    np.ones(16),
    WOMEN[:, 0], MEN[:, 0], WOMEN[:, 0] * MEN[:, 0],
    WOMEN[:, 1], MEN[:, 1], WOMEN[:, 1] * MEN[:, 1],
))


def solve_market(phi, migration=2.0, tolerance=1e-12, max_iterations=10000):
    """Solve the local and outside market matching equations."""
    weight = np.exp(phi / 2)
    migration_weight = np.zeros_like(weight)
    migration_weight[2:, 2:] = weight[2:, 2:] * np.exp(migration / 2)
    scale = np.sqrt(1 / (8 + 2 * weight.sum()))
    tx = np.full(4, scale)
    ty = np.full(4, scale)
    rx = np.full(4, scale)
    ry = np.full(4, scale)

    def update(population, total):
        denominator = np.sqrt(total * total + 4 * population) + total
        return np.divide(2 * population, denominator, out=np.zeros_like(population),
                         where=denominator != 0)

    for _ in range(max_iterations):
        new_tx = update(LOCAL_WOMEN, weight @ ty + migration_weight @ ry)
        new_rx = update(OUTSIDE_WOMEN, weight @ ry + migration_weight @ ty)
        new_ty = update(LOCAL_MEN, weight.T @ new_tx + migration_weight.T @ new_rx)
        new_ry = update(OUTSIDE_MEN, weight.T @ new_rx + migration_weight.T @ new_tx)
        error = sum(np.max(np.abs(new - old)) for new, old in zip(
            (new_tx, new_ty, new_rx, new_ry), (tx, ty, rx, ry)))
        tx, ty, rx, ry = new_tx, new_ty, new_rx, new_ry
        if error <= tolerance * scale:
            local = weight * np.outer(tx, ty)
            return local, tx**2, ty**2
    raise RuntimeError(f"Matching equilibrium did not converge in {max_iterations} iterations.")


def estimate_once(rng):
    """Draw type-pair shocks and estimate surplus coefficients from local matches."""
    shocks = rng.gumbel(size=16) + rng.gumbel(size=16)
    phi = (DESIGN[:, 1:] @ TRUE_VALUES + shocks).reshape(4, 4)
    local, women_single, men_single = solve_market(phi)
    observed_surplus = 2 * np.log(local / np.sqrt(np.outer(women_single, men_single)))
    coefficients, _, rank, _ = np.linalg.lstsq(DESIGN, observed_surplus.ravel(), rcond=None)
    if rank != DESIGN.shape[1] or not np.isfinite(coefficients).all():
        raise RuntimeError("The simulation regression is not full rank or is non-finite.")
    return coefficients[1:]


def simulate(replications, seed):
    rng = np.random.default_rng(seed)
    rows = []
    for count in replications:
        for replication in range(1, count + 1):
            try:
                estimates = estimate_once(rng)
            except (FloatingPointError, RuntimeError) as error:
                raise RuntimeError(
                    f"Simulation failed for {count} replications, run {replication}."
                ) from error
            rows.append((count, replication, *estimates))
    return pd.DataFrame(rows, columns=["replication_count", "replication", *PARAMETERS])


def plot_results(results, replications, output_dir):
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    fig.patch.set_facecolor("white")
    densities = []
    for ax, parameter, label, true_value in zip(axes.flat, PARAMETERS, LABELS, TRUE_VALUES):
        samples = [results.loc[results["replication_count"] == count, parameter].to_numpy()
                   for count in replications]
        kernels = [gaussian_kde(sample, bw_method=0.5) for sample in samples]
        lower = min(sample.min() - 3 * np.sqrt(kernel.covariance[0, 0])
                    for sample, kernel in zip(samples, kernels))
        upper = max(sample.max() + 3 * np.sqrt(kernel.covariance[0, 0])
                    for sample, kernel in zip(samples, kernels))
        grid = np.linspace(lower, upper, 300)
        for count, kernel in zip(replications, kernels):
            density = kernel(grid)
            ax.plot(grid, density, label=f"Replications = {count}", linewidth=2)
            densities.extend((parameter, count, x, y) for x, y in zip(grid, density))
        ax.axvline(true_value, color="gray", linestyle="--", linewidth=1)
        ax.set(xlabel=label, ylabel="Density")
        ax.set_facecolor("white")
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color("black")
            spine.set_linewidth(1)
        legend = ax.legend(frameon=True)
        legend.get_frame().set_facecolor("white")
        legend.get_frame().set_edgecolor("black")
        legend.get_frame().set_alpha(1)
    fig.tight_layout()
    fig.savefig(output_dir / "Figure A13.png", dpi=200)
    plt.close(fig)
    pd.DataFrame(densities, columns=["parameter", "replication_count", "value", "density"]
                 ).to_csv(output_dir / "Figure A13 densities.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=20261108)
    parser.add_argument("--replications", type=int, nargs="+", default=[50, 500, 5000])
    args = parser.parse_args()
    if any(n < 2 for n in args.replications) or len(set(args.replications)) != len(args.replications):
        parser.error("--replications must contain distinct counts of at least 2")
    results = simulate(args.replications, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output_dir / "Figure A13 estimates.csv", index=False)
    plot_results(results, args.replications, args.output_dir)
    print(f"Figure A13 and simulation data saved to: {args.output_dir} (seed {args.seed})")


if __name__ == "__main__":
    main()
