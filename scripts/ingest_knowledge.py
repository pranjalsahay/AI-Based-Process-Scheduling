"""Command-line utility to ingest knowledge base documents into ChromaDB."""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.rag.retriever import ChromaKnowledgeRetriever


def main():
    parser = argparse.ArgumentParser(description="Ingest OS knowledge base into ChromaDB.")
    parser.add_argument(
        "--kb-dir",
        type=str,
        default="./knowledge_base",
        help="Directory containing markdown, text, or pdf documents."
    )
    parser.add_argument(
        "--chroma-dir",
        type=str,
        default="./data/chroma",
        help="ChromaDB persistent storage directory."
    )
    args = parser.parse_args()

    kb_path = Path(args.kb_dir)
    if not kb_path.exists():
        print(f"Error: Knowledge base directory '{args.kb_dir}' does not exist.")
        sys.exit(1)

    print(f"Starting ingestion from: {kb_path.resolve()}")
    print(f"Persisting ChromaDB to:   {Path(args.chroma_dir).resolve()}")

    retriever = ChromaKnowledgeRetriever(persist_directory=args.chroma_dir)
    stats = retriever.ingest_directory(str(kb_path))

    print("\n--- Ingestion Summary ---")
    print(f"Files processed: {stats['files_ingested']}")
    print(f"Chunks indexed:  {stats['total_chunks']}")
    for detail in stats["details"]:
        print(f"  * {detail['filename']} -> {detail['chunks']} chunks")

    sources = retriever.get_indexed_sources()
    print(f"\nDistinct document titles in index: {len(sources)}")
    print("Ingestion completed successfully!")


if __name__ == "__main__":
    main()
