import sys
sys.path.insert(0, ".")
from app.core.knowledge_catalog import KNOWLEDGE_CATALOG

print("Catalog questions count:", sum(1 for v in KNOWLEDGE_CATALOG.values() if "question" in v))
for k, v in KNOWLEDGE_CATALOG.items():
    if "question" in v:
        print(f"'{k}': \"{v['question']}\"")
