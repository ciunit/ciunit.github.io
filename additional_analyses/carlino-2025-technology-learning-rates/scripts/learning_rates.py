"""Fit Wright's law to each technology in ExpCurves.csv and summarize learning rates.

Wright's model (Carlino et al. 2025, Eqs. 1-3):
    log(C) = log(alpha) + beta * log(P)
    LR = 100 * (1 - 2**beta)

beta is fit by ordinary least squares on log(unit cost) vs log(cumulative production),
using all points of each technology's series (a single, constant learning rate).
"""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "input" / "ExpCurves.csv"
OUTPUT = ROOT / "data" / "output"


def load_series(path):
    series = defaultdict(list)
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            series[row["Tech"]].append(
                (float(row["Cumulative production"]), float(row["Unit cost"]))
            )
    return {tech: np.array(sorted(points)) for tech, points in series.items()}


def fit_tech(points):
    P, C = points[:, 0], points[:, 1]
    beta, _ = np.polyfit(np.log(P), np.log(C), 1)
    return {
        "n_points": len(P),
        "log10_P_range": np.log10(P.max()) - np.log10(P.min()),
        "beta": beta,
        "LR_percent": 100 * (1 - 2**beta),
    }


def summarize(name, values):
    print(f"{name:>22}: mean = {np.mean(values):8.3f}   "
          f"std = {np.std(values, ddof=1):7.3f}   median = {np.median(values):8.3f}")


def summarize_weighted(name, values, weights):
    """Weighted mean and (population) weighted standard deviation."""
    mean = np.average(values, weights=weights)
    std = np.sqrt(np.average((values - mean) ** 2, weights=weights))
    print(f"{name:>22}: mean = {mean:8.3f}   std = {std:7.3f}")


def learning_rate(beta):
    return 100 * (1 - 2**beta)


def beta_summary(beta, weights=None):
    """Mean and std of beta, and the learning rates implied at mean and mean +/- 1 std.

    Unweighted std uses ddof=1; weighted std is the population form.
    """
    if weights is None:
        mean, std = np.mean(beta), np.std(beta, ddof=1)
    else:
        mean = np.average(beta, weights=weights)
        std = np.sqrt(np.average((beta - mean) ** 2, weights=weights))
    return {
        "n_technologies": len(beta),
        "mean_beta": mean,
        "std_beta": std,
        "LR_percent_at_mean_beta": learning_rate(mean),
        "LR_percent_at_mean_beta_minus_1sd": learning_rate(mean - std),
        "LR_percent_at_mean_beta_plus_1sd": learning_rate(mean + std),
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    series = load_series(INPUT)
    results = {tech: fit_tech(points) for tech, points in series.items()}

    with open(OUTPUT / "learning_rates_by_tech.csv", "w", newline="") as f:
        fields = ["Tech", "n_points", "log10_P_range", "beta", "LR_percent"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for tech, r in sorted(results.items()):
            writer.writerow({"Tech": tech, **r})

    x = np.array([r["log10_P_range"] for r in results.values()])
    beta = np.array([r["beta"] for r in results.values()])
    lr = np.array([r["LR_percent"] for r in results.values()])

    print(f"{len(results)} technologies, {sum(r['n_points'] for r in results.values())} points")
    summarize("learning exponent beta", beta)
    summarize("learning rate LR (%)", lr)

    # Weight each technology by the orders of magnitude its production spans.
    n_eff = x.sum() ** 2 / (x**2).sum()
    print(f"weighted by log10_P_range (effective n = {n_eff:.1f}):")
    summarize_weighted("learning exponent beta", beta, x)
    summarize_weighted("learning rate LR (%)", lr, x)

    keep = np.array([tech != "Nuclear_Electricity" for tech in results])
    columns = {
        "unweighted_all": beta_summary(beta),
        "unweighted_without_nuclear": beta_summary(beta[keep]),
        "weighted_all": beta_summary(beta, x),
        "weighted_without_nuclear": beta_summary(beta[keep], x[keep]),
    }
    with open(OUTPUT / "learning_rate_summary.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["statistic", *columns])
        for stat in next(iter(columns.values())):
            writer.writerow([stat, *(f"{col[stat]:.4g}" for col in columns.values())])

    color, ink, muted = "#2a78d6", "#0b0b0b", "#52514e"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    panels = [(axes[0], beta, "Learning exponent β"), (axes[1], lr, "Learning rate LR (%)")]
    for ax, y, label in panels:
        ax.axhline(0, color=muted, lw=0.8)
        ax.axhline(np.mean(y), color=muted, lw=1, ls="--")
        ax.text(x.max(), np.mean(y), f"mean {np.mean(y):.2f}", color=muted,
                ha="right", va="bottom", fontsize=9)
        ax.scatter(x, y, s=28, color=color, edgecolor="white", linewidth=0.8, zorder=3)
        ax.set_ylabel(label, color=ink)
        ax.set_xlabel("log₁₀(last cumulative production) − log₁₀(first)", color=ink)
        ax.grid(color="#e5e4e0", lw=0.6)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle(f"Constant-rate Wright's law fits, {len(results)} technologies", color=ink)
    fig.tight_layout()
    fig.savefig(OUTPUT / "learning_rates_vs_production_range.png", dpi=200)


if __name__ == "__main__":
    main()
