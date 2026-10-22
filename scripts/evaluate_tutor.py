"""Evaluation script testing RAG retrieval quality and tutoring behavior."""

import sys
import json
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.rag.retriever import ChromaKnowledgeRetriever
from app.core.tutoring_engine import TutoringEngine
from app.schemas.chat import TutoringMode


def evaluate_retrieval(chroma_dir: str = "./data/chroma") -> dict:
    """Evaluates top-k retrieval accuracy against the evaluation cases."""
    cases_path = project_root / "app" / "evaluation" / "retrieval_cases.json"
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    retriever = ChromaKnowledgeRetriever(persist_directory=chroma_dir)
    total = len(cases)
    hits = 0
    keyword_hits = 0

    print("\n=== Evaluating RAG Retrieval Quality ===")
    for case in cases:
        query = case["query"]
        expected_doc = case["expected_document_id"]
        keywords = case["expected_keywords"]

        results = retriever.retrieve(query, topic=case.get("topic"), top_k=3)
        retrieved_docs = [r["metadata"].get("document_id", "") for r in results]
        all_text = " ".join(r["text"].lower() for r in results)

        hit = any(expected_doc in doc for doc in retrieved_docs)
        kw_hit = all(kw in all_text for kw in keywords)

        if hit:
            hits += 1
        if kw_hit:
            keyword_hits += 1

        status = "PASS" if hit else "FAIL"
        print(f"[{status}] Query: '{query[:45]}...'")
        print(f"       Expected: {expected_doc} | Retrieved: {retrieved_docs[:2]}")

    hit_rate = (hits / total) * 100.0 if total > 0 else 0.0
    kw_rate = (keyword_hits / total) * 100.0 if total > 0 else 0.0
    print(f"\nDocument Hit Rate (Top-3): {hit_rate:.1f}% ({hits}/{total})")
    print(f"Keyword Coverage Rate:    {kw_rate:.1f}% ({keyword_hits}/{total})")

    return {
        "total": total,
        "document_hit_rate": hit_rate,
        "keyword_coverage_rate": kw_rate
    }


def evaluate_tutoring_intents() -> dict:
    """Evaluates pedagogical intent classification against benchmark cases."""
    cases_path = project_root / "app" / "evaluation" / "tutoring_cases.json"
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    engine = TutoringEngine()
    total = len(cases)
    mode_correct = 0

    print("\n=== Evaluating Tutoring Intent & Mode Alignment ===")
    for case in cases:
        inp = case["user_input"]
        expected_mode_str = case["mode"]
        current_mode = TutoringMode.SOCRATIC
        detected_mode = engine.detect_mode_intent(inp, current_mode)

        # Match mode
        match = (detected_mode.value == expected_mode_str)
        if match:
            mode_correct += 1

        status = "PASS" if match else "INFO"
        print(f"[{status}] Case: {case['case_id']} -> Detected Mode: {detected_mode.value} (Expected: {expected_mode_str})")

    mode_acc = (mode_correct / total) * 100.0 if total > 0 else 0.0
    print(f"\nMode Detection Accuracy: {mode_acc:.1f}% ({mode_correct}/{total})")

    return {
        "total": total,
        "mode_accuracy": mode_acc
    }


def main():
    print("Running SchedulAI System Evaluations...")
    rag_metrics = evaluate_retrieval()
    tutor_metrics = evaluate_tutoring_intents()

    print("\n================ FINAL REPORT ================")
    print(f"Retrieval Top-3 Document Hit Rate: {rag_metrics['document_hit_rate']:.1f}%")
    print(f"Tutoring Mode Intent Accuracy:     {tutor_metrics['mode_accuracy']:.1f}%")
    print("==============================================")


if __name__ == "__main__":
    main()
