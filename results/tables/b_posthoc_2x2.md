## Failure B, source x certainty on the confirmation items (post-hoc) (b_posthoc_certainty)
medgemma-27b (kept 379): attending confirmed 33.8%, attending suspects 10.8%, nurse confirmed 19.0%, nurse suspects 9.2%
  attending vs nurse | confirmed: 61 vs 5, p=2.6e-13
  attending vs nurse | suspects: 17 vs 11, p=0.34
  confirmed vs suspects | attending: 92 vs 5, p=8.6e-22
  confirmed vs suspects | nurse: 45 vs 8, p=2.4e-07
gemma3-27b-vllm (kept 314): attending confirmed 41.4%, attending suspects 34.1%, nurse confirmed 30.6%, nurse suspects 27.1%
  attending vs nurse | confirmed: 34 vs 0, p=1.2e-10
  attending vs nurse | suspects: 23 vs 1, p=3e-06
  confirmed vs suspects | attending: 31 vs 8, p=0.00029
  confirmed vs suspects | nurse: 23 vs 12, p=0.09
llama33-70b (kept 381): attending confirmed 37.0%, attending suspects 17.8%, nurse confirmed 26.2%, nurse suspects 12.9%
  attending vs nurse | confirmed: 43 vs 2, p=5.9e-11
  attending vs nurse | suspects: 26 vs 7, p=0.0013
  confirmed vs suspects | attending: 74 vs 1, p=4e-21
  confirmed vs suspects | nurse: 56 vs 5, p=5.6e-12
