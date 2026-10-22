"""Baseline evaluation benchmark for SchedulAI."""

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
                "expected_answer_contains": ["1", "4", "waiting time"]
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


def run_benchmark():
    client = httpx.Client(base_url=BASE_URL, timeout=40.0)
    results = []
    latencies = []

    print("=== Running Baseline Benchmark ===")

    for scenario in BENCHMARK_SCENARIOS:
        print(f"\nRunning {scenario['id']}: {scenario['description']}")
        # Create dedicated session for isolation
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

            print(f"  Turn {i+1}: '{user_msg[:40]}...' -> {elapsed:.2f}s | Action: {action}")
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

    print("\n=== Baseline Results Summary ===")
    print(f"Total Requests: {len(latencies)}")
    print(f"Median Latency: {med_latency:.2f}s")
    print(f"95th Percentile Latency: {p95_latency:.2f}s")

    # Check Turn 6 in Scenario 6: did it remember the first weakness?
    scen6 = next(r for r in results if r["scenario"] == "SCENARIO_6_LONG_CONVERSATION")
    final_turn = scen6["turns"][-1]
    remembers_weakness = "turnaround" in final_turn["output"].lower()
    print(f"Scenario 6 Long Memory Retention: {'PASS' if remembers_weakness else 'FAIL'}")
    print(f"Final response: {final_turn['output'][:200]}...")

    with open("app/evaluation/baseline_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "median_latency": med_latency,
            "p95_latency": p95_latency,
            "scenarios": results,
            "remembers_weakness": remembers_weakness
        }, f, indent=2)


if __name__ == "__main__":
    run_benchmark()
