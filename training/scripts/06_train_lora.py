"""Phase 5: Supervised Parameter-Efficient Fine-Tuning (LoRA) Pipeline for SchedulAI.

Trains a LoRA adapter on Qwen2.5-0.5B-Instruct using:
- Pure PyTorch + Hugging Face Transformers + PEFT
- ChatML template with loss masking (labels=-100 on system & user tokens)
- Evaluates validation loss across training steps
- Saves intermediate checkpoints and retains best adapter
- Logs training metrics, loss curve, and resource usage.
"""

import os
import sys
import json
import time
import math
import random
import torch
import torch.nn as nn
from pathlib import Path
from typing import List, Dict, Any, Tuple
from torch.utils.data import Dataset, DataLoader

from transformers import AutoTokenizer, AutoModelForCausalLM, get_cosine_schedule_with_warmup
from peft import LoraConfig, get_peft_model, TaskType, PeftModel

class SocraticTutoringDataset(Dataset):
    """Dataset applying ChatML formatting and assistant-only loss masking."""

    CONCISE_SYSTEM = "You are SchedulAI, an adaptive Socratic Operating Systems tutor specializing in CPU process scheduling."

    def __init__(self, data_path: Path, tokenizer, max_length: int = 256):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []

        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.samples.append(json.loads(line))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        ex = self.samples[idx]
        messages = ex["messages"]

        input_ids = []
        labels = []

        # Tokenize turn by turn with assistant-only loss calculation
        im_start = "<|im_start|>"
        im_end = "<|im_end|>\n"

        for m in messages:
            role = m["role"]
            content = m["content"]
            # Use concise system prompt so sequence length fits comfortably without truncating assistant tokens
            if role == "system":
                content = self.CONCISE_SYSTEM

            turn_str = f"{im_start}{role}\n{content}{im_end}"
            turn_tokens = self.tokenizer.encode(turn_str, add_special_tokens=False)

            input_ids.extend(turn_tokens)
            if role == "assistant":
                # Compute loss on assistant responses and end-of-turn token
                header_tokens = self.tokenizer.encode(f"{im_start}assistant\n", add_special_tokens=False)
                header_len = len(header_tokens)
                turn_labels = [-100] * header_len + turn_tokens[header_len:]
                labels.extend(turn_labels)
            else:
                # Mask out system and user prompts
                labels.extend([-100] * len(turn_tokens))

        # Truncate
        if len(input_ids) > self.max_length:
            input_ids = input_ids[:self.max_length]
            labels = labels[:self.max_length]

        # Safety fallback: ensure at least some tokens are evaluated for loss
        if not any(l != -100 for l in labels):
            labels = list(input_ids)

        attention_mask = [1] * len(input_ids)

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long)
        }

def collate_fn(batch: List[Dict[str, torch.Tensor]], pad_token_id: int) -> Dict[str, torch.Tensor]:
    max_len = max(len(item["input_ids"]) for item in batch)

    batch_input_ids = []
    batch_attention_mask = []
    batch_labels = []

    for item in batch:
        seq_len = len(item["input_ids"])
        pad_len = max_len - seq_len

        # Right-pad
        b_ids = torch.cat([item["input_ids"], torch.full((pad_len,), pad_token_id, dtype=torch.long)])
        b_mask = torch.cat([item["attention_mask"], torch.zeros(pad_len, dtype=torch.long)])
        b_lab = torch.cat([item["labels"], torch.full((pad_len,), -100, dtype=torch.long)])

        batch_input_ids.append(b_ids)
        batch_attention_mask.append(b_mask)
        batch_labels.append(b_lab)

    return {
        "input_ids": torch.stack(batch_input_ids),
        "attention_mask": torch.stack(batch_attention_mask),
        "labels": torch.stack(batch_labels)
    }

def evaluate_loss(model, dataloader: DataLoader, max_batches: int = 6) -> float:
    model.eval()
    total_loss = 0.0
    count = 0
    with torch.no_grad():
        for i, batch in enumerate(dataloader):
            if i >= max_batches:
                break
            outputs = model(**batch)
            loss = outputs.loss
            if not torch.isnan(loss) and not torch.isinf(loss):
                total_loss += float(loss.item())
                count += 1
    model.train()
    return total_loss / max(count, 1)

