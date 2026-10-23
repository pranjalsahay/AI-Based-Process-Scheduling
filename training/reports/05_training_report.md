# SchedulAI Phase 5: LoRA Fine-Tuning Execution Report

- **Status:** **COMPLETED**
- **Base Model:** `training\base_model`
- **Adapter:** `LoRA (r=16, alpha=32, target_modules=all_projections)`
- **Training Duration:** 405.38s
- **Total Steps:** 40
- **Initial Validation Loss:** 2.9578
- **Best Validation Loss:** **0.2669**
- **Saved Checkpoint:** `training\checkpoints\schedulai_lora_final`

## Loss Progression

| Step | Train Loss | Val Loss | Learning Rate | Elapsed Time |
| :--- | :--- | :--- | :--- | :--- |
| 10 | 1.1801 | 1.0597 | 2.80e-04 | 96.6s |
| 20 | 0.1581 | 0.4771 | 1.76e-04 | 191.7s |
| 30 | 0.1911 | 0.3109 | 5.36e-05 | 287.8s |
| 40 | 0.1439 | 0.2669 | 0.00e+00 | 393.8s |
