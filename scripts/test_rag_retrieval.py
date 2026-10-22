"""Test RAG retrieval quality across representative Operating Systems queries."""

import sys
sys.path.insert(0, ".")
from app.rag.retriever import ChromaKnowledgeRetriever

def main():
    retriever = ChromaKnowledgeRetriever()
    queries = [
        ("Single-concept", "what is context switching"),
        ("Comparative", "preemptive vs non-preemptive"),
        ("Algorithm-specific", "how does Round Robin handle time quantum expiration"),
        ("Edge-case", "what happens when two processes have the same burst time in SJF")
    ]

    print("=== RAG Retrieval Benchmark ===")
    all_relevant = True
    for label, q in queries:
        res = retriever.retrieve(query=q, top_k=2)
        print(f"\n--- {label}: '{q}' ---")
        if not res:
            print("  FAIL: No chunks retrieved!")
            all_relevant = False
            continue
        for p in res:
            meta = p.get("metadata", {})
            print(f"  ID: {p['chunk_id']} | Distance: {p['distance']:.4f}")
            print(f"  Heading: {meta.get('section_heading')} | Source: {meta.get('source_filename')}")
            print(f"  Snippet: {p['text'][:140].strip()}...")

    print(f"\nAll Queries Yielded Relevant Documents: {'PASS' if all_relevant else 'FAIL'}")

if __name__ == "__main__":
    main()
