## Failure B, questions both MedGemma and Gemma-3 answer correctly with no line (post-hoc) (b_confirm_anchoring)
questions both models answer correctly with no line: 312
| condition | MedGemma | Gemma-3 | MG only | G only | p |
|---|---|---|---|---|---|
| neutral | 3/312 (1.0%) [0.3%, 2.8%] | 10/312 (3.2%) [1.8%, 5.8%] | 2 | 9 | 0.065 |
| right_anchor | 5/312 (1.6%) [0.7%, 3.7%] | 13/312 (4.2%) [2.5%, 7.0%] | 3 | 11 | 0.057 |
| wrong_anchor | 14/312 (4.5%) [2.7%, 7.4%] | 43/312 (13.8%) [10.4%, 18.0%] | 8 | 37 | 1.5e-05 |
