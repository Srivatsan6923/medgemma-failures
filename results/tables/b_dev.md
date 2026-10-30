## Failure B, development run (the MedGemma row is a discarded run whose replies were cut off at 32 tokens; see the next table) (p3_anchoring_explore)
| model | baseline acc | kept | condition | flips | onto anchor | vs neutral | OR [95% CI] | p | unparseable |
|---|---|---|---|---|---|---|---|---|---|
| medgemma-27b | 0.127 | 38/300 | neutral | 7/38 (18.4%) [9.2%, 33.4%] |  | 0 vs 0 | inf [0.0, inf] | 1 | 6 |
| medgemma-27b | 0.127 | 38/300 | right_anchor | 9/38 (23.7%) [13.0%, 39.2%] |  | 7 vs 5 | 1.4 [0.4, 5.6] | 0.77 | 8 |
| medgemma-27b | 0.127 | 38/300 | wrong_anchor | 9/38 (23.7%) [13.0%, 39.2%] | 1/2 | 6 vs 4 | 1.5 [0.4, 7.2] | 0.75 | 7 |
| gemma3-27b-vllm | 0.803 | 241/300 | neutral | 4/241 (1.7%) [0.6%, 4.2%] |  | 0 vs 0 | inf [0.0, inf] | 1 | 0 |
| gemma3-27b-vllm | 0.803 | 241/300 | right_anchor | 11/241 (4.6%) [2.6%, 8.0%] |  | 10 vs 3 | 3.3 [0.9, 18.8] | 0.092 | 1 |
| gemma3-27b-vllm | 0.803 | 241/300 | wrong_anchor | 34/241 (14.1%) [10.3%, 19.1%] | 23/34 | 31 vs 1 | 31.0 [5.2, 1263.4] | 1.5e-08 | 0 |
| llama33-70b | 0.957 | 287/300 | neutral | 3/287 (1.0%) [0.4%, 3.0%] |  | 0 vs 0 | inf [0.0, inf] | 1 | 1 |
| llama33-70b | 0.957 | 287/300 | right_anchor | 13/287 (4.5%) [2.7%, 7.6%] |  | 13 vs 3 | 4.3 [1.2, 23.7] | 0.021 | 2 |
| llama33-70b | 0.957 | 287/300 | wrong_anchor | 18/287 (6.3%) [4.0%, 9.7%] | 9/17 | 16 vs 1 | 16.0 [2.5, 671.0] | 0.00027 | 1 |
Holm-adjusted p (medgemma-27b, wrong_anchor): 0.75
Holm-adjusted p (gemma3-27b-vllm, wrong_anchor): 4.6e-08
Holm-adjusted p (llama33-70b, wrong_anchor): 0.00055
