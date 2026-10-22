"""Post-upgrade evaluation benchmark and comparison for SchedulAI."""

import time
import json
import httpx
from typing import List, Dict, Any

BASE_URL = "http://127.0.0.1:8000"

BENCHMARK_SCENARIOS = [
    {
        "id": "SCENARIO_1_NEW_TOPIC_DIAGNOSTIC",
        "description": "Student introduces a new conceptual topic",
        "turns": [
            {
                "input": "What is the difference between preemptive and non-preemptive scheduling?",
                "expect_diagnostic_or_inquiry": True,
                "notes": "Tutor should ask what student already knows or start diagnostic, not dump unprompted textbook."
            }
        ]
    },
    {
        "id": "SCENARIO_2_PARTIAL_UNDERSTANDING",
        "description": "Student knows one part but not the other",
        "turns": [
            {
                "input": "What is preemptive vs non-preemptive scheduling?",
            },
            {
                "input": "I know preemptive scheduling allows the OS to interrupt a process, but I don't understand non-preemptive scheduling.",
                "expect_targeted_explanation": True,
                "forbid_full_restart": True
            }
        ]
    },
    {
        "id": "SCENARIO_3_DIRECT_EXPLANATION",
        "description": "Student explicitly asks for direct teaching",
        "turns": [
            {
                "input": "Explain the whole concept of Round Robin directly from the beginning.",
                "expect_direct_explanation": True,
                "forbid_interrogative_rejection": True
            }
        ]
    },
    {
        "id": "SCENARIO_4_CONTEXT_RETENTION_EXAMPLE",
        "description": "Student asks a follow-up about a previous example",
        "turns": [
            {
                "input": "Take an example of FCFS with P1 burst 4 and P2 burst 3 and explain."
            },
            {
                "input": "In that example you just showed, what was the waiting time of P2?",
                "expect_context_retention": True,
                "expected_answer_contains": ["4", "waiting time"]
            }
        ]
    },
    {
        "id": "SCENARIO_5_TOPIC_SWITCH_AND_RETURN",
        "description": "Student switches topic and returns to earlier topic",
        "turns": [
            {
                "input": "Under FCFS, execution order is strictly determined by arrival time."
            },
            {
                "input": "Let's switch to Round Robin. What is a time quantum?"
            },
            {
                "input": "Going back to FCFS, what did we say determines the order?"
            }
        ]
    },
    {
        "id": "SCENARIO_6_LONG_CONVERSATION",
        "description": "Multi-turn conversation testing memory limits",
        "turns": [
            {"input": "Hi, I am studying CPU process scheduling for my OS exam."},
            {"input": "My main weakness is calculating average turnaround time."},
            {"input": "Can you remind me of the exact formula for Turnaround Time?"},
            {"input": "Got it. If arrival time is 3 and completion time is 11, what is TAT?"},
            {"input": "8. Now what if burst time is 4, what is the waiting time?"},
            {"input": "What was the very first weakness I mentioned when we started?"}
        ]
    }
]


def run_evaluation():
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)
    results = []
    latencies = []

    print("=== Running Post-Upgrade Benchmark Evaluation ===")

    for scenario in BENCHMARK_SCENARIOS:
        print(f"\nEvaluating {scenario['id']}: {scenario['description']}")
        s = client.post("/api/sessions", json={"title": scenario["id"], "topic": "Fundamentals"}).json()
        session_id = s["session_id"]

        scenario_turns = []
        for i, turn in enumerate(scenario["turns"]):
            user_msg = turn["input"]
            t0 = time.time()
            res = client.post("/api/chat", json={"session_id": session_id, "message": user_msg})
            elapsed = time.time() - t0
            latencies.append(elapsed)

            data = res.json()
            assistant_msg = data.get("message", "")
            action = data.get("action", "")

            print(f"  Turn {i+1}: '{user_msg[:35]}...' -> {elapsed:.2f}s | Action: {action}")
            scenario_turns.append({
                "turn": i + 1,
                "input": user_msg,
                "output": assistant_msg,
                "action": action,
                "elapsed": elapsed
            })

        results.append({
            "scenario": scenario["id"],
            "turns": scenario_turns
        })

    latencies.sort()
    med_latency = latencies[len(latencies)//2] if latencies else 0.0
    p95_latency = latencies[int(len(latencies)*0.95)] if latencies else 0.0

    print("\n=== Post-Upgrade Results Summary ===")
    print(f"Total Requests: {len(latencies)}")
    print(f"Median Latency: {med_latency:.2f}s")
    print(f"95th Percentile Latency: {p95_latency:.2f}s")

    # Criteria Checks
    # 1. Scenario 1: Diagnostic Opening
    scen1_out = results[0]["turns"][0]["output"]
    is_diagnostic = "?" in scen1_out and ("know" in scen1_out.lower() or "what happens" in scen1_out.lower() or "familiar" in scen1_out.lower())
    
    # 2. Scenario 2: Targeted explanation
    scen2_out = results[1]["turns"][1]["output"]
    is_targeted = "non-preemptive" in scen2_out.lower() and ("interrupt" in scen2_out.lower() or "runs until" in scen2_out.lower() or "yields" in scen2_out.lower())

    # 3. Scenario 3: Direct explanation delivered
    scen3_out = results[2]["turns"][0]["output"]
    is_direct = "round robin" in scen3_out.lower() and ("quantum" in scen3_out.lower() or "time slice" in scen3_out.lower())

    # 4. Scenario 6: Long Memory Retention
    scen6 = next(r for r in results if r["scenario"] == "SCENARIO_6_LONG_CONVERSATION")
    final_turn = scen6["turns"][-1]
    remembers_weakness = "turnaround" in final_turn["output"].lower()

    eval_summary = {
        "median_latency": med_latency,
        "p95_latency": p95_latency,
        "checks": {
            "scenario_1_diagnostic_opening": is_diagnostic,
            "scenario_2_targeted_partial_understanding": is_targeted,
            "scenario_3_direct_explanation_compliance": is_direct,
            "scenario_6_long_memory_retention": remembers_weakness
        },
        "scenarios": results
    }

    with open("app/evaluation/post_upgrade_results.json", "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)

    print("\n=== Criteria Checks ===")
    print(f"  [1] Socratic Diagnostic Opening: {'PASS' if is_diagnostic else 'FAIL'}")
    print(f"  [2] Targeted Partial Explanation: {'PASS' if is_targeted else 'FAIL'}")
    print(f"  [3] Direct Explanation Compliance: {'PASS' if is_direct else 'FAIL'}")
    print(f"  [4] Long Conversation Memory Retention: {'PASS' if remembers_weakness else 'FAIL'}")

    # Compare with baseline
    try:
        with open("app/evaluation/baseline_results.json", "r", encoding="utf-8") as bf:
            baseline = json.load(bf)
        print("\n=== Side-by-Side Baseline vs Post-Upgrade Comparison ===")
        print(f"  Baseline Median Latency:     {baseline.get('median_latency', 0):.2f}s | Upgraded: {med_latency:.2f}s")
        print(f"  Baseline P95 Latency:        {baseline.get('p95_latency', 0):.2f}s | Upgraded: {p95_latency:.2f}s")
        print(f"  Baseline Memory Retention:   {'PASS' if baseline.get('remembers_weakness') else 'FAIL'}")
        print(f"  Upgraded Memory Retention:   {'PASS' if remembers_weakness else 'FAIL'}")
    except Exception as e:
        print(f"Could not load baseline comparison: {e}")


if __name__ == "__main__":
    run_evaluation()
