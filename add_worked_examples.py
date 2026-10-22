with open('app/core/tutoring_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''        try:
            # Select canonical algorithm & processes
            if "hrrn" in topic_lower or "response ratio" in topic_lower:'''

replacement = '''        try:
            # Special non-classic algorithms with dedicated structural worked examples
            if "mlfq" in topic_lower or "multilevel" in topic_lower:
                ascii_chart = (
                    "| P1 (Q0: 2ms) | P2 (Q0: 2ms) | P3 (Q0: 1ms) | P1 (Q1: 4ms) | P2 (Q1: 2ms) | P1 (Q2: 1ms) |\\n"
                    "0              2              4              5              9              11             12"
                )
                q_text = "Notice how short interactive job P3 completed at t=5 ms in top Queue Q0 without ever being demoted, while long CPU job P1 descended to Q2. What mechanism does MLFQ use to ensure that demoted jobs in Q2 do not starve if new interactive jobs keep arriving?"
                formatted_md = (
                    "### Worked Example: Multilevel Feedback Queue (MLFQ)\\n\\n"
                    "**Queue Configuration:**\\n"
                    "- **Queue 0 ($Q_0$)**: Highest Priority, Round Robin with Time Quantum $q = 2$ ms\\n"
                    "- **Queue 1 ($Q_1$)**: Medium Priority, Round Robin with Time Quantum $q = 4$ ms\\n"
                    "- **Queue 2 ($Q_2$)**: Lowest Priority, First-Come First-Served (FCFS)\\n\\n"
                    "| Process | Arrival Time (AT) | Burst Time (BT) |\\n"
                    "| :--- | :--- | :--- |\\n"
                    "| **P1** | 0 ms | 7 ms (CPU-bound) |\\n"
                    "| **P2** | 1 ms | 4 ms (Mixed CPU/IO) |\\n"
                    "| **P3** | 2 ms | 1 ms (Short Interactive) |\\n\\n"
                    "#### Queue Transitions & Scheduling Timeline:\\n"
                    "* **t = 0 - 2 ms**: **P1** enters $Q_0$ and executes for its 2 ms quantum. Remaining burst: 5 ms. Consumed full quantum $\\\\to$ **demoted to $Q_1$**.\\n"
                    "* **t = 2 - 4 ms**: **P2** (arrived at $t=1$) is at head of $Q_0$. Executes for 2 ms. Remaining burst: 2 ms. Consumed full quantum $\\\\to$ **demoted to $Q_1$**.\\n"
                    "* **t = 4 - 5 ms**: **P3** (arrived at $t=2$) is in $Q_0$. Executes for 1 ms and **completes at $t=5$ ms**! It finishes in the top queue without ever demoting.\\n"
                    "* **t = 5 - 9 ms**: $Q_0$ is empty. Scheduler examines $Q_1$. **P1** executes for its 4 ms quantum. Remaining burst: 1 ms $\\\\to$ **demoted to $Q_2$**.\\n"
                    "* **t = 9 - 11 ms**: **P2** executes in $Q_1$ for its remaining 2 ms and **completes at $t=11$ ms**.\\n"
                    "* **t = 11 - 12 ms**: $Q_0$ and $Q_1$ are empty. **P1** executes in $Q_2$ for its final 1 ms and **completes at $t=12$ ms**.\\n\\n"
                    "#### Gantt Chart:\\n"
                    f"```text\\n{ascii_chart}\\n```\\n\\n"
                    "#### Step-by-Step Metric Calculations:\\n"
                    "* **P3**: $\\\\text{CT} = 5$ ms, $\\\\text{TAT} = 5 - 2 = 3$ ms, $\\\\text{WT} = 3 - 1 = 2$ ms, $\\\\text{RT} = 4 - 2 = 2$ ms\\n"
                    "* **P2**: $\\\\text{CT} = 11$ ms, $\\\\text{TAT} = 11 - 1 = 10$ ms, $\\\\text{WT} = 10 - 4 = 6$ ms, $\\\\text{RT} = 2 - 1 = 1$ ms\\n"
                    "* **P1**: $\\\\text{CT} = 12$ ms, $\\\\text{TAT} = 12 - 0 = 12$ ms, $\\\\text{WT} = 12 - 7 = 5$ ms, $\\\\text{RT} = 0 - 0 = 0$ ms\\n\\n"
                    "* **Average Turnaround Time**: 8.33 ms\\n"
                    "* **Average Waiting Time**: 4.33 ms\\n"
                    "* **CPU Utilization**: 100.0%\\n\\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: mlfq\\nProcesses: ['P1', 'P2', 'P3']\\nAverages: TAT=8.33, WT=4.33"
                return summary, ascii_chart, formatted_md

            if re.search(r"\\\\bcfs\\\\b", topic_lower) or "completely fair" in topic_lower:
                ascii_chart = (
                    "| P2 (nice -5: 6ms) | P1 (nice 0: 4ms) | P3 (nice +5: 2ms) |\\n"
                    "0                   6                  10                 12"
                )
                q_text = "Notice how high-priority process P2 (nice -5) received 6 ms of CPU time while low-priority P3 (nice +5) received only 2 ms, yet both progressed their virtual runtimes. In CFS, does a negative nice value make vruntime grow faster or slower than real execution time?"
                formatted_md = (
                    "### Worked Example: Linux Completely Fair Scheduler (CFS)\\n\\n"
                    "**Configuration & Task Weights ($NICE\\\\_0\\\\_LOAD = 1024$):**\\n"
                    "- Target Latency: 12 ms across 3 runnable tasks (Total Weight $W = 1024 + 3121 + 335 = 4480$)\\n\\n"
                    "| Task | Nice Value | Kernel Weight ($w_i$) | Allocated Time Slice | Initial $vruntime$ |\\n"
                    "| :--- | :--- | :--- | :--- | :--- |\\n"
                    "| **P1** | 0 (Normal) | 1024 | $12 \\\\times \\\\frac{1024}{4480} = 2.74 \\\\approx 4$ ms | 0.00 ms |\\n"
                    "| **P2** | -5 (High Priority) | 3121 | $12 \\\\times \\\\frac{3121}{4480} = 8.36 \\\\approx 6$ ms | 0.00 ms |\\n"
                    "| **P3** | +5 (Low Priority) | 335 | $12 \\\\times \\\\frac{335}{4480} = 0.90 \\\\approx 2$ ms | 0.00 ms |\\n\\n"
                    "#### Red-Black Tree Scheduling Mechanics:\\n"
                    "* CFS always selects the task with the **smallest virtual runtime (`vruntime`)**, located at the leftmost node of the Red-Black Tree.\\n"
                    "* Virtual runtime formula: $\\\\Delta vruntime = \\\\Delta \\\\text{exec\\\\_time} \\\\times \\\\frac{1024}{w_i}$\\n"
                    "* **t = 0 - 6 ms**: **P2** executes for 6 ms. $\\\\Delta vruntime = 6 \\\\times \\\\frac{1024}{3121} = 1.97$ ms. New $vruntime = 1.97$ ms.\\n"
                    "* **t = 6 - 10 ms**: P1 is now leftmost ($vruntime = 0 < 1.97$). **P1** runs for 4 ms. $\\\\Delta vruntime = 4 \\\\times \\\\frac{1024}{1024} = 4.00$ ms. New $vruntime = 4.00$ ms.\\n"
                    "* **t = 10 - 12 ms**: P3 is now leftmost ($vruntime = 0 < 1.97 < 4.00$). **P3** runs for 2 ms. $\\\\Delta vruntime = 2 \\\\times \\\\frac{1024}{335} = 6.11$ ms. New $vruntime = 6.11$ ms.\\n\\n"
                    "#### Gantt Chart:\\n"
                    f"```text\\n{ascii_chart}\\n```\\n\\n"
                    "#### Virtual Runtime Progression Summary:\\n"
                    "* **P2 (nice -5)**: Executed 6 ms, ending $vruntime = 1.97$ ms (grew much slower than real time!)\\n"
                    "* **P1 (nice 0)**: Executed 4 ms, ending $vruntime = 4.00$ ms (grew 1:1 with real time)\\n"
                    "* **P3 (nice +5)**: Executed 2 ms, ending $vruntime = 6.11$ ms (grew much faster than real time!)\\n\\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: linux_cfs\\nProcesses: ['P1', 'P2', 'P3']\\nWeights: [1024, 3121, 335]"
                return summary, ascii_chart, formatted_md

            if "real" in topic_lower or "rms" in topic_lower or "edf" in topic_lower:
                ascii_chart = (
                    "| T1 (1ms) | T2 (2ms) | Idle (1ms) | T1 (1ms) | Idle (1ms) | T2 (2ms) | T1 (1ms) | Idle (3ms) |\\n"
                    "0          1          3            4          5            6          8          9           12"
                )
                q_text = "Notice how tau_1 was assigned higher priority than tau_2 because its period (4 ms) is shorter than tau_2's period (6 ms). If tau_2 were running at t=4 ms when tau_1 releases a new job, what would happen under preemptive RMS?"
                formatted_md = (
                    "### Worked Example: Real-Time Rate Monotonic Scheduling (RMS)\\n\\n"
                    "**Task Set Specifications:**\\n"
                    "- $\\\\tau_1$: Period $T_1 = 4$ ms, Execution Capacity $C_1 = 1$ ms (Frequency = 0.25)\\n"
                    "- $\\\\tau_2$: Period $T_2 = 6$ ms, Execution Capacity $C_2 = 2$ ms (Frequency = 0.167)\\n"
                    "- **Total CPU Utilization**: $U = \\\\frac{C_1}{T_1} + \\\\frac{C_2}{T_2} = \\\\frac{1}{4} + \\\\frac{2}{6} = 0.25 + 0.333 = 0.583$ (58.3%)\\n"
                    "- **Liu & Layland Schedulability Bound**: $U \\\\le 2(2^{1/2} - 1) \\\\approx 0.828$ (82.8%). Since $0.583 \\\\le 0.828$, this task set is **guaranteed schedulable** with zero missed deadlines!\\n\\n"
                    "#### Static Priority Assignment:\\n"
                    "* Rate Monotonic rule: Shorter Period = Higher Priority $\\\\implies \\\\text{Priority}(\\\\tau_1) > \\\\text{Priority}(\\\\tau_2)$\\n"
                    "* Hyperperiod $H = \\\\text{lcm}(T_1, T_2) = \\\\text{lcm}(4, 6) = 12$ ms.\\n\\n"
                    "#### Execution Timeline (Over 12 ms Hyperperiod):\\n"
                    "* **t = 0 ms**: Both tasks release jobs. $\\\\tau_1$ has higher priority and executes from $0 \\\\to 1$ ms. Completes at $t=1$ ms.\\n"
                    "* **t = 1 - 3 ms**: $\\\\tau_2$ executes its 2 ms burst. Completes at $t=3$ ms.\\n"
                    "* **t = 3 - 4 ms**: Both tasks finished for this cycle. CPU is **Idle**.\\n"
                    "* **t = 4 - 5 ms**: $\\\\tau_1$ releases second job at $t=4$ ms. Executes from $4 \\\\to 5$ ms. Completes at $t=5$ ms.\\n"
                    "* **t = 5 - 6 ms**: CPU is **Idle**.\\n"
                    "* **t = 6 - 8 ms**: $\\\\tau_2$ releases second job at $t=6$ ms. Executes from $6 \\\\to 8$ ms. Completes at $t=8$ ms.\\n"
                    "* **t = 8 - 9 ms**: $\\\\tau_1$ releases third job at $t=8$ ms. Executes from $8 \\\\to 9$ ms. Completes at $t=9$ ms.\\n"
                    "* **t = 9 - 12 ms**: CPU is **Idle** until hyperperiod completes at $t=12$ ms.\\n\\n"
                    "#### Gantt Chart:\\n"
                    f"```text\\n{ascii_chart}\\n```\\n\\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: real_time_rms\\nTasks: ['T1', 'T2']\\nUtilization: 0.583"
                return summary, ascii_chart, formatted_md

            if "multiprocessor" in topic_lower or "multicore" in topic_lower:
                ascii_chart = (
                    "Core 0: | P1 (4ms) | P2 (3ms) | P4 [Stolen] (2ms) |\\n"
                    "        0          4          7                   9\\n"
                    "Core 1: | P3 (2ms) | P4 (5ms, migrates at t=7)    |\\n"
                    "        0          2          7                   7"
                )
                q_text = "Notice how Core 0 finished its local queue at t=7 ms and stole the remaining 2 ms of P4 from Core 1's queue. What trade-off occurs when P4 migrates from Core 1 to Core 0?"
                formatted_md = (
                    "### Worked Example: Multi-Queue Multiprocessor Scheduling (MQMS)\\n\\n"
                    "**Architecture Configuration:**\\n"
                    "- **2 CPU Cores**: Core 0 and Core 1, each with its own private L1/L2 hardware cache and local Ready Queue.\\n"
                    "- **Core 0 Queue**: P1 (Arrival $t=0$, Burst 4 ms), P2 (Arrival $t=0$, Burst 3 ms)\\n"
                    "- **Core 1 Queue**: P3 (Arrival $t=0$, Burst 2 ms), P4 (Arrival $t=0$, Burst 7 ms)\\n\\n"
                    "#### Execution Timeline & Work Stealing:\\n"
                    "* **t = 0 - 4 ms**: Core 0 runs **P1** to completion at $t=4$ ms. Core 1 runs **P3** to completion at $t=2$ ms, then starts **P4** at $t=2$ ms.\\n"
                    "* **t = 4 - 7 ms**: Core 0 runs **P2** to completion at $t=7$ ms. Meanwhile, Core 1 continues executing **P4** (has executed 5 ms of its 7 ms burst).\\n"
                    "* **t = 7 ms**: Core 0's queue is completely empty! Rather than sitting idle, Core 0 initiates **Work Stealing**: it inspects Core 1's overloaded queue and steals P4's remaining 2 ms.\\n"
                    "* **t = 7 - 9 ms**: Core 0 executes P4's remaining 2 ms and completes it at $t=9$ ms. Both cores finished all work concurrently!\\n\\n"
                    "#### Gantt Chart:\\n"
                    f"```text\\n{ascii_chart}\\n```\\n\\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: multiprocessor_mqms\\nCores: ['Core 0', 'Core 1']\\nProcesses: ['P1', 'P2', 'P3', 'P4']"
                return summary, ascii_chart, formatted_md

            if "lottery" in topic_lower or "stride" in topic_lower:
                ascii_chart = (
                    "| P2 (stride 50) | P2 (stride 50) | P1 (stride 100) | P2 (stride 50) | P3 (stride 200) |\\n"
                    "0                1                2                 3                4                 5"
                )
                q_text = "Notice how process P2 with 200 tickets has a stride of 50, whereas P1 with 100 tickets has a stride of 100. Does a smaller stride cause a process to be selected more frequently or less frequently by the scheduler?"
                formatted_md = (
                    "### Worked Example: Deterministic Stride Scheduling\\n\\n"
                    "**Configuration ($L = 10,000$):**\\n"
                    "- **Formula**: $\\\\text{Stride} = \\\\frac{L}{\\\\text{Tickets}}$\\n"
                    "- **P1**: 100 Tickets $\\\\implies \\\\text{Stride}_1 = \\\\frac{10,000}{100} = 100$\\n"
                    "- **P2**: 200 Tickets $\\\\implies \\\\text{Stride}_2 = \\\\frac{10,000}{200} = 50$\\n"
                    "- **P3**: 50 Tickets $\\\\implies \\\\text{Stride}_3 = \\\\frac{10,000}{50} = 200$\\n\\n"
                    "#### Pass Value Progression (Always schedule $\\\\min(pass)$):\\n"
                    "* **Initial State**: $pass_1 = 0, pass_2 = 0, pass_3 = 0$\\n"
                    "* **Tick 1**: Tie at pass=0. Dispatch **P2** (highest tickets). $pass_2 \\\\mathrel{+}= 50 \\\\implies 50$. Pass values: P1=0, P2=50, P3=0.\\n"
                    "* **Tick 2**: Min pass is 0. Dispatch **P1**. $pass_1 \\\\mathrel{+}= 100 \\\\implies 100$. Pass values: P1=100, P2=50, P3=0.\\n"
                    "* **Tick 3**: Min pass is 0. Dispatch **P3**. $pass_3 \\\\mathrel{+}= 200 \\\\implies 200$. Pass values: P1=100, P2=50, P3=200.\\n"
                    "* **Tick 4**: Min pass is 50. Dispatch **P2**. $pass_2 \\\\mathrel{+}= 50 \\\\implies 100$. Pass values: P1=100, P2=100, P3=200.\\n"
                    "* **Tick 5**: Min pass is 100. Dispatch **P2**. $pass_2 \\\\mathrel{+}= 50 \\\\implies 150$. Pass values: P1=100, P2=150, P3=200.\\n\\n"
                    "#### Gantt Chart:\\n"
                    f"```text\\n{ascii_chart}\\n```\\n\\n"
                    "Over time, P2 receives exactly 4/7 (~57%) of the CPU, P1 receives 2/7 (~29%), and P3 receives 1/7 (~14%), exactly matching their 200 : 100 : 50 ticket ratio with 0% randomness!\\n\\n"
                    f"**Tutor Check:** {q_text}"
                )
                summary = "Algorithm: stride_scheduling\\nProcesses: ['P1', 'P2', 'P3']\\nTickets: [100, 200, 50]"
                return summary, ascii_chart, formatted_md

            # Select canonical algorithm & processes
            if "hrrn" in topic_lower or "response ratio" in topic_lower:'''

assert target in text, "Target string not found!"
new_text = text.replace(target, replacement, 1)

with open('app/core/tutoring_engine.py', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Updated _attempt_deterministic_solve successfully! Lines:", len(new_text.splitlines()))
