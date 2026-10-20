# Constant learning rates per technology: Carlino et al. (2025)

A reanalysis of the data behind:

> Carlino, A., Wongel, A., Duan, L., Virgüez, E., Davis, S. J., Edwards, M. R., & Caldeira, K.
> (2025). Variability of technology learning rates. *Advances in Applied Energy*, 20, 100252.
> https://doi.org/10.1016/j.adapen.2025.100252

It supports the "Additional analysis" section of
<https://ciunit.org/publications/carlino-2025-technology-learning-rates.html>. The paper does
not report these results.

## Question

The paper's distribution of learning rates (Supplementary Table 2: mean learning exponent
β = −0.33, standard deviation 0.35) pools every segment of its piecewise fits, and counts
each segment equally however short. What do the same data give if each technology is
instead fitted with one constant learning rate over its whole record? And does it matter
whether each technology counts equally or in proportion to the length of its record?

## Method

For each of the 87 technologies, `scripts/learning_rates.py` fits Wright's model (the
paper's Equations 1 to 3),

    log(C) = log(α) + β log(P),    learning rate = 100 (1 − 2^β),

by ordinary least squares on log unit cost *C* against log cumulative production *P*, using
every point in the record. The learning rate is the percentage cost decline per doubling of
cumulative production.

The β values are then summarized four ways: all 87 technologies, or without
`Nuclear_Electricity` (whose cost rose with production, β = +1.03); each either unweighted
(each technology counts once) or weighted by record length. Record length is
log₁₀(last cumulative production) − log₁₀(first), which is proportional to the number of
doublings a record spans.

The "median" learning rate is the mean β converted to a rate, which is the median if β is
normally distributed. The unweighted standard deviation uses n − 1; the weighted one is
the population form.

## Data

`data/input/ExpCurves.csv` is the file `ExpCurves.csv` from the paper's Zenodo record, the
archive of the authors' code release v4.0:

- Zenodo: <https://doi.org/10.5281/zenodo.17179225>, file
  `carnegie/clab_experience_curve-v4.0.zip`, path
  `carnegie-clab_experience_curve-9964e42/ExpCurves.csv`
- MD5 `0e662032b72c644073d02f7d92d28829`, 1,707 rows, 87 technologies from the Performance
  Curve Database

`data/input/LICENSE` is the authors' MIT licence (Copyright 2024 Carnegie Institution for
Science), under which the file is redistributed here.

**Use this version, not an earlier one.** The authors' first release, v1.0 (2023), has an
`ExpCurves.csv` with different cumulative-production values, and it gives noticeably
different learning rates: a median of 22.7% instead of 17.9%, unweighted.

## Outputs

| File | Contents |
| --- | --- |
| `data/output/learning_rates_by_tech.csv` | β, learning rate, number of points, and record length for each technology |
| `data/output/learning_rate_summary.csv` | the four summaries quoted on the publication page |
| `data/output/learning_rates_vs_production_range.png` | β and learning rate against record length |

## Reproduce

```bash
pip install numpy matplotlib
python scripts/learning_rates.py
```

Run on 2026-10-20 with Python 3.12, NumPy 2.5.4, and Matplotlib 3.11.2.
