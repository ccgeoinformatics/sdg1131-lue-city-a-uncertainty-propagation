# City A Experiment Notes

## Purpose

The City A experiment is an illustrative application of uncertainty propagation for SDG 11.3.1-based LUE assessment. Instead of treating BUA and Pop as fixed values, the experiment represents the four endpoint quantities as uncertain inputs:

```text
BUA_t1, BUA_t2, Pop_t1, Pop_t2
```

These uncertain inputs are jointly sampled under scenario-specific correlation structures, propagated to LCR, PGR, and LCRPGR, and classified into LUE regimes.

## City A baseline values

| Input | Mean | Relative SD | SD |
|---|---:|---:|---:|
| BUA_t1, km<sup>2</sup> | 53.0 | 5% | 2.65 |
| BUA_t2, km<sup>2</sup> | 61.5 | 5% | 3.075 |
| Pop_t1, persons | 320,000 | 10% | 32,000 |
| Pop_t2, persons | 330,000 | 10% | 33,000 |

The time interval is 10 years.

## Dependence scenarios

The correlation matrix is applied to the vector:

```text
[BUA_t1, BUA_t2, Pop_t1, Pop_t2]
```

### S1: Full independence

All off-diagonal correlations are zero.

### S2: Temporal-only dependence

Temporal correlation is introduced within BUA and within Pop:

```text
corr(BUA_t1, BUA_t2) = 0.8
corr(Pop_t1, Pop_t2) = 0.8
```

Cross-variable correlations are zero.

### S3: Temporal and cross-variable dependence

Temporal correlations are retained and moderate cross-variable correlations are introduced:

```text
corr(BUA_t1, BUA_t2) = 0.8
corr(Pop_t1, Pop_t2) = 0.8
cross-variable correlations = 0.5
```

### Optional S4

The optional S4 scenario uses higher cross-variable correlation values. It is included only when `--include-s4` is used, so the main repository workflow remains aligned with the thesis-specific City A experiment.

## Regime probabilities

Each Monte Carlo draw produces one LCR, one PGR, one LCRPGR, and one LUE regime. Regime probabilities are computed as the share of valid Monte Carlo draws assigned to each regime.

These probabilities should be interpreted as conditional on the assumed input uncertainty distributions and dependence scenario.

## LUE regime descriptions

The simulated LUE regime for each Monte Carlo draw is assigned using the R1–R17 regime system. The classification is based on the signs of LCR and PGR, together with the LCRPGR value when PGR is non-zero. The same descriptions are also provided in machine-readable form in [`docs/lue_regime_descriptions.csv`](lue_regime_descriptions.csv).

| Code | LCR | PGR | LCRPGR | Interpretation | General LUE Class | LUE Regime Name |
|---|---|---|---|---|---|---|
| R1 | + | + | 1 | Both built-up area and population grow at proportional rates, indicating balanced expansion in which land consumption remains aligned with population increase and does not exceed what is needed. | Efficient | Efficient (Balanced Growth) |
| R2 | + | + | 0 to 1 | Both built-up area and population grow, but population increases faster than built-up area. This indicates efficient expansion, as additional population is accommodated with comparatively lower built-up consumption, consistent with compact growth or moderate densification. | Efficient | Efficient Built-up Expansion under Faster Population Growth |
| R3 | 0 | + | 0 | Population increases while built-up area remains stable. This indicates highly efficient growth, as additional population is absorbed without further built-up expansion. | Efficient | Efficient Population Growth Without Built-up Expansion |
| R4 | - | + | -1 to 0 | Built-up area contracts while population grows, but population growth exceeds built-up contraction in absolute terms. This indicates efficient population-growth-driven built-up contraction, where urban growth is accommodated through intensified use, redevelopment, or reorganization of the existing built-up footprint rather than outward expansion. | Efficient | Efficient Population Growth with Built-up Reduction |
| R5 | - | + | -1 | Built-up area contraction and population growth occur at similar absolute rates. This indicates a balanced opposite-direction adjustment in which urban development becomes more space-efficient while still accommodating population increase. | Efficient | Efficient Proportional Built-up Reduction and Population Growth |
| R6 | - | + | < -1 | Built-up area contracts faster than the population grows. This may reflect strong redevelopment, consolidation, or spatial compression that reduces built-up extent despite continued population growth. | Efficient | Efficient Built-up Reduction-Dominant Densification |
| R7 | - | 0 | Undefined | Built-up area contracts while population remains stable. This indicates efficient adjustment of the urban footprint, as built-up area is reduced without population loss, suggesting improved spatial efficiency through redevelopment, surplus built-up space removal, or more compact land use. | Efficient | Efficient Built-up Reduction under Stable Population |
| R8 | - | - | > 1 | Both built-up area and population decline, but built-up area contracts faster than population. The reduction in built-up extent more than compensates for population loss and helps limit underutilized urban space. | Efficient | Efficient Built-up Reduction under Population Decline |
| R9 | - | - | 1 | Both built-up area and population decline at similar rates. This indicates efficient proportional contraction, where the reduction in built-up area keeps pace with population decline, helping maintain an appropriate built-up footprint relative to reduced demographic demand. | Efficient | Efficient Proportional Built-up Reduction and Population Decline |
| R10 | - | - | 0 to 1 | Both built-up area and population decline, but population declines faster than built-up contraction. This indicates that built-up reduction is insufficient relative to population loss, leading to inefficient shrinkage and possible underutilization of urban space. | Inefficient | Inefficient Built-up Reduction under Population Decline |
| R11 | 0 | - | 0 | The population declines while the built-up area remains unchanged. This suggests underutilization, vacancy, or persistence of excess built-up area despite reduced population demand. | Inefficient | Inefficient Stable Built-up Area under Population Decline |
| R12 | + | - | -1 to 0 | Built-up area expands while population declines, although population decline exceeds built-up expansion in absolute terms. This still reflects inefficient land use, as built-up areas continue to increase despite declining population demand. | Inefficient | Inefficient Built-up Expansion with Population-Decline Dominance |
| R13 | + | - | -1 | Built-up expansion and population decline occur at the same rate in opposite directions. Although balanced in magnitude, this remains inefficient because land consumption continues to increase despite a declining population. | Inefficient | Inefficient Proportional Built-up Expansion and Population Decline |
| R14 | + | - | < -1 | Built-up area expands faster than population declines. This represents the strongest inefficient expansion under population decline, with clear excess built-up growth relative to demographic need. | Inefficient | Inefficient Built-up Expansion under Population Decline (Expansion-Dominant) |
| R15 | + | 0 | Undefined | Built-up area expands while population remains stable. This indicates demographic-detached expansion and unnecessary built-up growth without a corresponding population increase. | Inefficient | Inefficient Built-up Expansion under Stable Population |
| R16 | + | + | > 1 | Both built-up area and population grow, but built-up expansion exceeds population growth. This indicates inefficient outward growth or sprawl, where land is consumed faster than needed relative to population increase. | Inefficient | Inefficient Built-up Expansion under Slower Population Growth |
| R17 | 0 | 0 | Undefined | No detectable change in land consumption and population over the interval. | Neither efficient nor inefficient | Neutral |

## Notes on interpretation

The regime probabilities produced by the Monte Carlo experiment are not universal probabilities of urban development outcomes. They are conditional probabilities under the specified City A baseline values, marginal uncertainty assumptions, and dependence scenario. Therefore, differences among S1, S2, and S3 should be interpreted as the effect of alternative uncertainty-dependence assumptions on the propagated SDG 11.3.1 LUE assessment.
