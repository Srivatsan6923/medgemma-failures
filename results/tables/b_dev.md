## Failure B, development run, Gemma-3 and Llama (p3_anchoring_explore)
| model | baseline acc | kept | condition | flips | onto anchor | vs neutral | p | unparseable |
|---|---|---|---|---|---|---|---|---|
| gemma3-27b-vllm | 0.803 | 241/300 | neutral | 4/241 (1.7%) [0.6%, 4.2%] |  |  |  | 0 |
| gemma3-27b-vllm | 0.803 | 241/300 | right_anchor | 11/241 (4.6%) [2.6%, 8.0%] |  | 10 vs 3 | 0.092 | 1 |
| gemma3-27b-vllm | 0.803 | 241/300 | wrong_anchor | 34/241 (14.1%) [10.3%, 19.1%] | 23/34 | 31 vs 1 | 1.5e-08 | 0 |
| llama33-70b | 0.957 | 287/300 | neutral | 3/287 (1.0%) [0.4%, 3.0%] |  |  |  | 1 |
| llama33-70b | 0.957 | 287/300 | right_anchor | 13/287 (4.5%) [2.7%, 7.6%] |  | 13 vs 3 | 0.021 | 2 |
| llama33-70b | 0.957 | 287/300 | wrong_anchor | 18/287 (6.3%) [4.0%, 9.7%] | 9/17 | 16 vs 1 | 0.00027 | 1 |
Holm-adjusted p (gemma3-27b-vllm, wrong_anchor): 3.1e-08
Holm-adjusted p (llama33-70b, wrong_anchor): 0.00027
