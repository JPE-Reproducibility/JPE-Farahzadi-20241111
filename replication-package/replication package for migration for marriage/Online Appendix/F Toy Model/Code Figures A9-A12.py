"""Generate appendix Figures A9-A12 and their underlying data.

Run: python "Online Appendix\\F Toy Model\\Code Figures A9-A12.py"
Use --output-dir to choose a different output directory.
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "Output"
STACK_LABELS = ("Abroad", "Local-within group", "Local-intermarriage", "Single")


def _style_axis(ax):
    """Apply the paper plotting style: white background, no grid, black border."""
    ax.set_facecolor("white")
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(1.0)


def _style_legend(legend):
    """Match legend styling used in the supplied figures."""
    frame = legend.get_frame()
    frame.set_facecolor("white")
    frame.set_edgecolor("black")
    frame.set_alpha(1.0)


def solve_equilibrium(
    baseline=0.0, endogamy=0.0, migration=0.0, minority_share=0.1,
    outside_size=1.0, *, reward_endogamy=False, tolerance=1e-12,
    max_iterations=1000,
):
    """Solve the four-market IPFP system."""
    values = np.asarray([baseline, endogamy, migration, minority_share, outside_size])
    if not np.isfinite(values).all():
        raise ValueError("Model parameters must be finite.")
    if not 0 < minority_share < 1 or outside_size < 0:
        raise ValueError("Minority share must be in (0, 1) and outside size nonnegative.")

    difference = np.array([[0.0, 1.0], [1.0, 0.0]])
    if reward_endogamy:
        phi = baseline + endogamy * (1 - difference)
    else:
        phi = baseline - endogamy * difference
    with np.errstate(over="raise", invalid="raise"):
        local_weight = np.exp(phi / 2)
        cross_weight = np.zeros((2, 2))
        cross_weight[1, 1] = np.exp((phi[1, 1] + migration) / 2)

    population = np.array([1 - minority_share, minority_share])
    outside = np.array([0.0, outside_size])
    scale = np.sqrt(1 / (4 + 2 * local_weight.sum()))
    tx = np.full(2, scale)
    ty = np.full(2, scale)
    rx = np.full(2, scale)
    ry = np.full(2, scale)

    def update(mass, match_weight):
        denominator = np.sqrt(match_weight**2 + 4 * mass) + match_weight
        return np.divide(2 * mass, denominator, out=np.zeros_like(mass), where=denominator != 0)

    for _ in range(max_iterations):
        new_tx = update(population, local_weight @ ty + cross_weight @ ry)
        new_rx = update(outside, local_weight @ ry + cross_weight @ ty)
        new_ty = update(population, local_weight.T @ new_tx + cross_weight.T @ new_rx)
        new_ry = update(outside, local_weight.T @ new_rx + cross_weight.T @ new_tx)
        error = sum(
            np.max(np.abs(new - old))
            for new, old in zip((new_tx, new_ty, new_rx, new_ry), (tx, ty, rx, ry))
        )
        tx, ty, rx, ry = new_tx, new_ty, new_rx, new_ry
        if error <= tolerance * scale:
            break
    else:
        raise RuntimeError(
            f"Toy-model equilibrium did not converge after {max_iterations} iterations "
            f"(a={baseline}, b={migration}, c={endogamy}, "
            f"gamma={minority_share}, alpha={outside_size})."
        )

    return {
        "local": local_weight * np.outer(tx, ty),
        "outside": local_weight * np.outer(rx, ry),
        "migrant_women": cross_weight * np.outer(tx, ry),
        "migrant_men": cross_weight * np.outer(rx, ty),
        "local_women_single": tx**2,
        "local_men_single": ty**2,
        "outside_women_single": rx**2,
        "outside_men_single": ry**2,
    }


def outcomes(model, minority_share):
    """Return destination women's population shares and minority marital rates."""
    population = np.array([1 - minority_share, minority_share])
    local = model["local"]
    migrant = model["migrant_women"]
    single = model["local_women_single"]
    groups = {}
    for index, name in ((1, "Minority"), (0, "Majority")):
        groups[name] = 100 * np.array([
            migrant[index, :].sum(),
            local[index, index],
            local[index, 1 - index],
            single[index],
        ]) / population[index]
    minority_married = local[1, :].sum() + migrant[1, :].sum()
    if minority_married <= 0:
        raise ValueError("Minority marriage rate is undefined: no married individuals.")
    return groups, 100 * migrant[1, :].sum() / minority_married, (
        100 * local[1, 0] / minority_married
    )


