## Failure B, confirmation (pre-registered) (b_confirm_anchoring)
| model | baseline acc | kept | condition | flips | onto anchor | vs neutral | OR [95% CI] | p |
|---|---|---|---|---|---|---|---|---|
| medgemma-27b | 0.948 | 379/400 | neutral | 10/379 (2.6%) [1.4%, 4.8%] |  | 0 vs 0 | inf [0.0, inf] | 1 |
| medgemma-27b | 0.948 | 379/400 | right_anchor | 10/379 (2.6%) [1.4%, 4.8%] |  | 8 vs 8 | 1.0 [0.3, 3.1] | 1 |
| medgemma-27b | 0.948 | 379/400 | wrong_anchor | 29/379 (7.7%) [5.4%, 10.8%] | 13/28 | 23 vs 4 | 5.8 [2.0, 22.9] | 0.00031 |
| gemma3-27b-vllm | 0.785 | 314/400 | neutral | 10/314 (3.2%) [1.7%, 5.8%] |  | 0 vs 0 | inf [0.0, inf] | 1 |
| gemma3-27b-vllm | 0.785 | 314/400 | right_anchor | 13/314 (4.1%) [2.4%, 7.0%] |  | 9 vs 6 | 1.5 [0.5, 5.1] | 0.61 |
| gemma3-27b-vllm | 0.785 | 314/400 | wrong_anchor | 44/314 (14.0%) [10.6%, 18.3%] | 33/44 | 36 vs 2 | 18.0 [4.6, 154.3] | 5.4e-09 |
| llama33-70b | 0.953 | 381/400 | neutral | 7/381 (1.8%) [0.9%, 3.7%] |  | 0 vs 0 | inf [0.0, inf] | 1 |
| llama33-70b | 0.953 | 381/400 | right_anchor | 22/381 (5.8%) [3.8%, 8.6%] |  | 21 vs 6 | 3.5 [1.4, 10.6] | 0.0059 |
| llama33-70b | 0.953 | 381/400 | wrong_anchor | 25/381 (6.6%) [4.5%, 9.5%] | 16/25 | 21 vs 3 | 7.0 [2.1, 36.7] | 0.00028 |
Holm-adjusted p (medgemma-27b, wrong_anchor): 0.00055
Holm-adjusted p (gemma3-27b-vllm, wrong_anchor): 1.6e-08
Holm-adjusted p (llama33-70b, wrong_anchor): 0.00055
