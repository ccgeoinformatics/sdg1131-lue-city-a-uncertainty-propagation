# SDG 11.3.1 LUE City A Uncertainty Propagation Experiment

This repository contains the **City A** experiment for uncertainty-aware SDG 11.3.1 land-use efficiency (LUE) assessment, as described in the on-going PhD Thesis "Probabilistic and Multidimensional Assessment of Urban Land-Use Efficiency from Earth Observation Data" by Jojene R. Santillan (Leibniz University Hannover, 2026). It propagates uncertainty in built-up area (BUA) and population (Pop) to the derived indicators **LCR**, **PGR**, and **LCRPGR**, and then summarizes probabilistic LUE regime membership using Monte Carlo simulation.

The repository is intended to make the City A experiment reproducible, including the convergence check used to select a suitable number of Monte Carlo simulations.

## Repository structure

```text
sdg113-lue-city-a-experiment/
├── src/
│   ├── city_a_monte_carlo.py
│   ├── convergence_check.py
│   └── lue_regime_classifier.py
├── docs/
│   ├── city_a_experiment_notes.md
│   └── lue_regime_descriptions.csv
├── outputs/
│   └── .gitkeep
├── mc_sim_results/
│   └── .gitkeep
├── mc_sim_results_convergence/
│   └── .gitkeep
├── .gitignore
├── CITATION.cff
├── LICENSE
├── README.md
└── requirements.txt
```


## Documentation

Additional experiment documentation is provided in `docs/city_a_experiment_notes.md`. This file now includes the R1–R17 LUE regime descriptions used to interpret Monte Carlo regime probabilities. A machine-readable version is available in `docs/lue_regime_descriptions.csv`.

## City A experiment

The default parameterization follows the City A illustrative experiment used in the thesis:

| Quantity | Value |
|---|---:|
| BUA at t1 | 53.0 |
| BUA at t2 | 61.5 |
| Population at t1 | 320,000 |
| Population at t2 | 330,000 |
| Time interval | 10 years |
| BUA relative standard deviation | 5% |
| Population relative standard deviation | 10% |

The input vector is:

```text
[BUA_t1, BUA_t2, Pop_t1, Pop_t2]
```

The main thesis dependence scenarios are:

| Scenario | Description |
|---|---|
| `S1_full_independence` | BUA and Pop uncertainty are independent across variables and time. |
| `S2_temporal_only` | Temporal correlation is introduced within BUA and within Pop. |
| `S3_temporal_cross` | Temporal correlation and moderate cross-variable correlation are introduced. |

An additional sensitivity scenario, `S4_temporal_cross_higher_rho`, can be included using the `--include-s4` option.

## Indicators

The experiment computes:

```text
LCR = ((BUA_t2 - BUA_t1) / BUA_t1) / T
```

```text
PGR = (ln(Pop_t2) - ln(Pop_t1)) / T
```

```text
LCRPGR = LCR / PGR
```

LCR and PGR are computed in decimal units per year. LCRPGR is dimensionless.

## Installation

Create and activate a Python environment, then install the required packages:

```bash
pip install -r requirements.txt
```

The scripts require Python 3.10 or later.

## Run the Monte Carlo simulation

From the repository root, run:

```bash
python src/city_a_monte_carlo.py
```

By default, this runs `444,130` Monte Carlo simulations per scenario for the three main thesis scenarios.

For a quick test:

```bash
python src/city_a_monte_carlo.py --n-sim 1000
```

To include the additional high cross-correlation sensitivity scenario:

```bash
python src/city_a_monte_carlo.py --include-s4
```

To change the output directory:

```bash
python src/city_a_monte_carlo.py --output-dir mc_sim_results
```

To save only summaries and regime probabilities, without raw Monte Carlo draws:

```bash
python src/city_a_monte_carlo.py --no-raw
```

## Main outputs

The Monte Carlo script writes the following files to `mc_sim_results/` by default:

```text
S1_full_independence_simulation_output_<N>.csv
S2_temporal_only_simulation_output_<N>.csv
S3_temporal_cross_simulation_output_<N>.csv
S1_full_independence_regime_probabilities_<N>.csv
S2_temporal_only_regime_probabilities_<N>.csv
S3_temporal_cross_regime_probabilities_<N>.csv
city_a_indicator_summary_<N>.csv
```

The raw simulation output contains BUA, Pop, LCR, PGR, LCRPGR, and the simulated LUE regime for each Monte Carlo draw.

## Run the convergence check

After generating raw simulation CSVs, run:

```bash
python src/convergence_check.py
```

This reads files from `mc_sim_results/` and writes convergence outputs to `mc_sim_results_convergence/`.

The convergence check evaluates the stability of the median and 95% interval bounds of LCR, PGR, and LCRPGR using increasing prefix subsets of the raw Monte Carlo draws.

The combined output of interest is:

```text
mc_sim_results_convergence/ALL_plateau_N_selection.csv
```

This file reports the plateau N for each indicator and scenario. The scenario-level recommended N is the maximum plateau N across the three indicators.

## Reproducibility

The default random seed is:

```text
4480
```

A dedicated random generator is spawned for each scenario, so results are reproducible given the same seed, scenario set, and number of simulations.

## Notes on generated files

Large Monte Carlo CSVs are ignored by Git through `.gitignore`. This keeps the repository lightweight. To archive final outputs, consider using Zenodo, OSF, or GitHub Releases instead of committing large CSV files directly.


