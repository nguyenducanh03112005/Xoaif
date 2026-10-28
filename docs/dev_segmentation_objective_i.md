# DEV customer segmentation — Objective I

## Scope and method

- Input: `outputs\tables\day2_features_primary.csv` only; one DEV feature snapshot as of `2025-10-22`. The snapshot builder filters source orders to dates strictly before the test boundary.
- No test labels, test behavior, test evaluator, API, synthetic data, or `data/restricted/test` path is read.
- Features: R, F, M. Recency is untransformed; Frequency and non-negative Monetary use `log1p`; each transformed column is independently z-standardized on this DEV snapshot. Thus frequency remains in RFM but is not allowed to dominate by raw scale.
- Customers: 5,169; one-order customers: 87.64%.
- K values: 3, 4, 5; seeds: 13, 42, 87, 2025, 7; silhouette uses a deterministic sample of up to 1,200 rows per seed.

## Silhouette results

| K | Silhouette by seed (13, 42, 87, 2025, 7) | Mean | Min–max |
|---:|---|---:|---:|
| 3 | 0.3986, 0.3827, 0.3837, 0.3958, 0.3899 | 0.3901 | 0.3827–0.3986 |
| 4 | 0.3954, 0.3841, 0.3722, 0.3902, 0.3847 | 0.3853 | 0.3722–0.3954 |
| 5 | 0.4005, 0.3872, 0.3829, 0.3989, 0.3919 | 0.3923 | 0.3829–0.4005 |

## DEV-only cluster profiles

Profiles below use the seed-42 assignments; cluster IDs are arbitrary. Monetary values are reported in the source feature unit (VND).

### K=3

| Cluster | Customers | Median R (days) | Median F (orders) | Median M (VND) | Mean R | Mean F | Mean M (VND) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 2,476 | 383.0000 | 1.0000 | 290,000.0000 | 405.0670 | 1.0024 | 413,871.3744 |
| 1 | 637 | 217.0000 | 2.0000 | 668,000.0000 | 218.9953 | 2.4349 | 1,345,049.3752 |
| 2 | 2,056 | 123.5000 | 1.0000 | 236,725.0000 | 121.4022 | 1.0019 | 323,889.7695 |

### K=4

| Cluster | Customers | Median R (days) | Median F (orders) | Median M (VND) | Mean R | Mean F | Mean M (VND) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1,722 | 425.0000 | 1.0000 | 220,000.0000 | 429.5267 | 1.0035 | 233,214.6614 |
| 1 | 629 | 217.0000 | 2.0000 | 655,000.0000 | 218.8569 | 2.4531 | 1,238,735.3609 |
| 2 | 1,035 | 305.0000 | 1.0000 | 585,000.0000 | 304.9063 | 1.0000 | 887,786.0251 |
| 3 | 1,783 | 113.0000 | 1.0000 | 220,000.0000 | 111.7022 | 1.0022 | 251,172.5272 |

### K=5

| Cluster | Customers | Median R (days) | Median F (orders) | Median M (VND) | Mean R | Mean F | Mean M (VND) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1,705 | 424.0000 | 1.0000 | 220,000.0000 | 429.0205 | 1.0012 | 230,979.4997 |
| 1 | 1,784 | 112.0000 | 1.0000 | 220,000.0000 | 111.4019 | 1.0006 | 253,438.1256 |
| 2 | 499 | 231.0000 | 2.0000 | 550,000.0000 | 235.3587 | 2.0381 | 789,747.6834 |
| 3 | 1,044 | 307.0000 | 1.0000 | 582,000.0000 | 308.5421 | 1.0000 | 882,516.4138 |
| 4 | 137 | 119.0000 | 3.0000 | 1,320,000.0000 | 162.5255 | 3.9416 | 2,818,061.6642 |

## Interpretation

**No business meaning is established by this experiment.** Silhouette measures geometric separation in standardized RFM space, not customer value, actionability, retention, or causal impact. The profiles are descriptive DEV summaries only; without independent business-outcome or stakeholder validation, whether these clusters are actionable is unknown. Do not select or name a production segmentation from silhouette alone.

## Reproduction

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_dev_segmentation_objective_i.py
```
