# New and repaired ScrapeBench experiments

InstantID generated cells: 122/72.

## InstantID multi-identity aggregate

| Method | Tier | IDs | Conditional ID | Detection | Unconditional ID | Success | 95% CI (uncond.) |
|---|---:|---:|---:|---:|---:|---:|---:|
| clean | T0 | 6 | 0.514 | 80.0% | 0.406 | 78.3% | [0.341, 0.473] |
| clean | J85 | 6 | 0.541 | 76.7% | 0.413 | 76.7% | [0.313, 0.508] |
| clean | T2 | 6 | 0.547 | 61.7% | 0.336 | 61.7% | [0.247, 0.436] |
| clean | T5 | 6 | 0.256 | 50.0% | 0.139 | 26.7% | [0.065, 0.224] |
| fsmg | T0 | 6 | 0.276 | 63.3% | 0.178 | 28.3% | [0.112, 0.253] |
| fsmg | J85 | 6 | 0.262 | 65.0% | 0.182 | 21.7% | [0.103, 0.266] |
| fsmg | T2 | 6 | 0.277 | 66.7% | 0.194 | 35.0% | [0.115, 0.272] |
| fsmg | T5 | 6 | 0.101 | 6.7% | 0.007 | 0.0% | [0.000, 0.018] |
| fsmgj | T0 | 6 | 0.286 | 55.0% | 0.171 | 33.3% | [0.094, 0.254] |
| fsmgj | J85 | 6 | 0.277 | 51.7% | 0.153 | 26.7% | [0.084, 0.233] |
| fsmgj | T2 | 6 | 0.291 | 60.0% | 0.178 | 31.7% | [0.111, 0.256] |
| fsmgj | T5 | 6 | 0.115 | 3.3% | 0.004 | 0.0% | [0.000, 0.012] |

## Conditional-on-detection paired gaps and retention

| Method | Tier | Paired IDs | clean-protected gap | RR vs T0 |
|---|---:|---:|---:|---:|
| fsmg | T0 | 6 | 0.239 | 1.000 |
| fsmg | J85 | 6 | 0.279 | 1.170 |
| fsmg | T2 | 6 | 0.270 | 1.131 |
| fsmg | T5 | 2 | 0.129 | 0.540 |
| fsmgj | T0 | 6 | 0.228 | 1.000 |
| fsmgj | J85 | 6 | 0.264 | 1.155 |
| fsmgj | T2 | 6 | 0.256 | 1.124 |
| fsmgj | T5 | 1 | -0.010 | -0.043 |

## Detection-failure-zero paired gaps and retention

| Method | Tier | Paired IDs | clean-protected gap | RR vs T0 |
|---|---:|---:|---:|---:|
| fsmg | T0 | 6 | 0.228 | 1.000 |
| fsmg | J85 | 6 | 0.232 | 1.018 |
| fsmg | T2 | 6 | 0.142 | 0.624 |
| fsmg | T5 | 6 | 0.132 | 0.578 |
| fsmgj | T0 | 6 | 0.235 | 1.000 |
| fsmgj | J85 | 6 | 0.260 | 1.108 |
| fsmgj | T2 | 6 | 0.159 | 0.677 |
| fsmgj | T5 | 6 | 0.135 | 0.574 |

## Comparison with the paper's one-identity InstantID probe

| Method | Tier | Original | New conditional | Difference |
|---|---:|---:|---:|---:|
| clean | T0 | 0.460 | 0.514 | 0.054 |
| clean | J85 | 0.460 | 0.541 | 0.081 |
| clean | T2 | 0.430 | 0.547 | 0.117 |
| fsmg | T0 | 0.360 | 0.276 | -0.084 |
| fsmg | J85 | 0.330 | 0.262 | -0.068 |
| fsmg | T2 | 0.230 | 0.277 | 0.047 |

## Repaired T3

| Method | IDs | Conditional ID | Detection | Unconditional ID | Success |
|---|---:|---:|---:|---:|---:|
| clean | 6 | 0.376 | 81.7% | 0.308 | 61.7% |
| fsmg | 6 | 0.329 | 76.7% | 0.254 | 43.3% |
| fsmgj | 6 | 0.328 | 78.3% | 0.258 | 45.0% |

## Repaired Stage C

| Condition | IDs | Original invalid mean | New conditional | Detection | Unconditional | Success |
|---|---:|---:|---:|---:|---:|---:|
| mix20 | 6 | 0.042 | 0.097 | 60.0% | 0.059 | 0.0% |
| mix50 | 6 | 0.022 | 0.094 | 63.3% | 0.062 | 5.0% |
| purify50 | 6 | 0.078 | 0.063 | 65.0% | 0.045 | 0.0% |
