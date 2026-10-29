## Failure A, system prompt reworded (1) (a_mech_paraphrase_1)
| condition | MedGemma | Gemma-3 | MG only | G only | diff [95% CI] | OR [95% CI] | p | silent MG | silent G |
|---|---|---|---|---|---|---|---|---|---|
| neutral_continued | 19/120 (15.8%) [10.4%, 23.4%] | 4/120 (3.3%) [1.3%, 8.3%] | 15 | 0 | +12.5% [+6.6%, +18.4%] | inf [3.6, inf] | 6.1e-05 | 0 | 1 |
| trigger_continued | 31/120 (25.8%) [18.8%, 34.3%] | 6/120 (5.0%) [2.3%, 10.5%] | 26 | 1 | +20.8% [+13.2%, +28.5%] | 26.0 [4.3, 1065.9] | 4.2e-07 | 0 | 0 |
Holm-adjusted p (trigger_continued): 8.3e-07
Holm-adjusted p (neutral_continued): 6.1e-05
