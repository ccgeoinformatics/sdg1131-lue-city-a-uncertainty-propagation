#!/usr/bin/env python3
"""
City A Monte Carlo uncertainty propagation experiment for SDG 11.3.1 LUE assessment.

This script implements the thesis-specific City A experiment, where BUA and Pop at
t1 and t2 are treated as uncertain inputs and propagated to LCR, PGR, LCRPGR,
and probabilistic LUE regime membership.

Default City A configuration:
    BUA_t1 = 53.0
    BUA_t2 = 61.5
    Pop_t1 = 320,000
    Pop_t2 = 330,000
    T = 10 years
    BUA relative SD = 5%
    Pop relative SD = 10%

Main thesis dependence scenarios:
    S1_full_independence
    S2_temporal_only
    S3_temporal_cross

An additional S4 scenario can be included using --include-s4.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from numpy.random import SeedSequence, default_rng

from lue_regime_classifier import classify_regime


EPS = 1e-10


def compute_lcr(bua1: np.ndarray, bua2: np.ndarray, delta_t: float) -> np.ndarray:
    """Compute LCR in decimal units per year."""
    return ((bua2 - bua1) / bua1) / delta_t


def compute_pgr(pop1: np.ndarray, pop2: np.ndarray, delta_t: float) -> np.ndarray:
    """Compute PGR in decimal units per year using logarithmic population growth."""
    return (np.log(pop2) - np.log(pop1)) / delta_t


def compute_lcrpgr(lcr: np.ndarray, pgr: np.ndarray, eps: float = EPS) -> np.ndarray:
    """Compute LCRPGR, returning NaN where PGR is effectively zero."""
    ratio = np.full_like(lcr, np.nan, dtype=float)
    mask = np.abs(pgr) > eps
    ratio[mask] = lcr[mask] / pgr[mask]
    return ratio


def get_city_a_parameters() -> dict:
    """Return the thesis-specific City A baseline values and marginal uncertainty levels."""
    bua_t1_mean = 53.0
    bua_t2_mean = 61.5
    pop_t1_mean = 320_000.0
    pop_t2_mean = 330_000.0
    delta_t = 10.0

    bua_rel_sd = 0.05
    pop_rel_sd = 0.10

    means = np.array(
        [bua_t1_mean, bua_t2_mean, pop_t1_mean, pop_t2_mean],
        dtype=float,
    )

    stds = np.array(
        [
            bua_t1_mean * bua_rel_sd,
            bua_t2_mean * bua_rel_sd,
            pop_t1_mean * pop_rel_sd,
            pop_t2_mean * pop_rel_sd,
        ],
        dtype=float,
    )

    return {
        "bua_t1_mean": bua_t1_mean,
        "bua_t2_mean": bua_t2_mean,
        "pop_t1_mean": pop_t1_mean,
        "pop_t2_mean": pop_t2_mean,
        "delta_t": delta_t,
        "bua_rel_sd": bua_rel_sd,
        "pop_rel_sd": pop_rel_sd,
        "means": means,
        "stds": stds,
    }


def get_dependence_scenarios(include_s4: bool = False) -> Dict[str, np.ndarray]:
    """
    Return correlation matrices for the City A dependence scenarios.

    Input vector order:
        [BUA_t1, BUA_t2, Pop_t1, Pop_t2]
    """
    scenarios = {
        "S1_full_independence": np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=float,
        ),
        "S2_temporal_only": np.array(
            [
                [1.0, 0.8, 0.0, 0.0],
                [0.8, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.8],
                [0.0, 0.0, 0.8, 1.0],
            ],
            dtype=float,
        ),
        "S3_temporal_cross": np.array(
            [
                [1.0, 0.8, 0.5, 0.5],
                [0.8, 1.0, 0.5, 0.5],
                [0.5, 0.5, 1.0, 0.8],
                [0.5, 0.5, 0.8, 1.0],
            ],
            dtype=float,
        ),
    }

    if include_s4:
        scenarios["S4_temporal_cross_higher_rho"] = np.array(
            [
                [1.0, 0.8, 0.8, 0.8],
                [0.8, 1.0, 0.8, 0.8],
                [0.8, 0.8, 1.0, 0.8],
                [0.8, 0.8, 0.8, 1.0],
            ],
            dtype=float,
        )

    return scenarios


def is_positive_semidefinite(matrix: np.ndarray, tol: float = 1e-10) -> tuple[bool, float]:
    """Check whether a matrix is positive semi-definite within a numerical tolerance."""
    eigvals = np.linalg.eigvalsh(matrix)
    min_eig = float(np.min(eigvals))
    return min_eig >= -tol, min_eig


def summarize_indicator(values: np.ndarray, name: str) -> dict:
    """Summarize one simulated indicator distribution."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if len(values) == 0:
        return {
            f"{name}_mean": np.nan,
            f"{name}_std": np.nan,
            f"{name}_median": np.nan,
            f"{name}_p2_5": np.nan,
            f"{name}_p97_5": np.nan,
            f"{name}_width_95": np.nan,
        }

    p2_5 = float(np.quantile(values, 0.025))
    p97_5 = float(np.quantile(values, 0.975))

    return {
        f"{name}_mean": float(np.mean(values)),
        f"{name}_std": float(np.std(values, ddof=1)),
        f"{name}_median": float(np.median(values)),
        f"{name}_p2_5": p2_5,
        f"{name}_p97_5": p97_5,
        f"{name}_width_95": p97_5 - p2_5,
    }