def stack_figure(parameter, x_label, output_dir):
    records = []
    for value in parameter:
        options = {"migration": value} if x_label == "Migration Utility" else {"endogamy": value}
        groups, _, _ = outcomes(solve_equilibrium(**options), 0.1)
        for group, shares in groups.items():
            records.append({
                "parameter": value, "group": group,
                **dict(zip(("abroad", "local_within", "local_inter", "single"), shares)),
            })
    data = pd.DataFrame(records)
    figure_number = "A9" if x_label == "Migration Utility" else "A10"
    data.to_csv(output_dir / f"Figure {figure_number} data.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    fig.patch.set_facecolor("white")
    for ax, group, title in zip(axes, ("Minority", "Majority"), ("(a) Minority", "(b) Majority")):
        subset = data[data["group"] == group]
        ax.stackplot(subset["parameter"], *(subset[c] for c in
                     ("abroad", "local_within", "local_inter", "single")), labels=STACK_LABELS)
        ax.set(xlim=(-10, 10), ylim=(0, 100), xlabel=x_label, ylabel="Percent", title=title)
        _style_axis(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc="upper center", ncol=4, frameon=True)
    _style_legend(legend)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(output_dir / f"Figure {figure_number}.png", dpi=200)
    plt.close(fig)


def gain_data():
    rows = []
    scenarios = (
        ("endogamy", np.linspace(0, 10, 101)),
        ("migration", np.linspace(-5, 5, 101)),
        ("outside_size", np.arange(200) / 100),
    )
    for scenario, grid in scenarios:
        for value in grid:
            options = {"minority_share": 0.05, "migration": -5.0}
            if scenario == "endogamy":
                options.update(endogamy=value, reward_endogamy=True)
            elif scenario == "migration":
                options.update(migration=value, endogamy=0.0)
            else:
                options.update(outside_size=value, endogamy=0.0)
            model = solve_equilibrium(**options)
            _, migration_rate, intermarriage_rate = outcomes(model, 0.05)
            rows.append({
                "scenario": scenario, "parameter": value,
                "baseline": 0.0, "endogamy": options.get("endogamy", 0.0),
                "migration_utility": options["migration"],
                "outside_size": options.get("outside_size", 1.0),
                "minority_share": 0.05,
                "surplus_specification": (
                    "same_group_reward" if options.get("reward_endogamy") else "cross_group_penalty"
                ),
                "marriage_migration_pct": migration_rate,
                "intermarriage_pct": intermarriage_rate,
            })
    return pd.DataFrame(rows)


def gains_figures(data, output_dir):
    data.to_csv(output_dir / "Figures A11-A12 data.csv", index=False)
    outcomes_to_plot = (
        ("marriage_migration_pct", "Marriage Migration (%)", "Marriage Migration"),
        ("intermarriage_pct", "Intermarriage (%)", "Intermarriage"),
    )
    for column, ylabel, outcome_name in outcomes_to_plot:
        endogamy = data[data["scenario"] == "endogamy"]
        fig, ax = plt.subplots(figsize=(4, 5))
        fig.patch.set_facecolor("white")
        ax.plot(endogamy["parameter"], endogamy[column],
                label="$b$ = -5,\n$\\alpha$ = 1,\n$\\gamma$ = .05")
        ax.set(xlabel="Endogamy Utility ($c$)", ylabel=ylabel)
        _style_axis(ax)
        legend = ax.legend(loc="best")
        _style_legend(legend)
        fig.tight_layout()
        fig.savefig(output_dir / f"Figure A11 ({outcome_name}).png", dpi=200)
        plt.close(fig)

        fig, axes = plt.subplots(1, 2, figsize=(8, 5), sharey=True)
        fig.patch.set_facecolor("white")
        for ax, scenario, xlabel, label in (
            (axes[0], "migration", "Migration Utility ($b$)",
             "$c$ = 0,\n$\\alpha$ = 1,\n$\\gamma$ = .05"),
            (axes[1], "outside_size", "Outside Market Size ($\\alpha$)",
             "$b$ = -5,\n$c$ = 0,\n$\\gamma$ = .05"),
        ):
            subset = data[data["scenario"] == scenario]
            ax.plot(subset["parameter"], subset[column], label=label)
            ax.set_xlabel(xlabel)
            _style_axis(ax)
            legend = ax.legend(loc="best")
            _style_legend(legend)
        axes[0].set_ylabel(ylabel)
        fig.tight_layout()
        fig.savefig(output_dir / f"Figure A12 ({outcome_name}).png", dpi=200)
        plt.close(fig)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stack_figure(np.linspace(-10, 10, 201), "Migration Utility", args.output_dir)
    stack_figure(np.linspace(-10, 10, 201), "Endogamy Utility", args.output_dir)
    gains_figures(gain_data(), args.output_dir)
    print(f"Toy-model figures and CSV data saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
