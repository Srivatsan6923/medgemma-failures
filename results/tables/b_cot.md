## Failure B, step-by-step reasoning (b_mech_cot)
| model | baseline acc | kept | condition | flips | onto anchor | vs neutral | OR [95% CI] | p | unparseable |
|---|---|---|---|---|---|---|---|---|---|
| gemma3-27b-vllm | 0.850 | 255/300 | neutral | 9/255 (3.5%) [1.9%, 6.6%] |  | 0 vs 0 | inf [0.0, inf] | 1 | 0 |
| gemma3-27b-vllm | 0.850 | 255/300 | wrong_anchor | 36/255 (14.1%) [10.4%, 18.9%] | 23/36 | 32 vs 5 | 6.4 [2.5, 21.0] | 7.4e-06 | 0 |
| llama33-70b | 0.977 | 293/300 | neutral | 4/293 (1.4%) [0.5%, 3.5%] |  | 0 vs 0 | inf [0.0, inf] | 1 | 0 |
| llama33-70b | 0.977 | 293/300 | wrong_anchor | 10/293 (3.4%) [1.9%, 6.2%] | 6/10 | 10 vs 4 | 2.5 [0.7, 10.9] | 0.18 | 0 |
Holm-adjusted p (gemma3-27b-vllm, wrong_anchor): 1.5e-05
Holm-adjusted p (llama33-70b, wrong_anchor): 0.18
