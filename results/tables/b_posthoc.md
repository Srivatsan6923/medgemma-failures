## Failure B, certainty, source and no-source lines on the confirmation items (post-hoc) (b_posthoc_certainty)
| model | baseline acc | kept | condition | flips | onto anchor | vs neutral | OR [95% CI] | p |
|---|---|---|---|---|---|---|---|---|
| medgemma-27b | 0.948 | 379/400 | neutral | 10/379 (2.6%) [1.4%, 4.8%] |  | 0 vs 0 | inf [0.0, inf] | 1 |
| medgemma-27b | 0.948 | 379/400 | wrong_anchor | 29/379 (7.7%) [5.4%, 10.8%] | 13/28 | 23 vs 4 | 5.8 [2.0, 22.9] | 0.00031 |
| medgemma-27b | 0.948 | 379/400 | wrong_attending | 128/379 (33.8%) [29.2%, 38.7%] | 114/120 | 121 vs 3 | 40.3 [13.5, 198.3] | 3e-32 |
| medgemma-27b | 0.948 | 379/400 | wrong_attending_suspects | 41/379 (10.8%) [8.1%, 14.3%] | 31/39 | 34 vs 3 | 11.3 [3.6, 57.7] | 1.2e-07 |
| medgemma-27b | 0.948 | 379/400 | wrong_bare | 65/379 (17.2%) [13.7%, 21.3%] | 58/62 | 58 vs 3 | 19.3 [6.3, 96.5] | 3.3e-14 |
| medgemma-27b | 0.948 | 379/400 | wrong_nurse_confirmed | 72/379 (19.0%) [15.4%, 23.3%] | 63/68 | 66 vs 4 | 16.5 [6.1, 62.3] | 1.7e-15 |
| medgemma-27b | 0.948 | 379/400 | wrong_nurse_suspects | 35/379 (9.2%) [6.7%, 12.6%] | 20/27 | 29 vs 4 | 7.2 [2.5, 28.4] | 1.1e-05 |
| gemma3-27b-vllm | 0.785 | 314/400 | neutral | 10/314 (3.2%) [1.7%, 5.8%] |  | 0 vs 0 | inf [0.0, inf] | 1 |
| gemma3-27b-vllm | 0.785 | 314/400 | wrong_anchor | 44/314 (14.0%) [10.6%, 18.3%] | 33/44 | 36 vs 2 | 18.0 [4.6, 154.3] | 5.4e-09 |
| gemma3-27b-vllm | 0.785 | 314/400 | wrong_attending | 130/314 (41.4%) [36.1%, 46.9%] | 122/130 | 120 vs 0 | inf [32.0, inf] | 1.5e-36 |
| gemma3-27b-vllm | 0.785 | 314/400 | wrong_attending_suspects | 107/314 (34.1%) [29.1%, 39.5%] | 94/106 | 97 vs 0 | inf [25.8, inf] | 1.3e-29 |
| gemma3-27b-vllm | 0.785 | 314/400 | wrong_bare | 118/314 (37.6%) [32.4%, 43.1%] | 108/117 | 109 vs 1 | 109.0 [19.2, 4344.3] | 1.7e-31 |
| gemma3-27b-vllm | 0.785 | 314/400 | wrong_nurse_confirmed | 96/314 (30.6%) [25.7%, 35.9%] | 86/96 | 87 vs 1 | 87.0 [15.2, 3475.3] | 5.8e-25 |
| gemma3-27b-vllm | 0.785 | 314/400 | wrong_nurse_suspects | 85/314 (27.1%) [22.5%, 32.2%] | 71/85 | 75 vs 0 | inf [19.8, inf] | 5.3e-23 |
| llama33-70b | 0.953 | 381/400 | neutral | 7/381 (1.8%) [0.9%, 3.7%] |  | 0 vs 0 | inf [0.0, inf] | 1 |
| llama33-70b | 0.953 | 381/400 | wrong_anchor | 25/381 (6.6%) [4.5%, 9.5%] | 16/25 | 21 vs 3 | 7.0 [2.1, 36.7] | 0.00028 |
| llama33-70b | 0.953 | 381/400 | wrong_attending | 141/381 (37.0%) [32.3%, 42.0%] | 129/138 | 134 vs 0 | inf [35.8, inf] | 9.2e-41 |
| llama33-70b | 0.953 | 381/400 | wrong_attending_suspects | 68/381 (17.8%) [14.3%, 22.0%] | 56/66 | 61 vs 0 | inf [16.0, inf] | 8.7e-19 |
| llama33-70b | 0.953 | 381/400 | wrong_bare | 113/381 (29.7%) [25.3%, 34.4%] | 104/112 | 106 vs 0 | inf [28.2, inf] | 2.5e-32 |
| llama33-70b | 0.953 | 381/400 | wrong_nurse_confirmed | 100/381 (26.2%) [22.1%, 30.9%] | 88/98 | 93 vs 0 | inf [24.7, inf] | 2e-28 |
| llama33-70b | 0.953 | 381/400 | wrong_nurse_suspects | 49/381 (12.9%) [9.9%, 16.6%] | 38/48 | 42 vs 0 | inf [10.9, inf] | 4.5e-13 |
Holm-adjusted p (medgemma-27b, wrong_anchor): 0.00055
Holm-adjusted p (gemma3-27b-vllm, wrong_anchor): 1.6e-08
Holm-adjusted p (llama33-70b, wrong_anchor): 0.00055
