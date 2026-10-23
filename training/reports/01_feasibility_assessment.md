# SchedulAI Fine-Tuning Feasibility & Environment Assessment

**Date:** 2026-10-23 17:41:30

## 1. Hardware & System Overview

- **OS:** Windows-10-10.0.26300-SP0
- **Python:** 3.10.11 (`C:\Users\suraj\AppData\Local\Programs\Python\Python310\python.exe`)
- **CPU:** 16 Cores (8 Physical)
- **System RAM:** 15.31 GB Total (5.99 GB Free)
- **Disk Free:** 464.8 GB / 951.46 GB
- **GPU:** NVIDIA GeForce RTX 5050 Laptop GPU (7.96 GB VRAM)
- **Driver:** 617.42
- **PyTorch CUDA Kernel Status:** False (CUDA error: no kernel image is available for execution on the device)

## 2. ML Stack Compatibility

- **torch:** `2.5.1+cu121`
- **transformers:** `5.17.0`
- **peft:** `0.21.2`
- **trl:** `1.14.2`
- **datasets:** `5.1.0`
- **accelerate:** `1.15.0`
- **bitsandbytes:** `NOT INSTALLED`

## 3. Ollama Runtime & Current Model

- **Active Model:** `schedulai:latest (parent: qwen2.5:14b-instruct-q3_K_M)` (14.8 Billion, GGUF Q3_K_M)
- **Baseline /api/chat Latency:** 0.056s

## 4. Feasibility Verdict & Recommended Strategy

- **14.8B Direct Local Training:** **INFEASIBLE**
  - 14.8B parameters require ~28 GB VRAM for FP16 or >12 GB VRAM for 4-bit QLoRA with optimizer states and context activations.
  - Available GPU VRAM is 8.0 GB, causing immediate Out-of-Memory (OOM) on 14B QLoRA.
  - System RAM is 15.3 GB total (~6 GB free), which cannot hold 14B FP16 weights (28 GB).
  - Current PyTorch build lacks precompiled sm_120 kernels for RTX 5050 Laptop GPU.

- **Recommended Base Model:** `Qwen/Qwen2.5-0.5B-Instruct`
- **Fine-Tuning Method:** `LoRA (rank=16, alpha=32, target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'])`
- **Execution Engine:** `FP32/BF16 on CPU with multi-threading or compatible acceleration`
- **Deployment Path:** `Export trained LoRA adapter -> Merge into standalone weights -> Export to GGUF -> Register in Ollama as 'schedulai-tuned:latest' -> Seamless zero-downtime integration with instant rollback to 'schedulai:latest'`
