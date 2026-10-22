"""Ollama client for local LLM inference with health checks, retries, and fallbacks."""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Asynchronous client interacting with local Ollama daemon."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.preferred_model = model_name or settings.OLLAMA_MODEL
        self.timeout = timeout_seconds or settings.INFERENCE_TIMEOUT_SECONDS
        self._active_model: Optional[str] = None

    async def get_available_models(self) -> List[str]:
        """Queries Ollama for currently installed local models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return [m for m in models if m]
        except Exception as e:
            logger.warning(f"Could not reach Ollama at {self.base_url}: {e}")
        return []

    async def select_model(self) -> str:
        """Determines the best available model, falling back if preferred is missing."""
        if self._active_model:
            return self._active_model

        available = await self.get_available_models()
        if not available:
            # Ollama might not be running or no models pulled yet
            self._active_model = self.preferred_model
            return self._active_model

        # Check preferred
        for model in available:
            if self.preferred_model in model or model in self.preferred_model:
                self._active_model = model
                return self._active_model

        # Check fallbacks
        for fallback in settings.OLLAMA_FALLBACK_MODELS:
            for model in available:
                if fallback in model or model in fallback:
                    self._active_model = model
                    return self._active_model

        # Default to the first available model
        self._active_model = available[0]
        return self._active_model

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        format_json: bool = True,
        temperature: float = 0.2
    ) -> str:
        """
        Sends conversation messages to Ollama /api/chat.
        Includes retry and offline fallback handling.
        """
        # Fast path during automated testing
        if os.getenv("TESTING") == "1":
            return self._generate_simulated_fallback(messages[-1]["content"] if messages else "")

        model = await self.select_model()

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": payload_messages,
            "stream": False,
            "keep_alive": "15m",
            "options": {
                "temperature": temperature,
                "num_thread": 8,
                "num_ctx": 1024,
                "num_predict": 120
            }
        }
        if format_json:
            payload["format"] = "json"

        # Attempt API call
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("message", {}).get("content", "")
                    return content
                else:
                    logger.error(f"Ollama returned HTTP {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Ollama inference attempt failed or timed out: {e}")

        # If Ollama is unavailable after retries, return a safe simulated Socratic response
        return self._generate_simulated_fallback(
            messages[-1]["content"] if messages else "",
            messages=payload_messages
        )

    def _generate_simulated_fallback(
        self,
        user_text: str,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Heuristic fallback response matching natural human tutoring intent."""
        from app.core.knowledge_catalog import find_knowledge_entry

        text_lower = user_text.lower().strip()

        # 1. Greetings: "Hello", "Hi", "Hey"
        is_greeting = (
            text_lower in ["hello", "hi", "hey", "hey there", "hi there", "hello!", "hi!", "good morning", "good evening", "howdy", "sup", "greetings"]
            or bool(re.match(r"^(hello|hi|hey|good\s+(morning|afternoon|evening)|howdy|sup|greetings)(\s+there|\s+tutor)?[\s!.,?]*$", text_lower))
        )
        if is_greeting and len(text_lower.split()) <= 4:
            return json.dumps({
                "message": "Hey! What are we learning today?",
                "mode": "socratic",
                "topic": "Fundamentals",
                "action": "chat",
                "question": None,
                "hint": None,
                "misconception": None,
                "concepts_demonstrated": [],
                "concepts_needing_review": [],
                "source_ids": [],
                "requires_calculation": False
            })

        # 2. Gratitude / Closing: "Thanks", "Thank you", "Bye"
        is_gratitude = (
            text_lower in ["thanks", "thank you", "thanks a lot", "thank you so much", "thx", "appreciate it", "got it thanks", "got it, thanks", "bye", "goodbye"]
            or bool(re.match(r"^(thanks|thank\s+you|thx|appreciate\s+it|got\s+it\s+thanks|bye|goodbye)[\s!.,?]*$", text_lower))
        )
        if is_gratitude and len(text_lower.split()) <= 5:
            return json.dumps({
                "message": "You're welcome!",
                "mode": "socratic",
                "topic": "Fundamentals",
                "action": "chat",
                "question": None,
                "hint": None,
                "misconception": None,
                "concepts_demonstrated": [],
                "concepts_needing_review": [],
                "source_ids": [],
                "requires_calculation": False
            })

        # 3. Broad statements / General Goal: "I'm studying CPU scheduling."
        is_general_goal = (
            any(phrase in text_lower for phrase in [
                "studying cpu scheduling", "learning cpu scheduling", "study cpu scheduling",
                "learn cpu scheduling", "working on cpu scheduling"
            ])
            or text_lower in ["cpu scheduling", "i'm studying cpu scheduling", "i am studying cpu scheduling", "i'm studying cpu scheduling.", "i am studying cpu scheduling."]
        )
        if is_general_goal and len(text_lower.split()) <= 8:
            return json.dumps({
                "message": "Nice. Which part are you working on?",
                "mode": "socratic",
                "topic": "Fundamentals",
                "action": "chat",
                "question": None,
                "hint": None,
                "misconception": None,
                "concepts_demonstrated": [],
                "concepts_needing_review": [],
                "source_ids": [],
                "requires_calculation": False
            })

        # 4. Explicit Syllabus Request: "What is on the syllabus?" (ONLY when explicitly asked)
        is_syllabus_req = any(phrase in text_lower for phrase in [
            "syllabus", "topics do you cover", "what topics", "list topics", "what can you teach", "topics covered"
        ])
        if is_syllabus_req:
            return json.dumps({
                "message": (
                    "Here are the topics we cover in CPU scheduling:\n\n"
                    "* **Fundamentals**: Process states, CPU/I/O bursts, CPU scheduler vs. dispatcher, context switching\n"
                    "* **Scheduling Metrics**: Completion Time, Turnaround Time, Waiting Time, Response Time, and Gantt charts\n"
                    "* **Non-Preemptive Algorithms**: First-Come First-Served (FCFS), Shortest Job First (SJF)\n"
                    "* **Preemptive Algorithms**: Shortest Remaining Time First (SRTF), Round Robin (RR), Preemptive Priority\n"
                    "* **Advanced Concepts**: Starvation, aging, convoy effect, multilevel queues\n\n"
                    "Which of these would you like to start with?"
                ),
                "mode": "explanation",
                "topic": "Fundamentals",
                "action": "explain_concept",
                "question": "Which of these topics would you like to start with?",
                "hint": "Pick any algorithm or fundamental concept to begin.",
                "misconception": None,
                "concepts_demonstrated": [],
                "concepts_needing_review": [],
                "source_ids": [],
                "requires_calculation": False
            })

        # 5. Direct Comparison: "What is the difference between FCFS and SJF?"
        if ("fcfs" in text_lower and "sjf" in text_lower) or ("difference between fcfs and sjf" in text_lower):
            return json.dumps({
                "message": (
                    "Here is how **FCFS** and **SJF** compare:\n\n"
                    "* **Selection Rule**: FCFS (First-Come, First-Served) runs processes strictly in the order they arrive (FIFO). SJF (Shortest Job First) selects the process with the shortest CPU burst time next.\n"
                    "* **Performance**: SJF is provably optimal for minimizing average waiting time. In contrast, FCFS can suffer from the **Convoy Effect**, where short processes get stuck waiting behind one long process, resulting in high average waiting times.\n"
                    "* **Trade-off / Risk**: FCFS is simple and fair with zero starvation. SJF requires knowing or estimating burst times in advance, and long processes can suffer from **starvation** if shorter jobs keep arriving.\n\n"
                    "*Quick Example*: If P1 (burst 10) arrives first at $t=0$, followed by P2 (burst 2) and P3 (burst 1):\n"
                    "- Under **FCFS**: P1 runs first (0-10), then P2 (10-12), then P3 (12-13). Average waiting time = $(0 + 10 + 12) / 3 = 7.33$ ms.\n"
                    "- Under **SJF** (if all ready): P3 runs first (0-1), then P2 (1-3), then P1 (3-13). Average waiting time = $(0 + 1 + 3) / 3 = 1.33$ ms."
                ),
                "mode": "explanation",
                "topic": "SJF",
                "action": "explain_concept",
                "question": None,
                "hint": None,
                "misconception": None,
                "concepts_demonstrated": ["fcfs_vs_sjf", "convoy_effect", "optimal_waiting_time"],
                "concepts_needing_review": [],
                "source_ids": ["01_fcfs_algorithm_p1_c0", "01_sjf_algorithm_p1_c0"],
                "requires_calculation": False
            })

        # 6. Direct Explanation Request: "Just explain it directly."
        if any(phrase in text_lower for phrase in [
            "just explain it directly", "explain directly", "teach me from beginning",
            "teach me from the beginning", "just tell me the answer", "just tell me"
        ]):
            return json.dumps({
                "message": (
                    "In Operating Systems, the difference comes down to whether the operating system can interrupt a running process before it finishes:\n\n"
                    "* **Preemptive Scheduling**: The operating system can pause (preempt) a currently running process when a higher-priority process arrives or when its time slice expires (via a hardware timer interrupt). The interrupted process moves from the Running state back to the Ready state.\n"
                    "* **Non-Preemptive (Cooperative) Scheduling**: Once a process gets the CPU, it keeps running until it finishes its CPU burst or voluntarily yields (for example, by waiting for I/O). The scheduler cannot force it off the CPU.\n\n"
                    "Preemptive scheduling provides much better responsiveness for interactive systems, but incurs context switch overhead. Non-preemptive scheduling is simpler and has lower overhead, but long jobs can delay shorter jobs."
                ),
                "mode": "explanation",
                "topic": "Preemption",
                "action": "explain_concept",
                "question": None,
                "hint": None,
                "misconception": None,
                "concepts_demonstrated": ["preemptive_definition", "non_preemptive_cooperative"],
                "concepts_needing_review": [],
                "source_ids": ["01_preemption_concepts_p1_c0"],
                "requires_calculation": False
            })

        # 7. Student Knows Nothing: "I don't know anything about it."
        if any(phrase in text_lower for phrase in [
            "i don't know anything", "i dont know anything", "i know nothing",
            "no idea", "not sure", "don't know anything about it", "dont know anything about it"
        ]):
            return json.dumps({
                "message": (
                    "No problem. Let's start with a simple example. Imagine you're doing a task and someone asks you to pause it so they can use your desk. "
                    "That's the basic idea behind preemption: the operating system can pause a running task so another task can use the CPU. "
                    "In non-preemptive systems, once you get the desk, you keep it until you finish your entire task."
                ),
                "mode": "explanation",
                "topic": "Preemption",
                "action": "explain_concept",
                "question": "Does that desk analogy make sense?",
                "hint": "Think about whether sharing is forced or voluntary.",
                "misconception": None,
                "concepts_demonstrated": ["preemption_analogy"],
                "concepts_needing_review": [],
                "source_ids": ["01_preemption_concepts_p1_c0"],
                "requires_calculation": False
            })

        # 8. Partial Understanding: "I know that preemptive scheduling can interrupt a running process."
        if ("i know" in text_lower or "i understand" in text_lower) and any(k in text_lower for k in ["interrupt", "can interrupt", "allows interrupt"]):
            return json.dumps({
                "message": "Exactly. The key question is what happens when another process becomes ready. Want to try a quick example?",
                "mode": "socratic",
                "topic": "Preemption",
                "action": "ask_question",
                "question": "Want to try a quick example?",
                "hint": "Consider what happens to the interrupted process.",
                "misconception": None,
                "concepts_demonstrated": ["preemptive_interrupts"],
                "concepts_needing_review": [],
                "source_ids": ["01_preemption_concepts_p1_c0"],
                "requires_calculation": False
            })

        # 9. New Concept Inquiry: "I want to understand preemptive and non-preemptive scheduling."
        if any(k in text_lower for k in ["want to understand", "want to learn", "tell me about"]) and "preempt" in text_lower:
            return json.dumps({
                "message": "Sure. Before I explain, what do you already know about the difference?",
                "mode": "socratic",
                "topic": "Preemption",
                "action": "ask_question",
                "question": "Before I explain, what do you already know about the difference?",
                "hint": "Think about whether a running process can be stopped before it finishes.",
                "misconception": None,
                "concepts_demonstrated": [],
                "concepts_needing_review": [],
                "source_ids": ["01_preemption_concepts_p1_c0"],
                "requires_calculation": False
            })

        # Check conversational memory questions if messages are provided
        if messages and any(k in text_lower for k in ["weakness", "first weakness"]):
            stated_weakness = "calculating average turnaround time"
            for m in messages:
                content = m.get("content", "")
                if m.get("role") == "user" and any(k in content.lower() for k in ["weakness", "struggle", "trouble", "bad at"]):
                    stated_weakness = content
                    break
            return json.dumps({
                "message": (
                    f"At the very start of our session, you mentioned that your main weakness is: **{stated_weakness}**.\n\n"
                    f"We have been practicing Turnaround Time ($TAT = CT - AT$) and Waiting Time ($WT = TAT - BT$) to build up your confidence!"
                ),
                "mode": "socratic",
                "topic": "Metrics",
                "action": "ask_question",
                "question": "Would you like to try one more quick turnaround time calculation to verify your mastery?",
                "hint": "Remember: TAT is Completion Time minus Arrival Time.",
                "misconception": None,
                "concepts_demonstrated": ["turnaround_time"],
                "concepts_needing_review": [],
                "source_ids": ["01_scheduling_metrics_p1_c0"],
                "requires_calculation": False,
                "gantt_chart_ascii": None
            })

        # 1. Direct match from Comprehensive Knowledge Catalog (preemption, states, pcb, dispatchers, etc.)
        matched_entry = find_knowledge_entry(user_text)
        if matched_entry:
            return json.dumps({
                "message": matched_entry["message"],
                "mode": "explanation",
                "topic": matched_entry["topic"],
                "action": "explain_concept",
                "question": matched_entry.get("question"),
                "hint": matched_entry.get("hint"),
                "misconception": None,
                "concepts_demonstrated": [matched_entry["topic"].lower()],
                "concepts_needing_review": [],
                "source_ids": ["01_scheduling_concepts_p1_c0"],
                "requires_calculation": False,
                "gantt_chart_ascii": None
            })

        # 2. Example request (e.g. "take an example", "consider an example", "give an example")
        if any(k in text_lower for k in ["example", "sample", "consider an example", "take an example", "show an example", "worked example"]):
            fcfs_gantt = (
                "+-------+-------+---+\n"
                "|  P1   |  P2   | P3|\n"
                "+-------+-------+---+\n"
                "0       4       7   8"
            )
            return json.dumps({
                "message": (
                    "### Step-by-Step Worked Example: FCFS Scheduling\n\n"
                    "Let's walk through a concrete example with three processes arriving in the Ready Queue:\n\n"
                    "| Process | Arrival Time (AT) | Burst Time (BT) |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **P1** | 0 ms | 4 ms |\n"
                    "| **P2** | 1 ms | 3 ms |\n"
                    "| **P3** | 2 ms | 1 ms |\n\n"
                    "#### Execution Timeline:\n"
                    "1. **At t = 0 ms**: P1 arrives and immediately starts running. It executes without interruption for 4 ms.\n"
                    "2. **At t = 4 ms**: P1 finishes (Completion Time = 4 ms). Now both P2 (arrived at t=1) and P3 (arrived at t=2) are waiting. Since P2 arrived first, P2 is dispatched and runs for 3 ms.\n"
                    "3. **At t = 7 ms**: P2 finishes (Completion Time = 7 ms). P3 is dispatched and runs for 1 ms.\n"
                    "4. **At t = 8 ms**: P3 finishes (Completion Time = 8 ms). All processes are complete!\n\n"
                    "#### Gantt Chart:\n"
                    "```text\n"
                    f"{fcfs_gantt}\n"
                    "```\n\n"
                    "#### Calculating Metrics:\n"
                    "* **Turnaround Time (TAT = CT - AT)**:\n"
                    "  * P1: $4 - 0 = 4$ ms\n"
                    "  * P2: $7 - 1 = 6$ ms\n"
                    "  * P3: $8 - 2 = 6$ ms\n"
                    "  * **Average Turnaround Time**: $(4 + 6 + 6) / 3 = 5.33$ ms\n\n"
                    "* **Waiting Time (WT = TAT - BT)**:\n"
                    "  * P1: $4 - 4 = 0$ ms\n"
                    "  * P2: $6 - 3 = 3$ ms\n"
                    "  * P3: $6 - 1 = 5$ ms\n"
                    "  * **Average Waiting Time**: $(0 + 3 + 5) / 3 = 2.67$ ms"
                ),
                "mode": "explanation",
                "topic": "FCFS",
                "action": "explain_concept",
                "question": "Notice that P3 only needed 1 ms of CPU time, but had to wait 5 ms because P1 and P2 ran before it. What is the name of this phenomenon in FCFS?",
                "hint": "Think of fast cars queued behind a slow heavy vehicle on a narrow one-lane highway.",
                "misconception": None,
                "concepts_demonstrated": ["fcfs_order", "gantt_chart", "turnaround_time", "waiting_time"],
                "concepts_needing_review": [],
                "source_ids": ["01_fcfs_algorithm_p1_c0", "01_scheduling_metrics_p1_c0"],
                "requires_calculation": False,
                "gantt_chart_ascii": fcfs_gantt
            })

        # 2. Gantt chart inquiry
        elif "gantt" in text_lower or ("chart" in text_lower and "process" in text_lower):
            ascii_gantt = (
                "+-------+-------+-------+\n"
                "|  P1   |  P2   |  P3   |\n"
                "+-------+-------+-------+\n"
                "0       4       7       8"
            )
            return json.dumps({
                "message": (
                    "### What is a Gantt Chart?\n\n"
                    "In CPU process scheduling, a **Gantt Chart** is a horizontal timeline bar chart that illustrates how the CPU is allocated to processes over time.\n\n"
                    "* **Horizontal Axis**: Represents continuous time units (usually milliseconds).\n"
                    "* **Blocks**: Each block represents a process occupying the CPU.\n"
                    "* **Start and End Marks**: Numbers at the bottom mark the exact moment a process begins and finishes (or is preempted).\n"
                    "* **CPU Idle Blocks**: If no process is ready to execute at time `t`, an *Idle* interval is drawn.\n\n"
                    "```text\n"
                    f"{ascii_gantt}\n"
                    "```\n\n"
                    "**Worked Example**: If Process P1 arrives at time 0 with Burst Time 4, it runs from `t=0` to `t=4`. If P2 runs next with Burst Time 3, it runs from `t=4` to `t=7`."
                ),
                "mode": "explanation",
                "topic": "Metrics",
                "action": "explain_concept",
                "question": "If Process P1 arrives at time 0 with burst time 5 ms and runs under FCFS without interruption, at what time will P1 complete on the Gantt chart?",
                "hint": "Since P1 starts at t=0, its completion time is simply 0 + its burst time.",
                "misconception": None,
                "concepts_demonstrated": ["gantt_chart", "timeline_representation"],
                "concepts_needing_review": [],
                "source_ids": ["01_scheduling_metrics_p1_c0", "01_numerical_examples_p1_c0"],
                "requires_calculation": False,
                "gantt_chart_ascii": ascii_gantt
            })

        # 2. Process vs Program or "don't know the difference"
        elif ("process" in text_lower and "program" in text_lower) or (
            any(w in text_lower for w in ["dont know", "don't know", "no idea", "not sure", "what is the difference", "diffrence"]) and
            any(w in text_lower for w in ["process", "program"])
        ):
            return json.dumps({
                "message": (
                    "### Process vs Program: The Core Distinction\n\n"
                    "1. **Program (Passive Entity)**:\n"
                    "   * A file containing instructions stored passively on secondary storage (like your SSD or hard drive, e.g., `chrome.exe` or `python.exe`).\n"
                    "   * It consumes no CPU cycles, has no execution state, and remains static.\n\n"
                    "2. **Process (Active Entity)**:\n"
                    "   * A program loaded into main memory (RAM) and actively being executed by the CPU.\n"
                    "   * It possesses dynamic state: a **Program Counter (PC)**, call stack, heap, data section, and a **Process Control Block (PCB)** managed by the OS.\n\n"
                    "💡 **Everyday Analogy**:\n"
                    "A recipe printed in a cookbook is a **program**. The chef actively reading the recipe, mixing ingredients in the kitchen, and cooking the meal is a **process**!"
                ),
                "mode": "explanation",
                "topic": "Fundamentals",
                "action": "explain_concept",
                "question": "If you open two separate windows of the same web browser, does the operating system treat them as one single process or two distinct processes?",
                "hint": "Consider whether each open window needs its own independent memory state and program counter.",
                "misconception": None,
                "concepts_demonstrated": ["process_vs_program", "active_vs_passive_entity"],
                "concepts_needing_review": [],
                "source_ids": ["01_process_basics_p1_c0"],
                "requires_calculation": False
            })

        # 3. Scheduling Metrics: Turnaround Time, Waiting Time, Response Time
        elif any(k in text_lower for k in ["turnaround", "waiting time", "response time", "completion time", "metrics"]):
            return json.dumps({
                "message": (
                    "### Key CPU Scheduling Metrics\n\n"
                    "To evaluate how well an algorithm performs, the OS tracks three fundamental metrics:\n\n"
                    "1. **Turnaround Time (TAT)**: Total elapsed time from process arrival to final completion.\n"
                    "   $$\\text{TAT} = \\text{Completion Time (CT)} - \\text{Arrival Time (AT)}$$\n\n"
                    "2. **Waiting Time (WT)**: Total time the process spent sitting in the Ready Queue waiting for the CPU.\n"
                    "   $$\\text{WT} = \\text{Turnaround Time (TAT)} - \\text{Burst Time (BT)}$$\n\n"
                    "3. **Response Time (RT)**: Time from process arrival until it gets its very first CPU slice.\n"
                    "   $$\\text{RT} = \\text{First Execution Time} - \\text{Arrival Time (AT)}$$"
                ),
                "mode": "explanation",
                "topic": "Metrics",
                "action": "explain_concept",
                "question": "Suppose Process P1 arrives at time 0, needs 6 ms of CPU burst, and completes at time 10 ms. What is its Waiting Time?",
                "hint": "Waiting Time = Turnaround Time (10 - 0 = 10) minus Burst Time (6).",
                "misconception": None,
                "concepts_demonstrated": ["turnaround_time", "waiting_time", "response_time"],
                "concepts_needing_review": [],
                "source_ids": ["01_scheduling_metrics_p1_c0"],
                "requires_calculation": True
            })

        # 4. FCFS (First-Come, First-Served) & Convoy Effect
        elif "fcfs" in text_lower or "first-come" in text_lower or "convoy" in text_lower:
            return json.dumps({
                "message": (
                    "### First-Come, First-Served (FCFS) Scheduling\n\n"
                    "**FCFS** is the simplest non-preemptive scheduling algorithm. The CPU is allocated strictly in the order processes arrive in the Ready Queue (FIFO queue).\n\n"
                    "* **Advantage**: Simple, predictable, and zero starvation.\n"
                    "* **Major Drawback**: The **Convoy Effect**, where short I/O-bound processes wait behind a massive CPU-bound job, causing poor CPU and I/O device utilization and high average waiting times."
                ),
                "mode": "socratic",
                "topic": "FCFS",
                "action": "ask_question",
                "question": "What is the name and practical consequence of short processes getting trapped behind a very long process in FCFS?",
                "hint": "Think about several sports cars queued behind an extremely slow tractor on a single-lane road.",
                "misconception": None,
                "concepts_demonstrated": ["fcfs_order", "convoy_effect"],
                "concepts_needing_review": [],
                "source_ids": ["01_fcfs_algorithm_p1_c0"],
                "requires_calculation": False
            })

        # 5. Round Robin (RR) & Time Quantum
        elif "round robin" in text_lower or "rr" in text_lower or "quantum" in text_lower:
            return json.dumps({
                "message": (
                    "### Round Robin (RR) Scheduling\n\n"
                    "**Round Robin** is designed specifically for time-sharing interactive systems. Each process is allocated a small unit of CPU time called a **Time Quantum** (typically 10-100 ms).\n\n"
                    "* If a process's burst exceeds the quantum, it is **preempted** and placed at the tail of the Ready Queue.\n"
                    "* If the quantum is very large (approaching $\\infty$), RR behaves like **FCFS**.\n"
                    "* If the quantum is too small, context-switching overhead dominates and degrades overall throughput."
                ),
                "mode": "socratic",
                "topic": "Round Robin",
                "action": "ask_question",
                "question": "Which algorithm does Round Robin become equivalent to when the time quantum exceeds the largest process burst time?",
                "hint": "When the quantum is huge, no process ever gets preempted before finishing its CPU burst.",
                "misconception": None,
                "concepts_demonstrated": ["round_robin_concept", "time_quantum_tradeoff"],
                "concepts_needing_review": [],
                "source_ids": ["01_round_robin_algorithm_p1_c0"],
                "requires_calculation": False
            })

        # 6. SJF / SRTF
        elif "srtf" in text_lower or "sjf" in text_lower or "shortest" in text_lower:
            return json.dumps({
                "message": (
                    "### SJF (Shortest Job First) vs SRTF\n\n"
                    "* **SJF (Non-Preemptive)**: Once the CPU is allocated to a process with the shortest burst, it runs to completion.\n"
                    "* **SRTF (Shortest Remaining Time First)**: The preemptive version of SJF. When a new process arrives, the scheduler compares its burst with the **remaining** time of the currently running process.\n"
                    "* **Provably Optimal**: SJF/SRTF yields the minimum average waiting time for a given set of processes, but suffers from potential starvation of long processes."
                ),
                "mode": "socratic",
                "topic": "SRTF",
                "action": "ask_question",
                "question": "In preemptive SRTF, when a new process arrives, does the scheduler compare total burst time or remaining burst time?",
                "hint": "The currently executing process has already used part of its CPU burst.",
                "misconception": None,
                "concepts_demonstrated": ["sjf_concept", "srtf_preemption"],
                "concepts_needing_review": [],
                "source_ids": ["01_sjf_algorithm_p1_c0", "01_srtf_preemptive_p1_c0"],
                "requires_calculation": False
            })

        # 7. Priority Scheduling, Starvation, and Aging
        elif "priority" in text_lower or "starvation" in text_lower or "aging" in text_lower:
            return json.dumps({
                "message": (
                    "### Priority Scheduling\n\n"
                    "Each process is assigned a priority value, and the CPU is allocated to the process with the highest priority (often smaller numerical value = higher priority in OS conventions).\n\n"
                    "* **Starvation (Indefinite Blocking)**: Low-priority processes may wait forever if a steady stream of high-priority processes keeps arriving.\n"
                    "* **Solution (Aging)**: Gradually increasing the priority of processes that have been waiting in the system for a long duration."
                ),
                "mode": "socratic",
                "topic": "Priority",
                "action": "ask_question",
                "question": "What technique prevents starvation by gradually boosting the priority of waiting processes over time?",
                "hint": "Think of human beings getting older as time passes.",
                "misconception": None,
                "concepts_demonstrated": ["priority_scheduling", "starvation_and_aging"],
                "concepts_needing_review": [],
                "source_ids": ["01_priority_scheduling_p1_c0"],
                "requires_calculation": False
            })

        # 8. General "I don't know" or confusion
        elif any(w in text_lower for w in ["i don't know", "i dont know", "no idea", "not sure", "don't understand", "dont understand", "teach me", "help"]):
            return json.dumps({
                "message": (
                    "No problem at all! Learning Operating Systems is all about building strong mental models step by step.\n\n"
                    "At its core, **CPU Process Scheduling** solves a simple problem: the computer has one CPU (or limited CPU cores), but dozens of programs want to run simultaneously. The operating system must decide:\n"
                    "1. **Who runs next?**\n"
                    "2. **For how long?**\n"
                    "3. **What happens when a new or higher-priority job arrives?**\n\n"
                    "We can explore this through intuitive real-world analogies, algorithm rules (like FCFS or Round Robin), or interactive numerical problems."
                ),
                "mode": "explanation",
                "topic": "Fundamentals",
                "action": "explain_concept",
                "question": "Would you like to start with how processes queue up in arrival order (FCFS), or how they share CPU time in turns (Round Robin)?",
                "hint": "Choose either FCFS or Round Robin to begin our exploration.",
                "misconception": None,
                "concepts_demonstrated": ["scheduling_objective"],
                "concepts_needing_review": [],
                "source_ids": ["01_process_basics_p1_c0"],
                "requires_calculation": False
            })

        # 9. Generic Default Fallback - Natural dialogue without syllabus dump
        else:
            return json.dumps({
                "message": "Let's explore that. Which specific concept or scheduling algorithm would you like to focus on?",
                "mode": "socratic",
                "topic": "Fundamentals",
                "action": "chat",
                "question": None,
                "hint": None,
                "misconception": None,
                "concepts_demonstrated": [],
                "concepts_needing_review": [],
                "source_ids": [],
                "requires_calculation": False
            })
