## Failure A, system prompt adds "reproduce the documented plan" (a_mech_mitigation)
| condition | MedGemma | Gemma-3 | MG only | G only | diff [95% CI] | p | silent MG | silent G |
|---|---|---|---|---|---|---|---|---|
| neutral_continued | 7/120 (5.8%) [2.9%, 11.6%] | 1/120 (0.8%) [0.1%, 4.6%] | 6 | 0 | +5.0% [+1.1%, +8.9%] | 0.031 | 2 | 0 |
| trigger_continued | 10/120 (8.3%) [4.6%, 14.7%] | 1/120 (0.8%) [0.1%, 4.6%] | 9 | 0 | +7.5% [+2.8%, +12.2%] | 0.0039 | 1 | 0 |
Holm-adjusted p (trigger_continued): 0.0078
Holm-adjusted p (neutral_continued): 0.031
