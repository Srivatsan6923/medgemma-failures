## Failure B, source of the wrong diagnosis (b_mech_authority)
| model | baseline acc | kept | condition | flips | onto anchor | vs neutral | p | unparseable |
|---|---|---|---|---|---|---|---|---|
| medgemma-27b | 0.947 | 284/300 | neutral | 5/284 (1.8%) [0.8%, 4.1%] |  |  |  | 0 |
| medgemma-27b | 0.947 | 284/300 | wrong_ai | 20/284 (7.0%) [4.6%, 10.6%] | 10/18 | 17 vs 2 | 0.00073 | 2 |
| medgemma-27b | 0.947 | 284/300 | wrong_anchor | 24/284 (8.5%) [5.7%, 12.3%] | 13/19 | 20 vs 1 | 2.1e-05 | 5 |
| medgemma-27b | 0.947 | 284/300 | wrong_attending | 85/284 (29.9%) [24.9%, 35.5%] | 81/85 | 80 vs 0 | 1.7e-24 | 0 |
| medgemma-27b | 0.947 | 284/300 | wrong_nurse | 37/284 (13.0%) [9.6%, 17.4%] | 27/33 | 34 vs 2 | 1.9e-08 | 4 |
| medgemma-27b | 0.947 | 284/300 | wrong_patient | 13/284 (4.6%) [2.7%, 7.7%] | 3/8 | 11 vs 3 | 0.057 | 5 |
| gemma3-27b-vllm | 0.807 | 242/300 | neutral | 4/242 (1.7%) [0.6%, 4.2%] |  |  |  | 0 |
| gemma3-27b-vllm | 0.807 | 242/300 | wrong_ai | 34/242 (14.0%) [10.2%, 19.0%] | 22/34 | 31 vs 1 | 1.5e-08 | 0 |
| gemma3-27b-vllm | 0.807 | 242/300 | wrong_anchor | 35/242 (14.5%) [10.6%, 19.4%] | 23/35 | 32 vs 1 | 7.9e-09 | 0 |
| gemma3-27b-vllm | 0.807 | 242/300 | wrong_attending | 96/242 (39.7%) [33.7%, 45.9%] | 87/96 | 94 vs 2 | 1.2e-25 | 0 |
| gemma3-27b-vllm | 0.807 | 242/300 | wrong_nurse | 63/242 (26.0%) [20.9%, 31.9%] | 50/63 | 61 vs 2 | 4.4e-16 | 0 |
| gemma3-27b-vllm | 0.807 | 242/300 | wrong_patient | 21/242 (8.7%) [5.7%, 12.9%] | 11/21 | 19 vs 2 | 0.00022 | 0 |
| llama33-70b | 0.950 | 285/300 | neutral | 3/285 (1.1%) [0.4%, 3.0%] |  |  |  | 0 |
| llama33-70b | 0.950 | 285/300 | wrong_ai | 20/285 (7.0%) [4.6%, 10.6%] | 12/20 | 18 vs 1 | 7.6e-05 | 0 |
| llama33-70b | 0.950 | 285/300 | wrong_anchor | 17/285 (6.0%) [3.8%, 9.3%] | 8/16 | 15 vs 1 | 0.00052 | 1 |
| llama33-70b | 0.950 | 285/300 | wrong_attending | 94/285 (33.0%) [27.8%, 38.6%] | 89/94 | 91 vs 0 | 8.1e-28 | 0 |
| llama33-70b | 0.950 | 285/300 | wrong_nurse | 24/285 (8.4%) [5.7%, 12.2%] | 13/23 | 22 vs 1 | 5.7e-06 | 1 |
| llama33-70b | 0.950 | 285/300 | wrong_patient | 18/285 (6.3%) [4.0%, 9.8%] | 8/18 | 16 vs 1 | 0.00027 | 0 |
Holm-adjusted p (medgemma-27b, wrong_anchor): 4.2e-05
Holm-adjusted p (gemma3-27b-vllm, wrong_anchor): 2.4e-08
Holm-adjusted p (llama33-70b, wrong_anchor): 0.00052
