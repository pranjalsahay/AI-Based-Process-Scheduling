import sys
sys.path.insert(0, ".")
from app.core.socratic_engine import SOCRATIC_CURRICULUM
from app.core.knowledge_catalog import KNOWLEDGE_CATALOG, evaluate_catalog_answer

print("=== VERIFYING SOCRATIC CURRICULUM (20 concepts) ===")
required_fields = [
    'id', 'display_name', 'topic', 'subtopic', 'keywords',
    'stage_1_analogy_question', 'stage_1_hint', 'stage_1_expected', 'stage_1_misconceptions', 'stage_1_dont_know',
    'stage_2_explanation', 'stage_2_question', 'stage_2_expected', 'stage_2_misconceptions',
    'stage_3_explanation', 'stage_3_question', 'stage_3_expected',
    'stage_4_worked_example_trigger', 'direct_definition'
]

for name, concept in SOCRATIC_CURRICULUM.items():
    missing = [f for f in required_fields if f not in concept or not concept[f]]
    if missing:
        print(f"FAILED {name}: missing {missing}")
    else:
        print(f"OK {name}: trigger_ex={concept['stage_4_worked_example_trigger']}")

print("\n=== CHECKING evaluate_catalog_answer() against KNOWLEDGE_CATALOG ===")
import inspect
src = inspect.getsource(evaluate_catalog_answer)
print(f"evaluate_catalog_answer source length: {len(src)} chars, {len(src.splitlines())} lines")

import re
eval_patterns = re.findall(r'if\s+(?:.*in\s+last_q_lower|.*search\(.*last_q_lower\)|.*concept\s*==|.*topic\s*==).*:', src)
print(f"Found {len(eval_patterns)} condition checks in evaluate_catalog_answer")
for p in eval_patterns:
    print("  ", p.strip())