def train_lora_model():
    print("=" * 70, flush=True)
    print("PHASE 5: STARTING CONTROLLED LORA FINE-TUNING PIPELINE", flush=True)
    print("=" * 70, flush=True)

    base_model_dir = Path("training/base_model")
    train_data_path = Path("training/data/splits/train.jsonl")
    val_data_path = Path("training/data/splits/val.jsonl")
    output_dir = Path("training/checkpoints/schedulai_lora_final")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Tokenizer & Model
    print(f"Loading local base model from {base_model_dir}...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(str(base_model_dir), use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        str(base_model_dir),
        torch_dtype=torch.float32,
        device_map="cpu",
        low_cpu_mem_usage=True
    )

    # 2. Configure LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none"
    )

    peft_model = get_peft_model(base_model, lora_config)
    peft_model.print_trainable_parameters()

    # 3. DataLoaders
    print("Preparing Datasets and DataLoaders...", flush=True)
    max_seq_len = 256
    train_dataset = SocraticTutoringDataset(train_data_path, tokenizer, max_length=max_seq_len)
    val_dataset = SocraticTutoringDataset(val_data_path, tokenizer, max_length=max_seq_len)

    batch_size = 2
    grad_accum_steps = 2  # Effective batch size = 4
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda b: collate_fn(b, tokenizer.pad_token_id)
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=lambda b: collate_fn(b, tokenizer.pad_token_id)
    )

    # 4. Optimizer & Scheduler
    target_steps = 40
    lr = 3.0e-4
    optimizer = torch.optim.AdamW(peft_model.parameters(), lr=lr, weight_decay=0.01)
    lr_scheduler = get_cosine_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=4,
        num_training_steps=target_steps
    )

    print(f"Training Plan: {target_steps} optimization steps (max_len={max_seq_len}), effective batch size=4, LR={lr}", flush=True)

    # Evaluate Initial Validation Loss
    init_val_loss = evaluate_loss(peft_model, val_loader, max_batches=6)
    print(f"Initial Validation Loss: {init_val_loss:.4f}", flush=True)

    # 5. Training Loop
    peft_model.train()
    step = 0
    running_loss = 0.0
    best_val_loss = init_val_loss
    loss_history = []
    t_start = time.time()

    optimizer.zero_grad()
    done = False
    epoch = 0

    while not done:
        epoch += 1
        for i, batch in enumerate(train_loader):
            outputs = peft_model(**batch)
            loss = outputs.loss / grad_accum_steps
            loss.backward()
            running_loss += float(outputs.loss.item())

            if (i + 1) % grad_accum_steps == 0 or (i + 1) == len(train_loader):
                torch.nn.utils.clip_grad_norm_(peft_model.parameters(), max_norm=1.0)
                optimizer.step()
                lr_scheduler.step()
                optimizer.zero_grad()
                step += 1

                avg_train_loss = running_loss / grad_accum_steps
                running_loss = 0.0
                elapsed = time.time() - t_start

                if step % 10 == 0 or step == target_steps:
                    val_loss = evaluate_loss(peft_model, val_loader, max_batches=6)
                    current_lr = lr_scheduler.get_last_lr()[0]
                    print(
                        f"Step {step:02d}/{target_steps} | "
                        f"Train Loss: {avg_train_loss:.4f} | "
                        f"Val Loss: {val_loss:.4f} | "
                        f"LR: {current_lr:.2e} | "
                        f"Elapsed: {elapsed:.1f}s",
                        flush=True
                    )
                    loss_history.append({
                        "step": step,
                        "train_loss": round(avg_train_loss, 4),
                        "val_loss": round(val_loss, 4),
                        "lr": current_lr,
                        "elapsed_seconds": round(elapsed, 1)
                    })

                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        best_dir = Path("training/checkpoints/best_adapter")
                        best_dir.mkdir(parents=True, exist_ok=True)
                        peft_model.save_pretrained(str(best_dir))
                        tokenizer.save_pretrained(str(best_dir))
                        print(f"  --> Saved new best adapter (Val Loss: {best_val_loss:.4f}) to {best_dir}", flush=True)
                else:
                    print(f"Step {step:02d}/{target_steps} | Train Loss: {avg_train_loss:.4f} | Elapsed: {elapsed:.1f}s", flush=True)

                if step >= target_steps:
                    done = True
                    break

    total_training_time = round(time.time() - t_start, 2)
    print(f"\nTraining completed in {total_training_time}s! Best Val Loss: {best_val_loss:.4f}", flush=True)

    # Save final adapter
    peft_model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"Final adapter saved to {output_dir}", flush=True)

    # 6. Save Report
    report = {
        "status": "COMPLETED",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_model": str(base_model_dir),
        "adapter_type": "LoRA (r=16, alpha=32, target_modules=all_projections)",
        "epochs": epoch,
        "total_optimization_steps": step,
        "training_time_seconds": total_training_time,
        "initial_val_loss": round(init_val_loss, 4),
        "best_val_loss": round(best_val_loss, 4),
        "final_checkpoint": str(output_dir),
        "best_checkpoint": str(Path("training/checkpoints/best_adapter")),
        "loss_history": loss_history
    }

    report_path = Path("training/reports/05_training_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    report_md = Path("training/reports/05_training_report.md")
    with open(report_md, "w", encoding="utf-8") as f:
        f.write("# SchedulAI Phase 5: LoRA Fine-Tuning Execution Report\n\n")
        f.write(f"- **Status:** **{report['status']}**\n")
        f.write(f"- **Base Model:** `{report['base_model']}`\n")
        f.write(f"- **Adapter:** `{report['adapter_type']}`\n")
        f.write(f"- **Training Duration:** {report['training_time_seconds']}s\n")
        f.write(f"- **Total Steps:** {report['total_optimization_steps']}\n")
        f.write(f"- **Initial Validation Loss:** {report['initial_val_loss']}\n")
        f.write(f"- **Best Validation Loss:** **{report['best_val_loss']}**\n")
        f.write(f"- **Saved Checkpoint:** `{report['final_checkpoint']}`\n\n")
        f.write("## Loss Progression\n\n")
        f.write("| Step | Train Loss | Val Loss | Learning Rate | Elapsed Time |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for h in loss_history:
            f.write(f"| {h['step']} | {h['train_loss']} | {h['val_loss']} | {h['lr']:.2e} | {h['elapsed_seconds']}s |\n")

    print(f"Training report saved to:\n  - {report_path}\n  - {report_md}", flush=True)
    print("=" * 70, flush=True)
    return report

if __name__ == "__main__":
    train_lora_model()
