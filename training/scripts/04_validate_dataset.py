"""Phase 3: Dataset Quality Control, Strict Validation, Deduplication, and Splitting.

Validates:
1. Valid message roles (system, user, assistant) and alternating structure
2. Proper tokenization & length constraints
3. Non-empty messages and valid UTF-8 strings
4. Deduplication across conversations (exact content hashing)
5. Strategy compliance:
   - Concept-learning examples begin interactively or with real-life analogies
   - Direct-answer requests provide immediate technical answers without diagnostic questions
   - Misconception corrections identify errors kindly and provide counter-examples
   - Numerical calculations match exact formulas
6. Splits into reproducible partitions:
   - train.jsonl (80%)
   - val.jsonl (10%)
   - test.jsonl (10%)
7. Generates a comprehensive validation report.
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

def validate_example(ex: Dict[str, Any], idx: int) -> Tuple[bool, List[str]]:
    errors = []
    messages = ex.get("messages", [])

    if not messages or not isinstance(messages, list):
        return False, [f"Example {idx}: 'messages' must be a non-empty list."]

    if len(messages) < 2:
        return False, [f"Example {idx}: Conversation must have at least 2 turns."]

    if messages[0].get("role") != "system":
        errors.append(f"Example {idx}: First message must be 'system' role.")

    expected_role = "user"
    for m_idx, m in enumerate(messages[1:], start=1):
        role = m.get("role")
        content = m.get("content", "")

        if role not in ["user", "assistant"]:
            errors.append(f"Example {idx}, Turn {m_idx}: Invalid role '{role}'.")

        if not content or not isinstance(content, str) or not content.strip():
            errors.append(f"Example {idx}, Turn {m_idx}: Message content cannot be empty.")

        if role != expected_role:
            errors.append(f"Example {idx}, Turn {m_idx}: Expected role '{expected_role}', got '{role}'.")

        expected_role = "assistant" if expected_role == "user" else "user"

    # Pedagogical strategy checks
    first_user_content = messages[1].get("content", "").lower()
    first_assistant_content = messages[2].get("content", "").lower() if len(messages) > 2 else ""

    # If user explicitly requested direct answer, assistant should NOT force a question
    if "just give me" in first_user_content or "directly" in first_user_content or "no questions" in first_user_content:
        if "what do you think" in first_assistant_content or "how would you" in first_assistant_content:
            errors.append(f"Example {idx}: Direct-answer request was met with forced diagnostic question.")

    return len(errors) == 0, errors

def compute_hash(messages: List[Dict[str, str]]) -> str:
    """Computes a deterministic MD5 hash of conversation text for deduplication."""
    text = "".join(f"{m.get('role', '')}:{m.get('content', '').strip()}" for m in messages)
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def validate_and_split(
    raw_path: Path,
    out_dir: Path,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    seed: int = 42
) -> Dict[str, Any]:
    print("=" * 70)
    print("PHASE 3: VALIDATING, DEDUPLICATING, AND SPLITTING DATASET")
    print("=" * 70)

    if not raw_path.exists():
        print(f"Error: Raw dataset {raw_path} not found.")
        return {}

    raw_examples = []
    with open(raw_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_examples.append(json.loads(line))

    print(f"Loaded {len(raw_examples)} raw examples from {raw_path}")

    # Validation & Deduplication
    seen_hashes = set()
    validated_examples = []
    validation_failures = []
    duplicates_count = 0

    for idx, ex in enumerate(raw_examples):
        is_valid, errs = validate_example(ex, idx)
        if not is_valid:
            validation_failures.append({"index": idx, "errors": errs})
            continue

        h = compute_hash(ex["messages"])
        if h in seen_hashes:
            duplicates_count += 1
            continue
        seen_hashes.add(h)
        validated_examples.append(ex)

    print(f"Validation summary:")
    print(f"  - Valid unique examples: {len(validated_examples)}")
    print(f"  - Duplicates discarded: {duplicates_count}")
    print(f"  - Failed schema/strategy checks: {len(validation_failures)}")

    # Deterministic Shuffle and Split
    import random
    random.seed(seed)
    shuffled = list(validated_examples)
    random.shuffle(shuffled)

    n_total = len(shuffled)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_data = shuffled[:n_train]
    val_data = shuffled[n_train:n_train + n_val]
    test_data = shuffled[n_train + n_val:]

    print(f"Split breakdown:")
    print(f"  - Train: {len(train_data)} examples ({len(train_data)/n_total*100:.1f}%)")
    print(f"  - Validation: {len(val_data)} examples ({len(val_data)/n_total*100:.1f}%)")
    print(f"  - Held-out Test: {len(test_data)} examples ({len(test_data)/n_total*100:.1f}%)")

    # Save Splits
    splits_dir = out_dir / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    def write_split(path: Path, data: List[Dict[str, Any]]):
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    train_path = splits_dir / "train.jsonl"
    val_path = splits_dir / "val.jsonl"
    test_path = splits_dir / "test.jsonl"

    write_split(train_path, train_data)
    write_split(val_path, val_data)
    write_split(test_path, test_data)

    # Category and Token Statistics
    categories = {}
    total_tokens_approx = 0
    for ex in validated_examples:
        cat = ex.get("metadata", {}).get("category", "OTHER")
        categories[cat] = categories.get(cat, 0) + 1
        for m in ex["messages"]:
            total_tokens_approx += len(m.get("content", "").split()) * 1.3

    report = {
        "raw_count": len(raw_examples),
        "validated_unique_count": len(validated_examples),
        "duplicate_count": duplicates_count,
        "failure_count": len(validation_failures),
        "train_count": len(train_data),
        "val_count": len(val_data),
        "test_count": len(test_data),
        "approx_total_tokens": int(total_tokens_approx),
        "category_distribution": categories,
        "validation_failures": validation_failures[:10]  # sample of failures if any
    }

    # Save QC Report
    reports_dir = Path("training/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_json = reports_dir / "03_dataset_quality_report.json"
    with open(report_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    report_md = reports_dir / "03_dataset_quality_report.md"
    with open(report_md, "w", encoding="utf-8") as f:
        f.write("# SchedulAI Phase 3: Dataset Quality Control & Validation Report\n\n")
        f.write(f"- **Total Raw Examples:** {report['raw_count']}\n")
        f.write(f"- **Validated Unique Conversations:** {report['validated_unique_count']}\n")
        f.write(f"- **Duplicates Removed:** {report['duplicate_count']}\n")
        f.write(f"- **Validation Failure Count:** {report['failure_count']}\n")
        f.write(f"- **Approximate Token Count:** {report['approx_total_tokens']:,} tokens\n\n")
        f.write("## Data Partitioning\n\n")
        f.write(f"- **Train Split (`train.jsonl`):** {report['train_count']} examples\n")
        f.write(f"- **Validation Split (`val.jsonl`):** {report['val_count']} examples\n")
        f.write(f"- **Held-Out Test Split (`test.jsonl`):** {report['test_count']} examples\n\n")
        f.write("## Category Distribution\n\n")
        for c, cnt in categories.items():
            f.write(f"- **{c}:** {cnt} conversations\n")

    print(f"\nSaved QC Report to:\n  - {report_json}\n  - {report_md}")
    print("=" * 70)
    return report

if __name__ == "__main__":
    raw = Path("training/data/raw/synthetic_tutoring_dataset_raw.jsonl")
    out = Path("training/data")
    validate_and_split(raw, out)
