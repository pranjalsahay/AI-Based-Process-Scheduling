import sys
sys.path.insert(0, ".")
from app.core.socratic_engine import SOCRATIC_CURRICULUM

for name, c in SOCRATIC_CURRICULUM.items():
    print(f"=== {name.upper()} ({c.get('display_name')}) ===")
    print("  S1 Analogy Q:", c.get("stage_1_analogy_question", "MISSING"))
    print("  S1 Expected:", c.get("stage_1_expected", []))
    print("  S1 Misconceptions:", list(c.get("stage_1_misconceptions", {}).keys()))
    print("  S2 Expl:", c.get("stage_2_explanation", "MISSING")[:80])
    print("  S2 Q:", c.get("stage_2_question", "MISSING"))
    print("  S2 Expected:", c.get("stage_2_expected", []))
    print("  S2 Misconceptions:", list(c.get("stage_2_misconceptions", {}).keys()))
    print("  S3 Expl:", c.get("stage_3_explanation", "MISSING")[:80])
    print("  S3 Q:", c.get("stage_3_question", "MISSING"))
    print("  S3 Expected:", c.get("stage_3_expected", []))
    print("  S4 Trigger:", c.get("stage_4_worked_example_trigger", False))
    print()
