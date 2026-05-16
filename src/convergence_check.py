#!/usr/bin/env python3
"""
Monte Carlo convergence check for the City A SDG 11.3.1 LUE experiment.

The script reads raw simulation CSVs produced by city_a_monte_carlo.py and
evaluates whether indicator summaries stabilize as N increases. It uses prefix
subsets of the same large simulation, so the convergence check is reproducible
and does not require rerunning new simulations for every candidate N.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def make_geometric_n_list(nmax: int, ratio: float, small: list[int]) -> list[int]:
    """Build a sorted unique N list up to nmax using small values plus a geometric progression."""
    ns = set(int(x) for x in small if x >= 2 and x <= nmax)

    if ns:
        n = max(max(ns), 10_000)
    else:
        n = min(10_000, nmax)

    while n < nmax:
        ns.add(int(n))
        n = int(np.ceil(n * ratio))

    ns.add(int(nmax))
    return sorted(ns)


def summarize_prefix(df: pd.DataFrame, col: str, q_lo: float = 0.025, q_hi: float = 0.975) -> dict:
    """Summarize a prefix subset for one indicator."""
    s = df[col].replace([np.inf, -np.inf], np.nan).dropna()
    q2_5 = float(s.quantile(q_lo))
    q97_5 = float(s.quantile(q_hi))
    return {
        "median": float(s.median()),
        "q2_5": q2_5,
        "q97_5": q97_5,
        "width_95": q97_5 - q2_5,
    }


def rel_change(curr: float, prev: float, eps: float) -> float:
    """Compute relative change with an epsilon safeguard."""
    denom = max(abs(curr), eps)
    return float(abs(curr - prev) / denom)


def step_pass(
    prev_stats: dict,
    curr_stats: dict,
    tol_median_rel: float,
    tol_q_rel: float,
    tol_median_abs_frac: float,
    tol_q_abs_frac: float,
    eps_frac: float,
) -> dict:
    """Check if one sequential N step passes the plateau/stability criteria."""
    width = curr_stats["width_95"]
    eps = eps_frac * width

    d_med = abs(curr_stats["median"] - prev_stats["median"])
    d_qlo = abs(curr_stats["q2_5"] - prev_stats["q2_5"])
    d_qhi = abs(curr_stats["q97_5"] - prev_stats["q97_5"])

    r_med = rel_change(curr_stats["median"], prev_stats["median"], eps)
    r_qlo = rel_change(curr_stats["q2_5"], prev_stats["q2_5"], eps)
    r_qhi = rel_change(curr_stats["q97_5"], prev_stats["q97_5"], eps)

    abs_thr_median = tol_median_abs_frac * width
    abs_thr_q = tol_q_abs_frac * width

    pass_median = (r_med <= tol_median_rel) and (d_med <= abs_thr_median)
    pass_qlo = (r_qlo <= tol_q_rel) and (d_qlo <= abs_thr_q)
    pass_qhi = (r_qhi <= tol_q_rel) and (d_qhi <= abs_thr_q)

    return {
        "eps_used": eps,
        "delta_median": d_med,
        "delta_q2_5": d_qlo,
        "delta_q97_5": d_qhi,
        "rel_change_median": r_med,
        "rel_change_q2_5": r_qlo,
        "rel_change_q97_5": r_qhi,
        "abs_thr_median": abs_thr_median,
        "abs_thr_q": abs_thr_q,
        "pass_median": pass_median,
        "pass_q2_5": pass_qlo,
        "pass_q97_5": pass_qhi,
        "pass_step": pass_median and pass_qlo and pass_qhi,
    }


def earliest_plateau_n(step_df: pd.DataFrame, required_consecutive: int) -> int | None:
    """Return the earliest N where the plateau rule is met."""
    passes = step_df["pass_step"].to_numpy(dtype=bool)
    ns = step_df["N_curr"].to_numpy(dtype=int)

    run = 0
    for i, ok in enumerate(passes):
        run = run + 1 if ok else 0
        if run >= required_consecutive:
            return int(ns[i])
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Monte Carlo convergence using prefix subsets of City A simulation outputs."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("mc_sim_results"),
        help="Directory containing raw simulation CSVs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("mc_sim_results_convergence"),
        help="Directory for convergence outputs.",
    )
    parser.add_argument(
        "--nmax-target",
        type=int,
        default=444_130,
        help="Maximum N to evaluate. Capped automatically by available rows.",
    )
    parser.add_argument(
        "--geom-ratio",
        type=float,
        default=1.25,
        help="Geometric increase ratio for N schedule.",
    )
    parser.add_argument(
        "--required-consecutive",
        type=int,
        default=2,
        help="Number of consecutive passing steps required to declare plateau.",
    )
    parser.add_argument(
        "--file-glob",
        type=str,
        default="*_simulation_output_*.csv",
        help="Glob pattern for raw simulation CSVs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    metrics = ["LCR", "PGR", "LCRPGR"]
    small_n = [100, 500, 1_000, 2_000, 5_000, 10_000]

    tol_median_rel = 0.005
    tol_q_rel = 0.01
    tol_median_abs_frac = 0.005
    tol_q_abs_frac = 0.01
    eps_frac = 0.01

    csv_files = sorted(args.input_dir.glob(args.file_glob))
    if not csv_files:
        raise FileNotFoundError(
            f"No simulation CSVs found in {args.input_dir.resolve()} using glob: {args.file_glob}"
        )

    all_summary_tables = []
    all_step_tables = []
    all_selection_tables = []

    for file_path in csv_files:
        print(f"Reading: {file_path.name}")
        df_full = pd.read_csv(file_path)
        nmax_actual = len(df_full)
        nmax = min(args.nmax_target, nmax_actual)
        n_list = make_geometric_n_list(nmax=nmax, ratio=args.geom_ratio, small=small_n)

        scenario_short = file_path.name.split("_simulation_output_")[0]

        rows_summary = []
        prefix_stats = {metric: {} for metric in metrics}

        for n in n_list:
            df_n = df_full.iloc[:n]
            for metric in metrics:
                stats = summarize_prefix(df_n, metric)
                prefix_stats[metric][n] = stats
                rows_summary.append(
                    {
                        "scenario": file_path.stem,
                        "scenario_short": scenario_short,
                        "N": n,
                        "metric": metric,
                        "median": stats["median"],
                        "q2_5": stats["q2_5"],
                        "q97_5": stats["q97_5"],
                        "width_95": stats["width_95"],
                        "geom_ratio": args.geom_ratio,
                        "nmax_used": nmax,
                    }
                )

        df_summary = pd.DataFrame(rows_summary).sort_values(["scenario_short", "metric", "N"])
        out_summary = args.output_dir / f"{file_path.stem}_prefix_summaries.csv"
        df_summary.to_csv(out_summary, index=False)

        rows_steps = []
        for metric in metrics:
            for i in range(1, len(n_list)):
                n_prev = n_list[i - 1]
                n_curr = n_list[i]
                prev_stats = prefix_stats[metric][n_prev]
                curr_stats = prefix_stats[metric][n_curr]

                step = step_pass(
                    prev_stats=prev_stats,
                    curr_stats=curr_stats,
                    tol_median_rel=tol_median_rel,
                    tol_q_rel=tol_q_rel,
                    tol_median_abs_frac=tol_median_abs_frac,
                    tol_q_abs_frac=tol_q_abs_frac,
                    eps_frac=eps_frac,
                )

                rows_steps.append(
                    {
                        "scenario": file_path.stem,
                        "scenario_short": scenario_short,
                        "metric": metric,
                        "N_prev": n_prev,
                        "N_curr": n_curr,
                        "median_prev": prev_stats["median"],
                        "median_curr": curr_stats["median"],
                        "q2_5_prev": prev_stats["q2_5"],
                        "q2_5_curr": curr_stats["q2_5"],
                        "q97_5_prev": prev_stats["q97_5"],
                        "q97_5_curr": curr_stats["q97_5"],
                        "width_95_curr": curr_stats["width_95"],
                        "geom_ratio": args.geom_ratio,
                        **step,
                    }
                )

        df_steps = pd.DataFrame(rows_steps).sort_values(["scenario_short", "metric", "N_curr"])
        out_steps = args.output_dir / f"{file_path.stem}_sequential_diffs.csv"
        df_steps.to_csv(out_steps, index=False)

        rows_selection = []
        for metric in metrics:
            d_metric = df_steps[df_steps["metric"] == metric].sort_values("N_curr")
            n_plateau = earliest_plateau_n(d_metric, args.required_consecutive)
            rows_selection.append(
                {
                    "scenario": file_path.stem,
                    "scenario_short": scenario_short,
                    "metric": metric,
                    "required_consecutive_steps": args.required_consecutive,
                    "N_plateau": n_plateau,
                    "geom_ratio": args.geom_ratio,
                    "nmax_used": nmax,
                }
            )

        df_selection = pd.DataFrame(rows_selection)
        if df_selection["N_plateau"].notna().all():
            df_selection["N_plateau_overall_scenario"] = int(df_selection["N_plateau"].max())
        else:
            df_selection["N_plateau_overall_scenario"] = np.nan

        out_selection = args.output_dir / f"{file_path.stem}_plateau_N_selection.csv"
        df_selection.to_csv(out_selection, index=False)

        all_summary_tables.append(df_summary)
        all_step_tables.append(df_steps)
        all_selection_tables.append(df_selection)

    combined_summary = pd.concat(all_summary_tables, ignore_index=True)
    combined_steps = pd.concat(all_step_tables, ignore_index=True)
    combined_selection = pd.concat(all_selection_tables, ignore_index=True)

    combined_summary.to_csv(args.output_dir / "ALL_prefix_summaries.csv", index=False)
    combined_steps.to_csv(args.output_dir / "ALL_sequential_diffs.csv", index=False)
    combined_selection.to_csv(args.output_dir / "ALL_plateau_N_selection.csv", index=False)

    print("Convergence check completed.")
    print(f"Combined N selection saved to: {args.output_dir / 'ALL_plateau_N_selection.csv'}")


if __name__ == "__main__":
    main()