def classify_regimes(lcr: np.ndarray, pgr: np.ndarray, lcrpgr: np.ndarray) -> list[str]:
    """Classify all Monte Carlo draws into LUE regimes."""
    return [
        classify_regime(float(lcr_i), float(pgr_i), float(ratio_i) if np.isfinite(ratio_i) else None)
        for lcr_i, pgr_i, ratio_i in zip(lcr, pgr, lcrpgr)
    ]


def summarize_regime_probabilities(regimes: list[str], n_total: int) -> pd.DataFrame:
    """Convert regime counts into probabilities."""
    counts = pd.Series(regimes, dtype="object").value_counts().sort_index()
    out = counts.rename_axis("LUE_regime").reset_index(name="count")
    out["probability"] = out["count"] / n_total
    return out


def run_scenario(
    scenario_name: str,
    corr_matrix: np.ndarray,
    means: np.ndarray,
    stds: np.ndarray,
    delta_t: float,
    n_sim: int,
    rng: np.random.Generator,
    output_dir: Path,
    save_raw: bool = True,
) -> dict:
    """Run one City A Monte Carlo scenario and save scenario-level outputs."""
    is_psd, min_eig = is_positive_semidefinite(corr_matrix)
    if not is_psd:
        raise ValueError(
            f"Correlation matrix for {scenario_name} is not positive semi-definite. "
            f"Minimum eigenvalue = {min_eig}."
        )

    cov_matrix = np.outer(stds, stds) * corr_matrix
    draws = rng.multivariate_normal(means, cov_matrix, size=n_sim, check_valid="raise")

    bua1 = np.maximum(draws[:, 0], 1e-8)
    bua2 = np.maximum(draws[:, 1], 1e-8)
    pop1 = np.maximum(draws[:, 2], 1e-8)
    pop2 = np.maximum(draws[:, 3], 1e-8)

    lcr = compute_lcr(bua1, bua2, delta_t)
    pgr = compute_pgr(pop1, pop2, delta_t)
    lcrpgr = compute_lcrpgr(lcr, pgr)
    regimes = classify_regimes(lcr, pgr, lcrpgr)

    df_raw = pd.DataFrame(
        {
            "BUA_t1": bua1,
            "BUA_t2": bua2,
            "Pop_t1": pop1,
            "Pop_t2": pop2,
            "LCR": lcr,
            "PGR": pgr,
            "LCRPGR": lcrpgr,
            "LUE_regime": regimes,
        }
    )

    if save_raw:
        raw_file = output_dir / f"{scenario_name}_simulation_output_{n_sim}.csv"
        df_raw.to_csv(raw_file, index=False)

    indicator_summary = {
        "scenario": scenario_name,
        "n_sim": n_sim,
        "corr_min_eigenvalue": min_eig,
        **summarize_indicator(lcr, "LCR"),
        **summarize_indicator(pgr, "PGR"),
        **summarize_indicator(lcrpgr, "LCRPGR"),
    }

    regime_probabilities = summarize_regime_probabilities(regimes, n_total=n_sim)
    regime_probabilities.insert(0, "scenario", scenario_name)
    regime_probabilities.insert(1, "n_sim", n_sim)

    regime_file = output_dir / f"{scenario_name}_regime_probabilities_{n_sim}.csv"
    regime_probabilities.to_csv(regime_file, index=False)

    return indicator_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the thesis-specific City A SDG 11.3.1 LUE uncertainty propagation experiment."
    )
    parser.add_argument(
        "--n-sim",
        type=int,
        default=444_130,
        help="Number of Monte Carlo simulations per scenario. Default: 444130.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=4480,
        help="Random seed for reproducibility. Default: 4480.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("mc_sim_results"),
        help="Directory where simulation outputs will be saved.",
    )
    parser.add_argument(
        "--include-s4",
        action="store_true",
        help="Include the additional high cross-correlation sensitivity scenario S4.",
    )
    parser.add_argument(
        "--no-raw",
        action="store_true",
        help="Do not save raw Monte Carlo draw files. Summaries and regime probabilities are still saved.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    params = get_city_a_parameters()
    scenarios = get_dependence_scenarios(include_s4=args.include_s4)

    seed_sequence = SeedSequence(args.seed)
    child_seeds = seed_sequence.spawn(len(scenarios))

    summary_rows = []

    for (scenario_name, corr_matrix), child_seed in zip(scenarios.items(), child_seeds):
        print(f"Running {scenario_name} with N={args.n_sim:,}")
        rng = default_rng(child_seed)

        summary = run_scenario(
            scenario_name=scenario_name,
            corr_matrix=corr_matrix,
            means=params["means"],
            stds=params["stds"],
            delta_t=params["delta_t"],
            n_sim=args.n_sim,
            rng=rng,
            output_dir=args.output_dir,
            save_raw=not args.no_raw,
        )
        summary_rows.append(summary)

    summary_df = pd.DataFrame(summary_rows)
    summary_file = args.output_dir / f"city_a_indicator_summary_{args.n_sim}.csv"
    summary_df.to_csv(summary_file, index=False)

    print("All scenarios completed successfully.")
    print(f"Indicator summary saved to: {summary_file}")


if __name__ == "__main__":
    main()
