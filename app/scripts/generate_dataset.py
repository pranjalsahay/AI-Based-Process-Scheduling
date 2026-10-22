import json
import random
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from app.core.socratic_engine import SOCRATIC_CURRICULUM
from app.core.quiz_engine import QUIZ_BANK

system_prompt = (
    "You are SchedulAI, an expert Operating Systems tutor specializing in CPU process scheduling. "
    "You teach adaptively through Socratic questioning, real-life analogies, and guided inquiry. "
    "Never dump textbook definitions unprompted. If a student holds a misconception, diagnose it kindly. "
    "If a student asks directly for an explanation, formula, or example, answer clearly and immediately."
)

def build_dataset():
    dialogues = []

    for cid, data in SOCRATIC_CURRICULUM.items():
        topic = data["topic"]
        disp = data["display_name"]
        
        # 1. Socratic Ideal Path (Analogy -> Mechanism -> Trade-offs)
        d1 = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"What is {disp}?"},
            {"role": "assistant", "content": data["stage_1_analogy_question"]},
            {"role": "user", "content": data["stage_1_expected"][0]},
            {"role": "assistant", "content": f"{data['stage_2_explanation']}\n\n{data['stage_2_question']}"},
            {"role": "user", "content": data["stage_2_expected"][0]},
            {"role": "assistant", "content": f"{data['stage_3_explanation']}\n\n{data['stage_3_question']}"},
            {"role": "user", "content": data["stage_3_expected"][0]},
            {"role": "assistant", "content": "Precisely! You've nailed the core concept and its trade-offs.\n\nWould you like to walk through a concrete numerical example with a Gantt chart to see this in action?"}
        ]
        dialogues.append({"messages": d1, "concept": cid, "type": "socratic_ideal"})

        # 2. Socratic Zero Knowledge Path ('I don't know' -> Prerequisite Analogy)
        d2 = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"I want to learn {topic}, but I have no prior background."},
            {"role": "assistant", "content": data["stage_1_analogy_question"]},
            {"role": "user", "content": "I don't know anything about this."},
            {"role": "assistant", "content": f"No problem at all! Let's start with a simple idea: {data['stage_1_dont_know']}\n\nWith that in mind, what do you think would happen?"},
            {"role": "user", "content": data["stage_1_expected"][0]},
            {"role": "assistant", "content": f"{data['stage_2_explanation']}\n\n{data['stage_2_question']}"}
        ]
        dialogues.append({"messages": d2, "concept": cid, "type": "socratic_dont_know"})

        # 3. Misconception Remediation Path
        misconceptions = data.get("stage_1_misconceptions", {})
        if misconceptions:
            mis_key, mis_feedback = next(iter(misconceptions.items()))
            d3 = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Explain {topic} to me."},
                {"role": "assistant", "content": data["stage_1_analogy_question"]},
                {"role": "user", "content": f"I think {mis_key} is how it works."},
                {"role": "assistant", "content": f"⚠️ {mis_feedback}\n\n{data['stage_1_analogy_question']}"},
                {"role": "user", "content": data["stage_1_expected"][0]},
                {"role": "assistant", "content": f"{data['stage_2_explanation']}\n\n{data['stage_2_question']}"}
            ]
            dialogues.append({"messages": d3, "concept": cid, "type": "socratic_misconception"})

        # 4. Direct Definition Request (Non-Socratic Direct Bypass)
        d4 = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Just give me the definition and key facts of {topic}. Don't ask me questions."},
            {"role": "assistant", "content": data["direct_definition"]}
        ]
        dialogues.append({"messages": d4, "concept": cid, "type": "direct_definition"})

    # 5. Interactive Quizzes from QUIZ_BANK
    for q_topic, questions in QUIZ_BANK.items():
        q_diag = [{"role": "system", "content": system_prompt}]
        q_diag.append({"role": "user", "content": f"Quiz me on {q_topic}."})
        q_diag.append({"role": "assistant", "content": f"🎯 **Interactive Quiz: {q_topic}**\n\n**Question 1 of {len(questions)}**:\n{questions[0]['question']}"})
        
        for idx in range(len(questions)):
            q_diag.append({"role": "user", "content": questions[idx]["expected_keywords"][0]})
            if idx + 1 < len(questions):
                q_diag.append({
                    "role": "assistant",
                    "content": f"✅ **Correct!** {questions[idx]['correct_explanation']}\n\n**Question {idx + 2} of {len(questions)}**:\n{questions[idx + 1]['question']}"
                })
            else:
                q_diag.append({
                    "role": "assistant",
                    "content": f"🎉 **Quiz Complete: {q_topic}**\n\n| Metric | Result |\n| :--- | :--- |\n| **Questions Attempted** | {len(questions)} / {len(questions)} |\n| **Score** | 100% ({len(questions)}/{len(questions)} correct) |\n| **Demonstrated Concepts** | {q_topic} mechanics, trade-offs, and edge cases |\n| **Recommended Next Step** | Practice numerical problem solving with a Gantt chart |"
                })
        dialogues.append({"messages": q_diag, "concept": q_topic.lower(), "type": "interactive_quiz"})

    # Shuffle and split
    os.makedirs("data/dataset", exist_ok=True)
    random.seed(42)
    random.shuffle(dialogues)

    with open("data/socratic_tutoring_dataset.jsonl", "w", encoding="utf-8") as f:
        for d in dialogues:
            f.write(json.dumps(d) + "\n")

    n = len(dialogues)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    train_set = dialogues[:n_train]
    val_set = dialogues[n_train:n_train + n_val]
    test_set = dialogues[n_train + n_val:]

    with open("data/dataset/train.jsonl", "w", encoding="utf-8") as f:
        for d in train_set:
            f.write(json.dumps(d) + "\n")

    with open("data/dataset/val.jsonl", "w", encoding="utf-8") as f:
        for d in val_set:
            f.write(json.dumps(d) + "\n")

    with open("data/dataset/test.jsonl", "w", encoding="utf-8") as f:
        for d in test_set:
            f.write(json.dumps(d) + "\n")

    print(f"Generated {n} total Socratic dialogues.")
    print(f"Train split: {len(train_set)} records (70%) -> data/dataset/train.jsonl")
    print(f"Validation split: {len(val_set)} records (15%) -> data/dataset/val.jsonl")
    print(f"Test split: {len(test_set)} records (15%) -> data/dataset/test.jsonl")

if __name__ == "__main__":
    build_dataset()
