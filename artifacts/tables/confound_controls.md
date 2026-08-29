# Confound Controls

| control | answer_token_auroc | prompt_token_auroc | probe_auroc | tfidf_auroc | gap | note | auroc | all_prompts_auroc | successful_attacks_auroc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| prompt_leakage | 1.0 | nan |  |  |  |  |  |  |  |
| surface_text |  |  | 1.0 | 0.5 | 0.5 |  |  |  |  |
| prefill_mismatch |  |  |  |  |  | requires additional artifacts; placeholder | 0.5 |  |  |
| template_overfit |  |  |  |  |  | requires additional artifacts; placeholder | 0.5 |  |  |
| failed_attack_filtering |  |  |  |  |  | requires additional artifacts; placeholder | 0.5 |  |  |
| failed_attack_filtering_real |  |  |  |  | 0.5 |  |  | 1.0 | 0.5 |
