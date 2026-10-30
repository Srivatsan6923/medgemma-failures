## Failure B, development run, MedGemma (p3_anchoring_explore_medgemma)
| model | baseline acc | kept | condition | flips | onto anchor | vs neutral | p | unparseable |
|---|---|---|---|---|---|---|---|---|
| medgemma-27b | 0.947 | 284/300 | neutral | 5/284 (1.8%) [0.8%, 4.1%] |  |  |  | 0 |
| medgemma-27b | 0.947 | 284/300 | right_anchor | 6/284 (2.1%) [1.0%, 4.5%] |  | 3 vs 2 | 1 | 2 |
| medgemma-27b | 0.947 | 284/300 | wrong_anchor | 24/284 (8.5%) [5.7%, 12.3%] | 13/19 | 20 vs 1 | 2.1e-05 | 5 |
Holm-adjusted p (medgemma-27b, wrong_anchor): 2.1e-05
