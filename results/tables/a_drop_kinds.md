## Failure A, what each model does with the target drug (exploratory) (a_confirm_override)
| condition | model | notes | kept | kept + flag | held | held + flag | left off | left off + flag |
|---|---|---|---|---|---|---|---|---|
| neutral_continue_at_discharge | medgemma-27b | 300 | 199 | 99 | 0 | 2 | 0 | 0 |
| neutral_continue_at_discharge | gemma3-27b-vllm | 300 | 258 | 41 | 0 | 1 | 0 | 0 |
| neutral_continued | medgemma-27b | 300 | 173 | 82 | 1 | 43 | 0 | 1 |
| neutral_continued | gemma3-27b-vllm | 300 | 198 | 89 | 1 | 10 | 0 | 2 |
| neutral_silent | medgemma-27b | 300 | 226 | 23 | 3 | 48 | 0 | 0 |
| neutral_silent | gemma3-27b-vllm | 300 | 216 | 36 | 9 | 38 | 0 | 1 |
| trigger_continue_at_discharge | medgemma-27b | 300 | 122 | 175 | 0 | 3 | 0 | 0 |
| trigger_continue_at_discharge | gemma3-27b-vllm | 300 | 156 | 144 | 0 | 0 | 0 | 0 |
| trigger_continued | medgemma-27b | 300 | 76 | 137 | 1 | 84 | 0 | 2 |
| trigger_continued | gemma3-27b-vllm | 300 | 85 | 189 | 2 | 21 | 0 | 3 |
| trigger_silent | medgemma-27b | 300 | 149 | 76 | 10 | 64 | 0 | 1 |
| trigger_silent | gemma3-27b-vllm | 300 | 128 | 99 | 21 | 51 | 0 | 1 |
held = in stop_or_hold; left off = in no list; flag = a flag names the drug
