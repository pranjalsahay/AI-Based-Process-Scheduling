"""Socratic Curriculum Engine for SchedulAI.

Implements question-driven, analogy-centered teaching across all Operating Systems CPU scheduling concepts:
- Fundamentals: Process vs Program, States, PCB, Dispatcher, Context Switching, CPU vs I/O bursts, Ready vs Waiting queues.
- Algorithms: FCFS, Non-Preemptive SJF, SRTF, Preemptive & Non-Preemptive Priority, Round Robin, Multilevel Feedback Queue (MLFQ).
- Metrics: Turnaround Time, Waiting Time, Response Time, CPU Utilization, Throughput.
- Properties: Preemption, Convoy Effect, Starvation, Aging, Time Quantum selection.

Core Teaching Principle:
Interpret concept inquiries as a request to learn interactively. Begin with an intuitive real-life analogy guiding question,
wait for the student's reasoning, interpret their answer adaptively, introduce formal terminology gradually, and verify understanding.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from app.schemas.chat import TutoringMode, TutorAction, TutorStructuredResponse
from app.database.models import LearnerStateModel, MessageModel

logger = logging.getLogger(__name__)


# Structured Socratic curriculum definition for all OS CPU scheduling concepts
SOCRATIC_CURRICULUM: Dict[str, Dict[str, Any]] = {
    "round_robin": {
        "id": "round_robin",
        "display_name": "Round Robin (RR)",
        "topic": "Round Robin",
        "subtopic": "Time-Sharing & Circular Queue",
        "keywords": ["round robin", "rr", "time slice", "time quantum", "quantum"],
        "stage_1_analogy_question": "Imagine several people need to share one computer. How could we make sure nobody occupies it for too long and everyone gets a fair turn?",
        "stage_1_hint": "Think about using a timer or taking turns.",
        "stage_1_expected": ["turn", "turns", "timer", "time limit", "fixed time", "share", "split", "equal", "clock", "take turns"],
        "stage_1_misconceptions": {
            "kick": "If we kick them off permanently, their unfinished work would be lost! Instead, they pause and wait for another turn.",
            "first come": "If the first person uses the computer all day, everyone else is blocked! Taking turns with a timer prevents any single user from hogging the machine."
        },
        "stage_1_dont_know": "Think of a board game or playground swing where each player gets a 2-minute timer on their turn. When the timer dings, the next player gets a turn!",
        "stage_2_explanation": "Exactly! Everyone gets a fixed turn, and when their timer expires, the next person gets the computer. In Operating Systems, this fixed time slice is called the **time quantum**.",
        "stage_2_question": "What do you think happens to a process that hasn't finished its work when its time quantum expires?",
        "stage_2_expected": [
            "back of the queue", "queue", "wait", "back of the line", "line", "ready queue", "tail",
            "next process", "next", "comes in", "switch", "switches", "pause", "paused", "preempt",
            "preempted", "yield", "yields", "back", "re-enters", "waits", "another process"
        ],
        "stage_2_misconceptions": {
            "terminated": "The process isn't terminated; it still has more work to do! It is simply paused (preempted) and moved to the back of the queue.",
            "deleted": "A running process is never deleted when its timer expires; it just yields the CPU."
        },
        "stage_3_explanation": "Spot on! The CPU switches to the next process, while the unfinished process is paused (preempted) and moved to the back of the circular **Ready Queue** to await its next turn. This circular, turn-taking design is **Round Robin**.",
        "stage_3_question": "If we set the time quantum to be extremely large—larger than the longest process CPU burst—what existing algorithm does Round Robin become equivalent to?",
        "stage_3_expected": ["fcfs", "first come", "first-come", "fifo"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Round Robin (RR)** is a preemptive CPU scheduling algorithm designed for time-sharing systems.\n\n"
            "- **Mechanism**: The CPU scheduler allocates a fixed duration called a **time quantum** (typically 10-100 ms) to each process in arrival order.\n"
            "- **Queue Structure**: Processes reside in a circular FIFO Ready Queue.\n"
            "- **Preemption**: When a hardware timer interrupt signals that a process's quantum has expired, the process is preempted and appended to the back of the Ready Queue.\n"
            "- **Key Trade-off**: If the time quantum is too large, RR degenerates into FCFS; if too small, excessive context-switch overhead degrades CPU throughput."
        )
    },

    "fcfs": {
        "id": "fcfs",
        "display_name": "First-Come, First-Served (FCFS)",
        "topic": "FCFS",
        "subtopic": "Arrival Order & Convoy Effect",
        "keywords": ["fcfs", "first come first served", "first come", "first-come", "fifo"],
        "stage_1_analogy_question": "Let's figure it out together. Imagine you're waiting in a queue at a canteen or ticket counter. Who do you think should be served first?",
        "stage_1_hint": "Think about the order in which people joined the line.",
        "stage_1_expected": ["first", "arrived first", "front of the line", "ahead", "order of arrival", "earlier", "first come", "first person"],
        "stage_1_misconceptions": {
            "shortest": "Serving the shortest order first is Shortest Job First (SJF). In a regular canteen line, whoever arrived first is served first!",
            "skip": "In a strict queue, you cannot cut in line or skip ahead; everyone waits in the order they arrived."
        },
        "stage_1_dont_know": "In any ordinary line at a grocery store or ticket booth, whoever gets in line first gets served first. Simple and natural!",
        "stage_2_explanation": "Exactly! The person who arrived first gets served first. FCFS works the same way: the CPU executes processes strictly in the order they arrive in the Ready Queue, without interrupting them.",
        "stage_2_question": "Now imagine person A in front places a massive order of 20 complex meals, while person B behind them only wants a single cup of coffee. What happens to person B?",
        "stage_2_expected": ["wait", "long wait", "delayed", "stuck", "held up", "slow", "high waiting"],
        "stage_2_misconceptions": {
            "skip": "Remember, in non-preemptive FCFS, person B cannot skip ahead! They must wait until person A is 100% finished."
        },
        "stage_3_explanation": "Right! Even though person B needs only 30 seconds, they are stuck waiting behind the massive task. In Operating Systems, this bottleneck is called the **Convoy Effect**, which inflates average waiting times.",
        "stage_3_question": "Because of the Convoy Effect, what happens to the average waiting time across all processes under FCFS?",
        "stage_3_expected": ["high", "increases", "large", "bad", "poor", "very high"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**First-Come, First-Served (FCFS)** is the simplest non-preemptive CPU scheduling algorithm.\n\n"
            "- **Mechanism**: Processes are dispatched strictly in the order of their arrival in the Ready Queue using a FIFO queue.\n"
            "- **Non-Preemptive**: Once a process obtains the CPU, it runs to completion or until it blocks for I/O.\n"
            "- **Major Weakness**: The **Convoy Effect**, where short CPU bursts are delayed behind a long-running CPU burst, producing high average waiting times."
        )
    },

    "sjf": {
        "id": "sjf",
        "display_name": "Shortest Job First (SJF)",
        "topic": "SJF",
        "subtopic": "Shortest Burst Selection & Starvation",
        "keywords": ["sjf", "shortest job first", "shortest job", "shortest burst"],
        "stage_1_analogy_question": "Let's figure it out together. Imagine you're running a customer service desk and four people are waiting with tasks taking 1 min, 2 min, 5 min, and 30 min. If your goal is to make the average waiting time for everyone as low as possible, in what order would you serve them?",
        "stage_1_hint": "Think about which task finishes quickest so they leave the queue earliest.",
        "stage_1_expected": ["1", "shortest", "smallest", "quickest", "1 min", "short first", "1, 2, 5, 30", "1 2 5 30"],
        "stage_1_misconceptions": {
            "longest": "If you do the 30-minute task first, the 1-min, 2-min, and 5-min people all wait 30 minutes! Doing the shortest tasks first gets more people served quickly and minimizes total waiting time.",
            "arrival": "Arrival order is FCFS. To minimize average waiting time, prioritizing duration works much better."
        },
        "stage_1_dont_know": "If you do the quick 1-minute task first, that person leaves immediately after waiting only 1 minute. If you did the 30-minute job first, everyone would wait half an hour!",
        "stage_2_explanation": "Exactly! Doing the shortest tasks first gets people out of the queue quickest, which mathematically minimizes the average waiting time. This policy is **Shortest Job First (SJF)**: the scheduler picks the process with the smallest CPU burst time.",
        "stage_2_question": "Now imagine that 30-minute job is waiting, and new 1-minute jobs keep arriving every 45 seconds. What happens to that 30-minute job?",
        "stage_2_expected": ["never runs", "starve", "starvation", "wait forever", "indefinite", "blocked", "waits forever"],
        "stage_2_misconceptions": {
            "runs": "It won't get to run if newer shorter jobs keep cutting in front of it! It gets perpetually pushed back."
        },
        "stage_3_explanation": "Precisely. That severe problem is called **starvation** (or indefinite blocking). SJF gives optimal average waiting times, but long processes can be postponed indefinitely.",
        "stage_3_question": "To prevent starvation, what technique gradually increases the priority of waiting processes the longer they wait?",
        "stage_3_expected": ["aging", "ageing"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Shortest Job First (SJF)** associates each process with the length of its next CPU burst and dispatches the process with the smallest burst.\n\n"
            "- **Optimality**: Provably optimal for minimizing average waiting time for a given stationary set of processes.\n"
            "- **Disadvantages**: The exact duration of future CPU bursts cannot be known in advance (must be estimated using exponential smoothing), and long processes suffer from **starvation**."
        )
    },

    "srtf": {
        "id": "srtf",
        "display_name": "Shortest Remaining Time First (SRTF)",
        "topic": "SRTF",
        "subtopic": "Preemptive SJF",
        "keywords": ["srtf", "shortest remaining time first", "shortest remaining time", "preemptive sjf"],
        "stage_1_analogy_question": "Imagine you're 3 minutes into a 10-minute task (leaving 7 minutes remaining). Suddenly, a customer arrives with an urgent task that takes only 1 minute. If you're allowed to pause your current task, what should you do to minimize average waiting time?",
        "stage_1_hint": "Compare your remaining 7 minutes to the new 1 minute task.",
        "stage_1_expected": ["pause", "switch", "1 minute", "short", "preempt", "do the 1 minute", "stop"],
        "stage_1_misconceptions": {
            "continue": "In a non-preemptive system you would finish your 7 minutes. But if preemption is allowed, pausing to do the 1-minute task lets that customer finish in 1 minute, dramatically reducing average waiting time!"
        },
        "stage_1_dont_know": "If you pause your task for just 1 minute, the other person leaves happy, and you only got delayed by 1 minute. That keeps average waiting time minimal!",
        "stage_2_explanation": "Exactly! Pausing a running process to execute an arriving process with a shorter remaining burst is called **Shortest Remaining Time First (SRTF)**—the preemptive version of SJF.",
        "stage_2_question": "When does the SRTF scheduler evaluate whether to preempt the running process: only when a process finishes, or whenever a new process arrives in the Ready Queue?",
        "stage_2_expected": ["arrives", "arrival", "new process", "whenever a new", "arrival of a new"],
        "stage_2_misconceptions": {
            "terminates": "Waiting until termination is non-preemptive! SRTF evaluates preemption every time a new process arrives in the Ready Queue."
        },
        "stage_3_explanation": "Spot on! Preemption occurs whenever a newly arrived process has a burst strictly shorter than the current runner's remaining time.",
        "stage_3_question": "What penalty does SRTF pay every time it pauses one process and switches to another?",
        "stage_3_expected": ["context switch", "overhead", "context switching", "switching overhead"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Shortest Remaining Time First (SRTF)** is the preemptive variant of Shortest Job First.\n\n"
            "- **Preemption Rule**: Whenever a new process arrives, the scheduler compares its burst with the remaining execution time of the running process. If the new process needs less time, the runner is preempted.\n"
            "- **Advantage**: Achieves minimal average waiting times in dynamic arrival environments.\n"
            "- **Overhead**: Frequent context switches if many short bursts arrive intermittently."
        )
    },

    "priority": {
        "id": "priority",
        "display_name": "Priority Scheduling",
        "topic": "Priority",
        "subtopic": "Urgency, Starvation & Aging",
        "keywords": ["priority scheduling", "priority", "priorities", "high priority", "low priority"],
        "stage_1_analogy_question": "Imagine an emergency room at a hospital. A patient arrives with a minor paper cut, and another arrives with severe chest pain. Who should the doctor see first, regardless of who arrived first?",
        "stage_1_hint": "Think about medical urgency.",
        "stage_1_expected": ["chest pain", "severe", "urgent", "heart", "emergency", "pain", "critical"],
        "stage_1_misconceptions": {
            "paper cut": "In an emergency triage, the most critical medical condition is treated first, not the minor cut!",
            "first arrival": "Emergency rooms don't use strict first-come-first-served when life-threatening cases arrive!"
        },
        "stage_1_dont_know": "The doctor sees the chest pain patient immediately because severe pain is life-critical, while a paper cut can wait safely.",
        "stage_2_explanation": "Exactly! The doctor prioritizes by urgency rather than arrival time. In **Priority Scheduling**, the operating system assigns a priority value to each process and always gives the CPU to the highest-priority ready process.",
        "stage_2_question": "What serious issue occurs if high-priority emergency tasks keep arriving continuously all day, leaving low-priority background tasks waiting?",
        "stage_2_expected": ["starvation", "starve", "indefinite", "wait forever", "never run", "blocked"],
        "stage_2_misconceptions": {
            "deadlock": "Deadlock is a circular wait for locks. When a ready process is neglected simply because higher priority tasks keep arriving, it is called starvation."
        },
        "stage_3_explanation": "Spot on! That is **starvation** (indefinite blocking).",
        "stage_3_question": "How does the Operating System solve starvation by adjusting the priority of waiting processes over time?",
        "stage_3_expected": ["aging", "ageing", "increase priority", "increase their priority", "longer they wait"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Priority Scheduling** allocates the CPU core to the process with the highest priority rank.\n\n"
            "- **Priority Convention**: Many Unix/Linux kernels treat lower numerical values as higher priority (e.g., 0 = highest).\n"
            "- **Variants**: Can be Preemptive (new higher-priority arrival interrupts runner) or Non-Preemptive.\n"
            "- **Starvation & Aging**: Low-priority processes may starve indefinitely. **Aging** resolves this by gradually increasing process priority the longer it waits in the Ready Queue."
        )
    },

    "preemption": {
        "id": "preemption",
        "display_name": "Preemptive vs. Non-Preemptive Scheduling",
        "topic": "Fundamentals",
        "subtopic": "Preemption Mechanics",
        "keywords": ["preempt", "preemptive", "non-preemptive", "non preemptive", "preemption"],
        "stage_1_analogy_question": "Sure. Before I explain, what do you already know about the difference?",
        "stage_1_hint": "Think about whether a running process can be interrupted or must be allowed to finish.",
        "stage_1_expected": ["interrupt", "pause", "cooperative", "running", "forced", "stop", "switch"],
        "stage_1_misconceptions": {
            "non-preemptive": "If non-preemptive were used on your desktop, clicking a button or typing would freeze until whatever long background task is running completely terminates!",
            "voluntary": "A voluntary yield is non-preemptive cooperation, whereas preemption is forced by an external interrupt!"
        },
        "stage_1_dont_know": "No problem. Let's start with a simple example. Imagine you're doing a task and someone asks you to pause it so they can use your desk. That's the basic idea behind preemption...",
        "stage_2_explanation": "Exactly! **Preemptive scheduling** allows the operating system kernel to forcibly interrupt a running process so interactive tasks (like keystrokes or mouse clicks) get immediate CPU time.",
        "stage_2_question": "What special hardware mechanism must an operating system have to interrupt a process that refuses to give up the CPU voluntarily?",
        "stage_2_expected": ["timer", "timer interrupt", "clock", "interrupt", "hardware timer"],
        "stage_2_misconceptions": {
            "software": "A runaway software loop can ignore instructions! Hardware timer interrupts forcibly transfer CPU control back to the kernel.",
            "terminated": "Preemption does not kill the process; it simply moves it back to the Ready Queue so it can continue later."
        },
        "stage_3_explanation": "Spot on. A programmable interval timer fires periodic hardware interrupts, allowing the kernel dispatcher to reclaim CPU control.",
        "stage_3_question": "In non-preemptive scheduling, when are the only times the CPU scheduler makes a scheduling decision?",
        "stage_3_expected": ["terminates", "blocks", "exit", "i/o", "voluntary", "finishes"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Preemptive vs. Non-Preemptive Scheduling**:\n\n"
            "- **Non-Preemptive (Cooperative)**: Once the CPU is allocated to a process, it holds the CPU until it voluntarily yields—either by terminating (`exit()`) or blocking for I/O (`wait()`).\n"
            "- **Preemptive**: The kernel can interrupt a running process before its burst completes (triggered by hardware timer interrupts, higher-priority arrivals, or I/O completions).\n"
            "- **Trade-off**: Preemption enables responsive multitasking but incurs context-switching overhead and requires synchronization locks."
        )
    },

    "starvation_and_aging": {
        "id": "starvation_and_aging",
        "display_name": "Starvation and Aging",
        "topic": "Properties",
        "subtopic": "Starvation & Aging",
        "keywords": ["starvation", "aging", "ageing", "indefinite blocking"],
        "stage_1_analogy_question": "In a restaurant where VIP guests keep arriving and getting seated immediately, what happens to the regular customer waiting in line who arrived hours ago?",
        "stage_1_hint": "Think about whether the regular customer ever gets a table.",
        "stage_1_expected": ["wait forever", "never seated", "starve", "starvation", "ignored", "bypassed", "never gets"],
        "stage_1_misconceptions": {
            "deadlock": "Deadlock is when processes are locked waiting on each other's resources. When someone is simply neglected due to priority, it is called starvation."
        },
        "stage_1_dont_know": "If VIPs keep cutting in line, the regular customer will sit waiting forever and never get seated. That is starvation!",
        "stage_2_explanation": "Exactly! That is **starvation** (or indefinite blocking): a ready process is perpetually bypassed because higher-priority tasks keep arriving.",
        "stage_2_question": "To solve this problem fairly without turning away VIPs, how could the restaurant manager ensure the waiting regular customer eventually gets seated?",
        "stage_2_expected": ["increase priority", "aging", "age", "bump up", "higher status", "longer they wait", "gradually"],
        "stage_2_misconceptions": {
            "restart": "Aging doesn't restart the process; it gradually increases its priority number while it waits!"
        },
        "stage_3_explanation": "Bingo! That is **Aging**: gradually increasing a waiting process's priority the longer it sits in the Ready Queue, until it eventually reaches the highest priority and executes.",
        "stage_3_question": "Which scheduling algorithms are most vulnerable to starvation if aging is not implemented?",
        "stage_3_expected": ["sjf", "srtf", "priority", "shortest job"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Starvation (Indefinite Blocking)** is a condition where a runnable process waits perpetually in the Ready Queue because the scheduler continually selects other processes.\n\n"
            "- **Algorithms Affected**: SJF, SRTF, and Priority Scheduling.\n"
            "- **Solution (Aging)**: The kernel periodically increments the priority of processes that have resided in the Ready Queue for extended durations, ensuring eventual execution."
        )
    },

    "context_switching": {
        "id": "context_switching",
        "display_name": "Context Switching",
        "topic": "Fundamentals",
        "subtopic": "Dispatcher & CPU Registers",
        "keywords": ["context switch", "context switching", "switching context", "save state"],
        "stage_1_analogy_question": "Imagine you are in the middle of solving a complex math problem, and you have to switch immediately to writing a history essay. What must you save or bookmark before switching so you don't lose your place?",
        "stage_1_hint": "Think about your notes, page number, and intermediate calculations.",
        "stage_1_expected": ["save", "bookmark", "write down", "notes", "page", "step", "state", "place"],
        "stage_1_misconceptions": {
            "nothing": "If you save nothing, you'd have to solve the whole math problem again from scratch when you return!",
            "free": "Context switching is pure overhead! The CPU executes zero user code while saving and reloading registers."
        },
        "stage_1_dont_know": "You write down your current step and bookmark your page so you can resume exactly where you left off. That's saving state!",
        "stage_2_explanation": "Spot on! In an operating system, saving the state (registers, program counter, memory pointers) of an outgoing process and restoring the state of an incoming process is called a **context switch**.",
        "stage_2_question": "Which specific kernel component performs the context switch: the scheduler that chooses the process, or the dispatcher?",
        "stage_2_expected": ["dispatcher"],
        "stage_2_misconceptions": {
            "scheduler": "The scheduler only decides *which* process to pick; the *dispatcher* is the component that actually performs the context switch.",
            "disk": "Context switching swaps CPU hardware registers and memory pointers in RAM; it doesn't write the process to disk unless swapping."
        },
        "stage_3_explanation": "Exactly! The Dispatcher saves the outgoing process's registers into its PCB and loads the incoming process's registers.",
        "stage_3_question": "During the microseconds while a context switch is happening, is the CPU executing any user program instructions?",
        "stage_3_expected": ["no", "overhead", "none", "wasted", "zero"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "A **Context Switch** is the mechanism of saving the CPU execution state of the currently running process into its Process Control Block (PCB) and loading the saved state of another process.\n\n"
            "- **State Saved**: Program Counter (PC), CPU general registers, stack pointer, and memory management registers.\n"
            "- **Executioner**: The kernel **Dispatcher**.\n"
            "- **Cost**: Pure computational overhead; no useful application work is performed during the switch."
        )
    },

    "pcb": {
        "id": "pcb",
        "display_name": "Process Control Block (PCB)",
        "topic": "Fundamentals",
        "subtopic": "Process Metadata",
        "keywords": ["pcb", "process control block", "task_struct"],
        "stage_1_analogy_question": "When a patient visits a hospital, the doctors need a comprehensive chart listing their vitals, medications, doctor notes, and current status so any doctor on shift can treat them. What kernel data structure serves as that comprehensive record for an active process?",
        "stage_1_hint": "It is a three-letter acronym starting with P.",
        "stage_1_expected": ["pcb", "process control block", "task_struct"],
        "stage_1_misconceptions": {
            "ready queue": "The ready queue holds pointers to PCBs, but the record itself containing all the metadata is the PCB!",
            "code": "The PCB stores execution metadata and saved registers, not the actual application program code itself."
        },
        "stage_1_dont_know": "It's called the Process Control Block (PCB)—the OS's master record file for every single running program.",
        "stage_2_explanation": "Exactly! The **Process Control Block (PCB)** (called `task_struct` in Linux) holds all process metadata: Process ID (PID), process state, program counter, CPU registers, scheduling priority, and memory pointers.",
        "stage_2_question": "When the operating system performs a context switch, where are the outgoing process's CPU registers saved?",
        "stage_2_expected": ["pcb", "process control block", "in its pcb"],
        "stage_2_misconceptions": {
            "user": "PCBs are kept strictly in protected kernel space so user programs cannot tamper with their own priorities or PIDs."
        },
        "stage_3_explanation": "Spot on. They are saved directly into the process's PCB so the process can resume seamlessly later.",
        "stage_3_question": "What happens to a process's PCB when the process finally calls exit() and terminates?",
        "stage_3_expected": ["deleted", "freed", "deallocated", "removed", "reclaimed"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "The **Process Control Block (PCB)** is the fundamental kernel data structure representing an active process in memory.\n\n"
            "- **Key Fields**: Process ID (PID), Process State, Program Counter (PC), CPU registers, CPU scheduling information (priority), Memory-management information (page tables), and I/O status information.\n"
            "- **Role**: Acts as the repository for any information that varies from process to process during execution."
        )
    },

    "dispatcher": {
        "id": "dispatcher",
        "display_name": "Dispatcher",
        "topic": "Fundamentals",
        "subtopic": "Dispatcher vs Scheduler",
        "keywords": ["dispatcher", "dispatch latency"],
        "stage_1_analogy_question": "In an office, after the manager decides who gets the conference room next, who actually guides the person in, sets up their projector, and hands them the microphone?",
        "stage_1_hint": "Think about the attendant who executes the manager's decision.",
        "stage_1_expected": ["dispatcher", "assistant", "nurse", "helper", "attendant", "coordinator"],
        "stage_1_misconceptions": {
            "manager": "The manager (scheduler) made the decision; an attendant or dispatcher physically sets up the room and grants control!",
            "decides": "The dispatcher does not decide which process runs—that is the CPU Scheduler's job! The dispatcher executes the decision."
        },
        "stage_1_dont_know": "In Operating Systems, that attendant is called the Dispatcher! The scheduler makes the decision, and the dispatcher carries it out.",
        "stage_2_explanation": "Exactly! While the **Scheduler** selects *which* process should execute, the **Dispatcher** gives control of the CPU to that selected process.",
        "stage_2_question": "The Dispatcher performs three tasks: saving/restoring context, switching to user mode, and jumping to what location in the program?",
        "stage_2_expected": ["instruction", "program counter", "address", "restart", "proper location"],
        "stage_2_misconceptions": {
            "compiles": "The dispatcher loads saved CPU registers and switches from kernel mode to user mode."
        },
        "stage_3_explanation": "Spot on! It jumps to the instruction pointed to by the Program Counter.",
        "stage_3_question": "What is the time required for the dispatcher to stop one process and start another called?",
        "stage_3_expected": ["dispatch latency", "latency"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "The **Dispatcher** is the kernel module that gives control of the CPU core to the process selected by the short-term scheduler.\n\n"
            "- **Functions**: 1) Context switching, 2) Switching from kernel mode to user mode, 3) Jumping to the proper instruction address in the user program.\n"
            "- **Dispatch Latency**: The elapsed time required for the dispatcher to stop one process and start another running."
        )
    },

    "ready_vs_waiting_queue": {
        "id": "ready_vs_waiting_queue",
        "display_name": "Ready Queue vs. Waiting Queue",
        "topic": "Fundamentals",
        "subtopic": "Queues and States",
        "keywords": ["ready queue", "waiting queue", "device queue", "blocked queue"],
        "stage_1_analogy_question": "In a medical clinic, what is the difference between patients in the waiting room who are ready to see the doctor right now, versus a patient who was sent to the laboratory for a blood test?",
        "stage_1_hint": "Can the blood test patient see the doctor before the lab results arrive?",
        "stage_1_expected": ["ready", "lab", "test", "waiting for test", "cannot see doctor", "waiting for results", "io"],
        "stage_1_misconceptions": {
            "same": "They are fundamentally different: Ready processes only need CPU time; Waiting processes cannot run until an I/O device completes."
        },
        "stage_1_dont_know": "Patients in the lobby are ready to see the doctor immediately. The patient in the lab cannot see the doctor until their test is done!",
        "stage_2_explanation": "Exactly! Processes in the **Ready Queue** have everything they need and are merely waiting for an available CPU core. Processes in the **Waiting Queue** cannot execute even if the CPU is idle because they are waiting for an I/O device or external event.",
        "stage_2_question": "When an I/O operation finishes, does the blocked process go straight onto the CPU core, or does it move to the Ready Queue first?",
        "stage_2_expected": ["ready queue", "ready", "ready state"],
        "stage_2_misconceptions": {
            "running": "A process completing I/O moves to Ready, not directly to Running, because another process is occupying the CPU."
        },
        "stage_3_explanation": "Spot on! The hardware interrupt handler moves the process from the Waiting Queue to the Ready Queue, where it waits for the scheduler to select it.",
        "stage_3_question": "If a CPU is sitting completely idle, can a process in the Waiting Queue be scheduled to run?",
        "stage_3_expected": ["no", "cannot", "never"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Ready Queue vs. Waiting Queue**:\n\n"
            "- **Ready Queue**: Holds processes residing in main memory that are in the READY state, awaiting CPU allocation.\n"
            "- **Waiting (Blocked) Queue**: Holds processes in the WAITING state awaiting an I/O completion or event signal.\n"
            "- **State Transition**: Processes never move directly from Waiting to Running; upon I/O completion, they transition from Waiting $\\to$ Ready."
        )
    },

    "turnaround_time_and_waiting_time": {
        "id": "turnaround_time_and_waiting_time",
        "display_name": "Turnaround Time and Waiting Time",
        "topic": "Metrics",
        "subtopic": "Scheduling Metrics Calculations",
        "keywords": ["turnaround time", "waiting time", "tat", "wt", "scheduling metrics"],
        "stage_1_analogy_question": "If you enter a bank at 10:00 AM, sit in the waiting chairs until 10:20 AM, and the teller serves you for 5 minutes until you leave at 10:25 AM, what was your total time in the bank versus your waiting time?",
        "stage_1_hint": "Total duration = 10:25 - 10:00. Waiting duration = time before service began.",
        "stage_1_expected": ["25", "20", "25 minutes", "20 minutes", "turnaround is 25", "waiting is 20", "25 and 20"],
        "stage_1_misconceptions": {
            "same": "Turnaround time includes execution time; waiting time is purely the time spent sitting in the queue without the CPU!"
        },
        "stage_1_dont_know": "Your total stay in the bank was 25 minutes (10:00 to 10:25). The time you spent waiting before the teller helped you was 20 minutes!",
        "stage_2_explanation": "Exactly! Your total elapsed time from entry to departure (25 minutes) is **Turnaround Time ($TAT = CT - AT$)**, while the time spent waiting in chairs (20 minutes) is **Waiting Time ($WT = TAT - BT$)**.",
        "stage_2_question": "If a process arrives at time AT=0, has burst time BT=8, and completes at CT=14, what was its waiting time?",
        "stage_2_expected": ["6", "6 ms", "6ms"],
        "stage_2_misconceptions": {
            "arrival": "Waiting time is Turnaround Time minus Burst Time, not just Arrival Time."
        },
        "stage_3_explanation": "Spot on! $TAT = 14 - 0 = 14$ ms, and $WT = 14 - 8 = 6$ ms.",
        "stage_3_question": "What is the third metric, Response Time, which measures the duration from arrival until the process gets the CPU for the very first time?",
        "stage_3_expected": ["response time", "rt", "first response"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Core CPU Scheduling Metric Formulas**:\n\n"
            "1. **Turnaround Time (TAT)**: $\\text{TAT} = \\text{Completion Time (CT)} - \\text{Arrival Time (AT)}$\n"
            "2. **Waiting Time (WT)**: $\\text{WT} = \\text{TAT} - \\text{Burst Time (BT)}$\n"
            "3. **Response Time (RT)**: $\\text{RT} = \\text{First Start Time} - \\text{Arrival Time (AT)}$"
        )
    },

    "convoy_effect": {
        "id": "convoy_effect",
        "display_name": "Convoy Effect",
        "topic": "Properties",
        "subtopic": "Convoy Bottleneck",
        "keywords": ["convoy effect", "convoy"],
        "stage_1_analogy_question": "Imagine driving on a narrow single-lane road behind a very slow tractor moving at 10 km/h. What happens to all the fast sports cars behind it?",
        "stage_1_hint": "Can the cars pass, or are they forced to crawl?",
        "stage_1_expected": ["stuck", "wait", "slowed down", "delayed", "line of cars", "convoy", "traffic", "slow"],
        "stage_1_misconceptions": {
            "sjf": "The convoy effect is a defect of FCFS, not SJF."
        },
        "stage_1_dont_know": "All the fast cars get stuck crawling behind the slow tractor because there's no way to pass. That's a convoy!",
        "stage_2_explanation": "Exactly! That exact bottleneck in FCFS scheduling is called the **Convoy Effect**: a long CPU-bound process holds the CPU while many short I/O-bound processes sit idle in the Ready Queue behind it.",
        "stage_2_question": "While the long process holds the CPU and the short I/O-bound processes are stuck waiting, what happens to the utilization of the I/O devices?",
        "stage_2_expected": ["idle", "underutilized", "low", "empty", "wasted", "not used"],
        "stage_2_misconceptions": {
            "deadlock": "Processes aren't deadlocked; they are simply queued up behind a slow CPU hog."
        },
        "stage_3_explanation": "Spot on! The I/O devices sit idle, wasting system capacity while short processes queue up behind the long CPU hog.",
        "stage_3_question": "Does Round Robin prevent the Convoy Effect by using a time quantum?",
        "stage_3_expected": ["yes", "prevents", "it does", "preempts"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "The **Convoy Effect** is a scheduling phenomenon primarily associated with FCFS where a CPU-heavy process with a large burst monopolizes the processor, causing a backlog of shorter, I/O-bound processes waiting in the Ready Queue.\n\n"
            "- **Consequences**: Extremely high average waiting times and low peripheral device utilization.\n"
            "- **Remedy**: Preemptive scheduling algorithms like Round Robin or SRTF."
        )
    },

    "multilevel_feedback_queue": {
        "id": "multilevel_feedback_queue",
        "display_name": "Multilevel Feedback Queue (MLFQ)",
        "topic": "Algorithms",
        "subtopic": "Adaptive Priority Queues",
        "keywords": ["multilevel feedback queue", "mlfq", "multilevel queue", "mlq"],
        "stage_1_analogy_question": "Imagine a supermarket checkout with an express lane (for 5 items or fewer) and a regular lane. If someone in the express lane suddenly starts unloading 50 more items, what should the cashier do to keep the express lane fair for others?",
        "stage_1_hint": "Should they let them stay in express or move them to the regular lane?",
        "stage_1_expected": ["move", "regular lane", "demote", "transfer", "send to back", "switch", "regular"],
        "stage_1_misconceptions": {
            "fixed": "Unlike standard MLQ, MLFQ dynamically shifts processes between queues based on their behavior!"
        },
        "stage_1_dont_know": "The cashier moves them to the regular lane so they don't block customers who genuinely only have 2 or 3 items!",
        "stage_2_explanation": "Spot on! That is the core idea of **Multilevel Feedback Queue (MLFQ)**: processes start in a high-priority queue with a short time quantum. If a process uses its entire quantum without finishing, it is demoted to a lower-priority queue with a longer quantum.",
        "stage_2_question": "Does MLFQ favor I/O-bound interactive processes or CPU-heavy batch processes for higher priority?",
        "stage_2_expected": ["i/o", "io", "interactive", "i/o-bound", "short"],
        "stage_2_misconceptions": {
            "kill": "Processes that use up their time quantum are demoted to a lower priority queue, not terminated."
        },
        "stage_3_explanation": "Exactly! Interactive processes give up the CPU quickly for user input, so they remain in the top, highly responsive queues.",
        "stage_3_question": "What mechanism does MLFQ use to prevent long-running batch processes in the lowest queues from starving?",
        "stage_3_expected": ["aging", "ageing", "priority boost", "boost"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Multilevel Feedback Queue (MLFQ)** is an adaptive priority scheduling algorithm that allows processes to move between queues based on their observed CPU burst behavior.\n\n"
            "- **Rules**: New processes enter Queue 0 (highest priority, smallest quantum). If a process consumes its full quantum, it is demoted. If it voluntarily yields for I/O, it remains at higher priority.\n"
            "- **Advantage**: Automatically favors short interactive jobs without requiring advance knowledge of burst durations.\n"
            "- **Starvation Prevention**: Periodic priority boosting (aging) promotes all waiting processes to Queue 0."
        )
    },

    "hrrn": {
        "id": "hrrn",
        "display_name": "Highest Response Ratio Next (HRRN)",
        "topic": "HRRN",
        "subtopic": "Starvation Prevention & Response Ratio",
        "keywords": ["hrrn", "highest response ratio next", "highest response ratio", "response ratio", "brinch hansen"],
        "stage_1_analogy_question": "Imagine a bakery where customers wait. If you only serve the quickest orders, someone waiting for hours never gets served. How could you balance how long someone has been waiting with how fast their order is?",
        "stage_1_hint": "Think about combining waiting time and service time.",
        "stage_1_expected": ["balance", "waiting time", "service time", "ratio", "wait time", "combine", "longer they wait", "wait", "wait + burst"],
        "stage_1_misconceptions": {
            "first come": "Serving strictly in arrival order is FCFS, which doesn't consider service duration at all! HRRN balances both.",
            "shortest": "Serving only shortest jobs is SJF, which can cause long jobs to starve!"
        },
        "stage_1_dont_know": "We could calculate a ratio that increases the longer someone waits, so even a larger order eventually rises to the front of the line!",
        "stage_2_explanation": "Spot on! That is the core insight of **Highest Response Ratio Next (HRRN)**. It uses the formula: Response Ratio $R = \\frac{W + S}{S} = 1 + \\frac{W}{S}$, where $W$ is waiting time and $S$ is service (burst) time. As waiting time $W$ grows, the ratio $R$ increases, preventing starvation.",
        "stage_2_question": "Is HRRN a preemptive or non-preemptive algorithm?",
        "stage_2_expected": ["non-preemptive", "non preemptive", "nonpreemptive", "not preemptive"],
        "stage_2_misconceptions": {
            "preemptive": "HRRN is non-preemptive! Recalculating response ratios continuously for every running millisecond would cause too much CPU scheduling overhead."
        },
        "stage_3_explanation": "Exactly right! HRRN is **non-preemptive** because continuously recomputing ratios on every clock tick would be computationally prohibitive.",
        "stage_3_question": "If all waiting processes arrive at the exact same moment (so waiting time $W=0$ for all of them), what algorithm does HRRN behave exactly like?",
        "stage_3_expected": ["sjf", "shortest job first", "shortest job"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Highest Response Ratio Next (HRRN)** is a non-preemptive scheduling algorithm developed by Brinch Hansen to eliminate starvation in SJF.\n\n"
            "- **Response Ratio Formula**: $R = \\frac{W + S}{S} = 1 + \\frac{W}{S}$, where $W$ = Waiting Time in Ready Queue, $S$ = Expected Service (Burst) Time.\n"
            "- **Properties**: Favors shorter jobs (smaller $S$), but long jobs cannot starve because their ratio increases as waiting time $W$ accumulates.\n"
            "- **Optimality**: Non-preemptive; if all $W=0$, HRRN is identical to Non-Preemptive SJF."
        )
    },

    "cfs": {
        "id": "cfs",
        "display_name": "Completely Fair Scheduler (CFS)",
        "topic": "Linux CFS",
        "subtopic": "Virtual Runtime & Red-Black Trees",
        "keywords": ["cfs", "completely fair scheduler", "completely fair", "vruntime", "virtual runtime", "red-black tree", "rbtree", "nice value", "nice level"],
        "stage_1_analogy_question": "Imagine sharing a single computer between three people. If you want everyone to get an exactly equal share of time, how would you track how much time each person has already received so the person with the least gets the next turn?",
        "stage_1_hint": "Think about tracking a virtual clock or tally of used time.",
        "stage_1_expected": ["track", "counter", "least", "tally", "record", "timer", "clock", "virtual", "spent least", "measure"],
        "stage_1_misconceptions": {
            "random": "Random selection doesn't guarantee fairness! Tracking accumulated time ensures everyone gets an equitable share.",
            "fixed queue": "A rigid circular queue doesn't adapt to dynamic priorities or different thread weights."
        },
        "stage_1_dont_know": "We can keep an exact tally of how much time each person has spent on the computer. Whenever the computer is free, whoever has the lowest tally gets to use it!",
        "stage_2_explanation": "Spot on! That is the principle behind Linux's default **Completely Fair Scheduler (CFS)**. It tracks an accurate metric called **virtual runtime (`vruntime`)** for each task. The scheduler always dispatches the task with the smallest `vruntime`.",
        "stage_2_question": "What balanced binary search tree data structure does Linux CFS use to store runnable processes and retrieve the task with the minimum `vruntime` in O(1) time?",
        "stage_2_expected": ["red-black tree", "rb tree", "red black tree", "rbtree", "binary search tree"],
        "stage_2_misconceptions": {
            "array": "An array requires O(N) scans to find the minimum! CFS uses a self-balancing red-black tree with a cached leftmost pointer."
        },
        "stage_3_explanation": "Exactly right! CFS stores tasks in a time-ordered **red-black tree**. The leftmost node has the smallest `vruntime` and is selected in O(1) time (or O(log N) tree update).",
        "stage_3_question": "Linux has 40 nice levels (from -20 to +19). If a process has a high nice value like +19 (very low priority), does its `vruntime` increase faster or slower than a standard process for each second of real CPU time?",
        "stage_3_expected": ["faster", "fast", "quicker", "rapidly"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "The **Completely Fair Scheduler (CFS)** is the default CPU scheduling algorithm in Linux (kernel 2.6.23 onwards).\n\n"
            "- **Core Metric**: **Virtual Runtime (`vruntime`)**, which measures the amount of CPU time consumed by a task scaled by its priority weight: $\\text{vruntime} \\mathrel{+}= \\Delta \\text{exec} \\times \\frac{\\text{NICE\\_0\\_LOAD}}{\\text{se->load.weight}}$.\n"
            "- **Data Structure**: Time-ordered **Red-Black Tree** (`rb_node`), with a cached pointer to the leftmost (minimum `vruntime`) task.\n"
            "- **Granularity**: Dynamically partitions latency target across runnable tasks, bounded by a minimum granularity."
        )
    },

    "real_time": {
        "id": "real_time",
        "display_name": "Real-Time Scheduling (RMS & EDF)",
        "topic": "Real-Time Scheduling",
        "subtopic": "Rate Monotonic & Earliest Deadline First",
        "keywords": ["real time", "real-time", "rms", "rate monotonic", "edf", "earliest deadline first", "hard real-time", "soft real-time", "deadline", "schedulability"],
        "stage_1_analogy_question": "Think of a hospital pacemaker or an aircraft flight controller versus a desktop video player. What is the fundamental difference if the flight controller is delayed by 10 milliseconds compared to the video player dropping a frame?",
        "stage_1_hint": "Think about life-critical consequences versus temporary video glitches.",
        "stage_1_expected": ["catastrophic", "dead", "crash", "life", "hard vs soft", "fatal", "strict", "deadline", "safety", "harm"],
        "stage_1_misconceptions": {
            "same": "They are completely different! A video glitch is mild quality degradation (soft real-time), whereas a flight control delay can cause a fatal crash (hard real-time)."
        },
        "stage_1_dont_know": "If a flight controller misses a deadline, the plane could crash (Hard Real-Time). If a video player is delayed, you just see a tiny stutter (Soft Real-Time). Deadlines are absolute in hard real-time!",
        "stage_2_explanation": "Spot on! In **Hard Real-Time**, missing a deadline produces total system failure, whereas **Soft Real-Time** allows occasional deadline misses with degraded quality.",
        "stage_2_question": "In Rate Monotonic Scheduling (RMS), static priorities are assigned based on task frequency. Do tasks with shorter periods (repeating very often) get higher priority or lower priority?",
        "stage_2_expected": ["higher", "high", "highest", "higher priority"],
        "stage_2_misconceptions": {
            "lower": "In RMS, Rate = 1/Period! Tasks that repeat more frequently (shorter period) must be served first, so shorter period = higher static priority."
        },
        "stage_3_explanation": "Exactly right! Under RMS, priority is inversely proportional to period: shorter period = higher priority.",
        "stage_3_question": "While RMS is static and subject to the Liu & Layland bound (approx 69.3%), Earliest Deadline First (EDF) assigns priority dynamically based on deadline closeness. What is the theoretical maximum CPU utilization bound achievable under EDF?",
        "stage_3_expected": ["100%", "100", "1.0", "1", "full", "full utilization"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Real-Time CPU Scheduling (RMS vs. EDF)**:\n\n"
            "- **Rate Monotonic Scheduling (RMS)**: Static-priority preemptive policy. Tasks with shorter periods $T_i$ receive higher static priorities. Schedulable if total utilization $U = \\sum \\frac{C_i}{T_i} \\le n(2^{1/n} - 1) \\to \\ln 2 \\approx 69.3\\%$.\n"
            "- **Earliest Deadline First (EDF)**: Dynamic-priority preemptive policy. The process whose absolute deadline is closest to current time receives the highest priority. Provably optimal: schedulable up to 100% CPU utilization ($U \\le 1.0$)."
        )
    },

    "multiprocessor": {
        "id": "multiprocessor",
        "display_name": "Multiprocessor & Thread Scheduling",
        "topic": "Multiprocessor Scheduling",
        "subtopic": "SQMS vs MQMS & Processor Affinity",
        "keywords": ["multiprocessor", "multicore", "smp", "multi-core", "affinity", "processor affinity", "sqms", "mqms", "work stealing", "numa", "gang scheduling"],
        "stage_1_analogy_question": "Imagine a kitchen with 4 cooks. Is it better to have all 4 cooks grab orders from a single shared order ticket board, or give each cook their own separate queue of orders?",
        "stage_1_hint": "Think about cooks bumping into each other trying to grab the same ticket (lock contention).",
        "stage_1_expected": ["separate", "own queue", "multiple", "both", "lock", "bump", "contention", "shared", "single", "own"],
        "stage_1_misconceptions": {
            "one": "In multiprocessor systems, multiple CPU cores execute different threads in parallel simultaneously rather than sharing just one active slot."
        },
        "stage_1_dont_know": "If they share one board, they constantly bump into each other and fight for the pen (lock contention). Giving each cook their own queue is much faster, but one cook might run out of work while another is swamped!",
        "stage_2_explanation": "Spot on! That is the classic trade-off between **Single-Queue Multiprocessor Scheduling (SQMS)** and **Multi-Queue Multiprocessor Scheduling (MQMS)**. SQMS has high lock contention and destroys cache affinity, whereas MQMS scales well with per-CPU queues.",
        "stage_2_question": "When a process continues running on the same CPU core so that its data remains hot in that core's hardware L1/L2 caches, what is that concept called?",
        "stage_2_expected": ["affinity", "processor affinity", "cpu affinity", "cache affinity"],
        "stage_2_misconceptions": {
            "caching": "Caching is the hardware mechanism, but the scheduler's policy to keep a task bound to a specific core is called Processor Affinity."
        },
        "stage_3_explanation": "Exactly right! **Processor Affinity** (soft or hard) keeps threads on the same core to avoid the heavy memory latency penalty of reloading CPU caches.",
        "stage_3_question": "In MQMS, if Core 1 runs out of work while Core 2 has 10 waiting tasks, what mechanism allows Core 1 to take tasks from Core 2's queue?",
        "stage_3_expected": ["work stealing", "stealing", "migration", "pull migration", "push migration"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Multiprocessor CPU Scheduling**:\n\n"
            "- **Architectures**: SQMS (Single-Queue, bottlenecked by spinlock contention and cache thrashing) vs. MQMS (Multi-Queue, per-core queues with high scalability).\n"
            "- **Processor Affinity**: Favoring executing a process on the same CPU core to preserve warm L1/L2 cache lines (Soft Affinity = OS preference, Hard Affinity = `sched_setaffinity`).\n"
            "- **Load Balancing**: Work Stealing (underloaded CPU pulls tasks from overloaded queues) and Push Migration (periodic kernel balancing thread)."
        )
    },

    "lottery_stride": {
        "id": "lottery_stride",
        "display_name": "Lottery and Stride Scheduling",
        "topic": "Proportional Share Scheduling",
        "subtopic": "Lottery Tickets & Stride Scheduling",
        "keywords": ["lottery", "stride", "lottery scheduling", "stride scheduling", "tickets", "proportional share", "lottery tickets"],
        "stage_1_analogy_question": "Imagine a raffle where you hold 75 tickets and your friend holds 25 tickets. If we draw a ticket with replacement 100 times, roughly what fraction of the turns will you get?",
        "stage_1_hint": "Think about the proportion 75 out of 100.",
        "stage_1_expected": ["75%", "75", "three quarters", "3/4", "most", "proportional", "75 percent"],
        "stage_1_misconceptions": {
            "equal": "Tickets are allocated proportionally based on desired resource share, not equally."
        },
        "stage_1_dont_know": "Because you have 75% of the tickets, you will win approximately 75% of the draws! That is proportional share.",
        "stage_2_explanation": "Spot on! That is **Lottery Scheduling**: processes hold lottery tickets, and every scheduling quantum the OS picks a random winning ticket. The process holding that ticket runs, providing randomized proportional CPU sharing.",
        "stage_2_question": "While Lottery scheduling is randomized and has statistical variance over short timeframes, what deterministic proportional-share algorithm calculates a precise 'stride' value for each task and always runs the task with the lowest pass value?",
        "stage_2_expected": ["stride", "stride scheduling"],
        "stage_2_misconceptions": {
            "random": "Stride scheduling is completely deterministic, unlike lottery scheduling which is randomized."
        },
        "stage_3_explanation": "Exactly right! **Stride Scheduling** is completely deterministic: Stride $S = L / \\text{Tickets}$. Each time a task runs, its pass value advances by its stride, achieving precise proportional shares with zero randomness.",
        "stage_3_question": "In Stride scheduling, does a task with MORE tickets have a larger stride or a smaller stride?",
        "stage_3_expected": ["smaller", "small", "lower", "less"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**Proportional-Share Scheduling (Lottery & Stride)**:\n\n"
            "- **Lottery Scheduling**: Probabilistic algorithm where tickets represent CPU shares. At each time slice, a pseudo-random winning ticket is drawn. Over time, CPU time converges to ticket ratio.\n"
            "- **Stride Scheduling**: Deterministic variant. Stride $S_i = \\frac{\\text{Large Constant } L}{\\text{Tickets } T_i}$. The scheduler maintains a `pass` counter for each process, dispatches the process with $\\min(pass)$, and updates $pass_i \\mathrel{+}= S_i$."
        )
    },

    "cpu_io_bursts": {
        "id": "cpu_io_bursts",
        "display_name": "CPU and I/O Burst Cycle",
        "topic": "Fundamentals",
        "subtopic": "CPU vs I/O Bound Processes",
        "keywords": ["cpu burst", "io burst", "i/o burst", "cpu bound", "io bound", "burst cycle", "cpu vs io"],
        "stage_1_analogy_question": "Think about a text editor where you type a character, wait a few seconds, type another character, and occasionally save. Does this program spend most of its life computing calculations or waiting for human input?",
        "stage_1_hint": "Think about the gap between keystrokes.",
        "stage_1_expected": ["waiting", "input", "human", "i/o", "io", "waiting for input", "user"],
        "stage_1_misconceptions": {
            "only cpu": "Real programs alternate between CPU calculation bursts and I/O wait bursts."
        },
        "stage_1_dont_know": "It spends 99% of its time waiting for you to press the next key! That means it is an I/O-bound task.",
        "stage_2_explanation": "Spot on! Processes alternate between CPU execution bursts and I/O wait bursts in a continuous **CPU-I/O burst cycle**. Programs with many short CPU bursts and long I/O waits are **I/O-bound**, while number-crunching tasks with massive continuous computing are **CPU-bound**.",
        "stage_2_question": "To keep an interactive system feeling responsive and ensure storage devices are kept busy, should the CPU scheduler prioritize I/O-bound processes or CPU-bound processes?",
        "stage_2_expected": ["i/o", "io", "i/o-bound", "io bound", "interactive"],
        "stage_2_misconceptions": {
            "cpu first": "Prioritizing short I/O bursts keeps disks and networks busy while providing responsive UI."
        },
        "stage_3_explanation": "Exactly right! Prioritizing I/O-bound processes gives rapid UI responsiveness and allows the I/O devices to operate concurrently with the CPU.",
        "stage_3_question": "When an I/O-bound process finishes waiting for a disk read or network packet, what queue in memory does the interrupt handler place it into?",
        "stage_3_expected": ["ready queue", "ready"],
        "stage_4_worked_example_trigger": True,
        "direct_definition": (
            "**CPU and I/O Burst Cycle**:\n\n"
            "- **Cycle**: Process execution consists of alternating cycles of CPU execution (CPU burst) and I/O wait (I/O burst).\n"
            "- **Process Types**: \n"
            "  * **I/O-bound**: Many short CPU bursts, frequent I/O waits (e.g., text editors, web servers). Priority should be higher to maximize concurrency.\n"
            "  * **CPU-bound**: Few very long CPU bursts, heavy computation (e.g., scientific simulations, video rendering).\n"
            "- **Frequency**: CPU burst distribution is hyperexponential—there is a large frequency of very short bursts and a small frequency of long bursts."
        )
    }
}


class SocraticEngine:
    """Orchestrates interactive, question-driven tutoring dialogues with real-life analogies."""

    @classmethod
    def detect_concept(cls, text: str) -> Optional[str]:
        """Identifies which supported OS concept the student is inquiring about."""
        t = text.lower().strip()

        # Check explicit display_name or id first
        for concept_id, data in SOCRATIC_CURRICULUM.items():
            if data["display_name"].lower() in t or data["id"] in t:
                return concept_id

        # Check explicit keywords
        for concept_id, data in SOCRATIC_CURRICULUM.items():
            for kw in data["keywords"]:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, t):
                    return concept_id

        # Fallback keyword checks
        if "quantum" in t or "round robin" in t or "rr" in t.split():
            return "round_robin"
        elif "fcfs" in t or "first come" in t:
            return "fcfs"
        elif "srtf" in t or "shortest remaining" in t:
            return "srtf"
        elif "sjf" in t or "shortest job" in t:
            return "sjf"
        elif "hrrn" in t or "response ratio" in t:
            return "hrrn"
        elif re.search(r"\bcfs\b", t) or "completely fair" in t or "vruntime" in t:
            return "cfs"
        elif "real time" in t or "real-time" in t or "rms" in t.split() or "edf" in t.split():
            return "real_time"
        elif "multiprocessor" in t or "multicore" in t or "sqms" in t or "mqms" in t or "affinity" in t:
            return "multiprocessor"
        elif "lottery" in t or "stride" in t:
            return "lottery_stride"
        elif "cpu burst" in t or "io burst" in t or "i/o burst" in t or "burst cycle" in t:
            return "cpu_io_bursts"
        elif "priority" in t:
            return "priority"
        elif "preempt" in t:
            return "preemption"
        elif "starv" in t or "aging" in t or "ageing" in t:
            return "starvation_and_aging"
        elif "context switch" in t or "save state" in t:
            return "context_switching"
        elif "pcb" in t or "process control block" in t:
            return "pcb"
        elif "dispatcher" in t:
            return "dispatcher"
        elif "ready queue" in t or "waiting queue" in t:
            return "ready_vs_waiting_queue"
        elif "turnaround" in t or "waiting time" in t or "tat" in t.split() or "wt" in t.split():
            return "turnaround_time_and_waiting_time"
        elif "convoy" in t:
            return "convoy_effect"
        elif "multilevel" in t or "mlfq" in t:
            return "multilevel_feedback_queue"

        return None

    @classmethod
    def get_concept_for_question(cls, question_text: str) -> Optional[str]:
        """Maps any Socratic curriculum question back to its concept_id."""
        if not question_text:
            return None
        q_norm = re.sub(r"[^a-z0-9 ]+", " ", question_text.lower()).strip()
        for cid, d in SOCRATIC_CURRICULUM.items():
            for stage_key in ["stage_1_analogy_question", "stage_2_question", "stage_3_question"]:
                st_q = d.get(stage_key, "")
                if st_q:
                    s_norm = re.sub(r"[^a-z0-9 ]+", " ", st_q.lower()).strip()
                    if s_norm and (s_norm == q_norm or s_norm in q_norm or q_norm in s_norm):
                        return cid
        return None

    @classmethod
    def is_direct_answer_request(cls, text: str) -> bool:
        """Determines if the user explicitly requested a direct factual definition or formula."""
        t = text.lower().strip()
        direct_triggers = [
            "just give me the definition", "give me the definition", "just the definition",
            "explain directly", "just explain it directly", "explain it directly",
            "explain completely in one answer", "explain the whole algorithm in detail",
            "just give me the formula", "give me the formula", "formula for",
            "give me proper notes", "direct answer", "just tell me"
        ]
        return any(tr in t for tr in direct_triggers)

    @classmethod
    def is_worked_example_request(cls, text: str) -> bool:
        """Detects requests for worked numerical examples."""
        t = text.lower().strip()
        example_triggers = [
            "take an example", "give an example", "give me an example", "show an example", "show me an example",
            "worked example", "explain with an example", "example with gantt", "numerical example",
            "show me a problem", "take an example for", "example of", "an example of", "example for"
        ]
        return any(tr in t for tr in example_triggers)

    @classmethod
    def start_socratic_lesson(
        cls,
        concept_id: str,
        learner_state: LearnerStateModel
    ) -> TutorStructuredResponse:
        """Initiates an interactive Socratic dialogue with the Stage 1 real-life analogy guiding question."""
        data = SOCRATIC_CURRICULUM[concept_id]
        question = data["stage_1_analogy_question"]

        learner_state.current_topic = data.get("display_name", data["topic"])
        learner_state.current_subtopic = data["subtopic"]
        learner_state.pending_question = question
        learner_state.last_question_asked = question
        learner_state.lesson_stage = "knowledge_assessment"
        learner_state.next_teaching_step = f"Assess student intuition on {data['display_name']} via analogy"

        return TutorStructuredResponse(
            message=question,
            mode=TutoringMode.SOCRATIC,
            topic=data["topic"],
            action=TutorAction.ASK_QUESTION,
            question=question,
            hint=data.get("stage_1_hint"),
            misconception=None,
            concepts_demonstrated=[],
            concepts_needing_review=[],
            source_ids=[],
            requires_calculation=False
        )

    @classmethod
    def get_direct_explanation(
        cls,
        concept_id: str,
        learner_state: LearnerStateModel
    ) -> TutorStructuredResponse:
        """Provides direct factual explanation when explicitly requested by the student."""
        data = SOCRATIC_CURRICULUM[concept_id]
        learner_state.current_topic = data["topic"]
        learner_state.current_subtopic = data["subtopic"]
        learner_state.last_concept_explained = f"Direct definition of {data['display_name']}"
        learner_state.lesson_stage = "explanation"
        learner_state.pending_question = None

        return TutorStructuredResponse(
            message=data["direct_definition"],
            mode=TutoringMode.EXPLANATION,
            topic=data["topic"],
            action=TutorAction.EXPLAIN_CONCEPT,
            question=None,
            hint=None,
            misconception=None,
            concepts_demonstrated=[f"{concept_id}_definition"],
            concepts_needing_review=[],
            source_ids=[],
            requires_calculation=False
        )

    @classmethod
    def evaluate_socratic_turn(
        cls,
        concept_id: str,
        user_answer: str,
        learner_state: LearnerStateModel
    ) -> Optional[TutorStructuredResponse]:
        """Evaluates student response against current pending question and advances the dialogue."""
        if concept_id not in SOCRATIC_CURRICULUM:
            return None

        data = SOCRATIC_CURRICULUM[concept_id]
        learner_state.current_topic = data.get("display_name", data["topic"])
        ans_lower = user_answer.lower().strip()
        pending_q = (learner_state.pending_question or "").lower().strip()

        def _norm(t: str) -> str:
            return re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower()).strip()

        def _matches(p: str, target: str) -> bool:
            np = _norm(p)
            nt = _norm(target)
            if not np or not nt:
                return False
            return np == nt or np in nt or nt in np

        # 1. Check for Stage 1 Analogy Question
        if _matches(pending_q, data.get("stage_1_analogy_question", "")):
            # User says "I don't know" or asks for help
            if any(w in ans_lower for w in ["don't know", "dont know", "no idea", "not sure", "help me", "cant answer", "can't answer", "nothing"]):
                dont_know_text = data.get("stage_1_dont_know", "Let's build the intuition step-by-step.")
                msg = f"No problem at all! {dont_know_text}\n\n{data['stage_2_question']}"
                next_q = data["stage_2_question"]
                learner_state.pending_question = next_q
                learner_state.last_question_asked = next_q
                learner_state.lesson_stage = "guided_inquiry"
                return TutorStructuredResponse(
                    message=msg,
                    mode=TutoringMode.SOCRATIC,
                    topic=data["topic"],
                    action=TutorAction.ASK_QUESTION,
                    question=next_q,
                    hint=data.get("stage_1_hint"),
                    misconception=None,
                    concepts_demonstrated=[],
                    concepts_needing_review=[],
                    source_ids=[],
                    requires_calculation=False
                )

            # Check for Stage 1 Correct / Intuitive Understanding first
            if any(kw in ans_lower for kw in data.get("stage_1_expected", [])):
                msg = f"{data['stage_2_explanation']}\n\n{data['stage_2_question']}"
                next_q = data["stage_2_question"]
                learner_state.pending_question = next_q
                learner_state.last_question_asked = next_q
                learner_state.lesson_stage = "guided_inquiry"
                return TutorStructuredResponse(
                    message=msg,
                    mode=TutoringMode.SOCRATIC,
                    topic=data["topic"],
                    action=TutorAction.ASK_QUESTION,
                    question=next_q,
                    hint="Think about what happens to unfinished tasks.",
                    misconception=None,
                    concepts_demonstrated=[f"{concept_id}_intuition"],
                    concepts_needing_review=[],
                    source_ids=[],
                    requires_calculation=False
                )

            # Check for Stage 1 Misconceptions
            for mis_kw, mis_expl in data.get("stage_1_misconceptions", {}).items():
                if mis_kw in ans_lower:
                    feedback = f"⚠️ {mis_expl}\n\n{data['stage_1_analogy_question']}"
                    next_q = data["stage_1_analogy_question"]
                    learner_state.pending_question = next_q
                    learner_state.last_question_asked = next_q
                    return TutorStructuredResponse(
                        message=feedback,
                        mode=TutoringMode.SOCRATIC,
                        topic=data["topic"],
                        action=TutorAction.ASK_QUESTION,
                        question=next_q,
                        hint=data.get("stage_1_hint"),
                        misconception=mis_expl,
                        concepts_demonstrated=[],
                        concepts_needing_review=[f"{concept_id}_basics"],
                        source_ids=[],
                        requires_calculation=False
                    )

            # Fallback for unexpected Stage 1 answer: acknowledge warmly and guide forward with Stage 2
            hint_text = data.get("stage_1_hint", "think about the core trade-off or mechanism")
            fallback_msg = (
                f"**Interesting perspective!** In {data['display_name']}, here is the core intuition: {hint_text}.\n\n"
                f"{data['stage_2_explanation']}\n\n{data['stage_2_question']}"
            )
            next_q = data["stage_2_question"]
            learner_state.pending_question = next_q
            learner_state.last_question_asked = next_q
            learner_state.lesson_stage = "guided_inquiry"
            return TutorStructuredResponse(
                message=fallback_msg,
                mode=TutoringMode.SOCRATIC,
                topic=data["topic"],
                action=TutorAction.ASK_QUESTION,
                question=next_q,
                hint="Think about what happens to unfinished tasks.",
                misconception=None,
                concepts_demonstrated=[f"{concept_id}_intuition"],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False
            )

        # 2. Check for Stage 2 Response (Mechanism & Terminology)
        if "stage_2_question" in data and _matches(pending_q, data["stage_2_question"]):
            # Check for Stage 2 Correct answer first
            if any(kw in ans_lower for kw in data.get("stage_2_expected", [])):
                msg = f"{data['stage_3_explanation']}\n\n{data['stage_3_question']}"
                next_q = data["stage_3_question"]
                learner_state.pending_question = next_q
                learner_state.last_question_asked = next_q
                learner_state.lesson_stage = "guided_practice"
                return TutorStructuredResponse(
                    message=msg,
                    mode=TutoringMode.SOCRATIC,
                    topic=data["topic"],
                    action=TutorAction.ASK_QUESTION,
                    question=next_q,
                    hint="Consider the impact on the other processes.",
                    misconception=None,
                    concepts_demonstrated=[f"{concept_id}_queue_mechanism"],
                    concepts_needing_review=[],
                    source_ids=[],
                    requires_calculation=False
                )

            # Check misconceptions
            for mis_kw, mis_expl in data.get("stage_2_misconceptions", {}).items():
                if mis_kw in ans_lower:
                    feedback = f"⚠️ {mis_expl}\n\n{data['stage_2_question']}"
                    return TutorStructuredResponse(
                        message=feedback,
                        mode=TutoringMode.SOCRATIC,
                        topic=data["topic"],
                        action=TutorAction.ASK_QUESTION,
                        question=data["stage_2_question"],
                        hint=None,
                        misconception=mis_expl,
                        concepts_demonstrated=[],
                        concepts_needing_review=[f"{concept_id}_mechanism"],
                        source_ids=[],
                        requires_calculation=False
                    )

            if any(w in ans_lower for w in ["don't know", "dont know", "no idea", "not sure", "tell me", "what happens"]):
                if concept_id == "round_robin":
                    dont_know_msg = "When its time quantum expires, the unfinished process is paused (preempted) and moved to the back of the circular Ready Queue so the next process gets the CPU."
                else:
                    dont_know_msg = f"In {data['display_name']}, here is how it works: {data['stage_3_explanation'].split('.')[0]}."
                msg = f"No problem! {dont_know_msg}\n\n{data['stage_3_question']}"
                next_q = data["stage_3_question"]
                learner_state.pending_question = next_q
                learner_state.last_question_asked = next_q
                learner_state.lesson_stage = "guided_practice"
                return TutorStructuredResponse(
                    message=msg,
                    mode=TutoringMode.SOCRATIC,
                    topic=data["topic"],
                    action=TutorAction.ASK_QUESTION,
                    question=next_q,
                    hint="Consider the impact on the other processes.",
                    misconception=None,
                    concepts_demonstrated=[f"{concept_id}_queue_mechanism"],
                    concepts_needing_review=[],
                    source_ids=[],
                    requires_calculation=False
                )

            # Clarifying prompt if response was unexpected
            if concept_id == "round_robin":
                clarifying_prompt = (
                    "Think about what happens to the unfinished process: the CPU switches to the next task, "
                    "but does that unfinished process get deleted, or does it wait at the back of the Ready Queue for another turn?"
                )
            else:
                hint_text = data.get("stage_1_hint", "Think about what the scheduler does next.")
                clarifying_prompt = f"Good thinking! In {data['display_name']}, consider this: {hint_text}\n\n{data['stage_2_question']}"
            return TutorStructuredResponse(
                message=clarifying_prompt,
                mode=TutoringMode.SOCRATIC,
                topic=data["topic"],
                action=TutorAction.ASK_QUESTION,
                question=data["stage_2_question"],
                hint="Think about where unfinished processes wait.",
                misconception=None,
                concepts_demonstrated=[],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False
            )

        # 3. Check for Stage 3 Response (Phenomenon / Equivalence / Trade-off)
        if "stage_3_question" in data and _matches(pending_q, data["stage_3_question"]):
            if any(kw in ans_lower for kw in data.get("stage_3_expected", [])):
                followup = "Would you like to walk through a concrete numerical example with a Gantt chart to see this in action?"
                msg = (
                    f"Precisely! You've nailed the core concept and its trade-offs.\n\n"
                    f"{followup}"
                )
                learner_state.pending_question = followup
                learner_state.last_question_asked = followup
                learner_state.lesson_stage = "worked_example_prompt"
                return TutorStructuredResponse(
                    message=msg,
                    mode=TutoringMode.SOCRATIC,
                    topic=data["topic"],
                    action=TutorAction.ASK_QUESTION,
                    question=followup,
                    hint="Type 'yes' or 'show example'.",
                    misconception=None,
                    concepts_demonstrated=[f"{concept_id}_tradeoffs"],
                    concepts_needing_review=[],
                    source_ids=[],
                    requires_calculation=False
                )

            if any(w in ans_lower for w in ["don't know", "dont know", "no idea", "not sure", "tell me", "which"]):
                if concept_id == "round_robin":
                    explanation = "If the time quantum is larger than the longest CPU burst, no process ever gets preempted—each process runs to completion in arrival order, making Round Robin equivalent to **First-Come, First-Served (FCFS)**."
                elif "stage_3_dont_know" in data:
                    explanation = data["stage_3_dont_know"]
                else:
                    target_val = data.get("stage_3_expected", ["this trade-off"])[0]
                    explanation = f"In {data['display_name']}, the key factor is **{target_val}**."
                followup = "Would you like to walk through a concrete numerical example with a Gantt chart to see this in action?"
                msg = f"{explanation}\n\n{followup}"
                learner_state.pending_question = followup
                learner_state.last_question_asked = followup
                learner_state.lesson_stage = "worked_example_prompt"
                return TutorStructuredResponse(
                    message=msg,
                    mode=TutoringMode.SOCRATIC,
                    topic=data["topic"],
                    action=TutorAction.ASK_QUESTION,
                    question=followup,
                    hint="Type 'yes' or 'show example'.",
                    misconception=None,
                    concepts_demonstrated=[f"{concept_id}_tradeoffs"],
                    concepts_needing_review=[],
                    source_ids=[],
                    requires_calculation=False
                )

            # Fallback for unexpected Stage 3 answer: acknowledge, explain the trade-off, and offer worked example
            target_val = data.get("stage_3_expected", ["this trade-off"])[0]
            explanation = f"**Good attempt!** In {data['display_name']}, the key factor to keep in mind is **{target_val}**. {data['stage_3_explanation']}"
            followup = "Would you like to walk through a concrete numerical example with a Gantt chart to see this in action?"
            msg = f"{explanation}\n\n{followup}"
            learner_state.pending_question = followup
            learner_state.last_question_asked = followup
            learner_state.lesson_stage = "worked_example_prompt"
            return TutorStructuredResponse(
                message=msg,
                mode=TutoringMode.SOCRATIC,
                topic=data["topic"],
                action=TutorAction.ASK_QUESTION,
                question=followup,
                hint="Type 'yes' or 'show example'.",
                misconception=None,
                concepts_demonstrated=[f"{concept_id}_tradeoffs"],
                concepts_needing_review=[],
                source_ids=[],
                requires_calculation=False
            )

        return None
