"""Comprehensive undergraduate-level knowledge catalog for all CPU Process Scheduling topics."""

import re
from typing import Optional, Dict, Any


KNOWLEDGE_CATALOG = {
    # =========================================================================
    # MODULE A: SCHEDULING FUNDAMENTALS
    # =========================================================================

    "preemption": {
        "keywords": [
            "preempt", "preemptive", "non-preemptive", "non preemptive", "cooperative scheduling",
            "decision points", "scheduling circumstances", "silberschatz circumstances",
            "preemption trigger", "voluntary yield"
        ],
        "regex": r"\b(preempt|preemptive|non-preemptive|non preemptive|cooperative)\b",
        "topic": "Fundamentals",
        "message": (
            "### Preemptive vs. Non-Preemptive Scheduling: Complete Breakdown\n\n"
            "CPU scheduling policies govern how the Operating System allocates CPU cores to ready processes. "
            "The distinction between **preemptive** and **non-preemptive** scheduling centers on whether the OS kernel has the authority to forcibly take the CPU away from a running process.\n\n"
            "---"
            "\n\n#### 1. Non-Preemptive Scheduling (Cooperative Scheduling)\n"
            "* **Core Rule**: Once the CPU is allocated to a process, that process retains exclusive control of the CPU until it voluntarily relinquishes it.\n"
            "* **Voluntary Release Events**:\n"
            "  1. The process **terminates** (calls `exit()`).\n"
            "  2. The process transitions to the **Waiting (Blocked)** state (e.g., initiating an I/O request, waiting on a child process, or sleeping).\n"
            "* **Hardware Requirement**: Minimal; does not require a hardware timer interrupt.\n"
            "* **Historical Systems**: Windows 3.1, classic Mac OS 9.\n"
            "* **Standard Algorithms**: FCFS (First-Come, First-Served), standard Non-Preemptive SJF, and Non-Preemptive Priority.\n"
            "* **Advantages**: Simple design, zero preemption overhead, avoids race conditions on shared data structures.\n"
            "* **Major Drawback**: Poor responsiveness; a single long or buggy process in an infinite loop can monopolize the CPU.\n\n"
            "---"
            "\n\n#### 2. Preemptive Scheduling\n"
            "* **Core Rule**: The OS kernel can interrupt and suspend a currently running process before its CPU burst completes, moving it back to the **Ready Queue** to dispatch another process.\n"
            "* **Preemption Triggers**:\n"
            "  1. **Hardware Timer Interrupt**: A process's allocated time slice (Time Quantum) expires (e.g., in Round Robin).\n"
            "  2. **Higher-Priority Arrival**: A newly arrived process has higher priority (Preemptive Priority) or shorter remaining burst time (SRTF).\n"
            "  3. **I/O Completion**: An I/O device finishes an operation for a high-priority blocked process, returning it to Ready.\n"
            "* **Hardware Requirement**: Requires a programmable interval timer (PIT / APIC).\n"
            "* **Standard Algorithms**: Round Robin (RR), Shortest Remaining Time First (SRTF), Preemptive Priority, MLFQ, Linux CFS.\n"
            "* **Advantages**: Excellent interactive responsiveness; guarantees fairness and prevents CPU monopolization.\n"
            "* **Major Drawback**: High context-switching overhead and potential race conditions requiring synchronization locks (mutexes, spinlocks).\n\n"
            "---"
            "\n\n#### 3. The 4 Silberschatz Scheduling Circumstances\n"
            "1. **Running $\\to$ Waiting** (e.g., I/O request or `wait()`) $\\to$ *Non-Preemptive* (voluntary release).\n"
            "2. **Running $\\to$ Ready** (e.g., timer interrupt or voluntary `sched_yield()`) $\\to$ *Preemptive* (forced suspension).\n"
            "3. **Waiting $\\to$ Ready** (e.g., I/O completion) $\\to$ *Preemptive* (if new process preempts runner).\n"
            "4. **Terminates** (process finishes or aborts) $\\to$ *Non-Preemptive* (voluntary exit).\n\n"
            "> **Golden Rule**: If an OS only schedules under circumstances 1 and 4, it is strictly **Non-Preemptive**. If it can schedule under 2 or 3, it is **Preemptive**."
        ),
        "question": "Under which specific operating circumstance does an algorithm switch from running to ready: a voluntary I/O request or an asynchronous timer interrupt?",
        "hint": "Think about whether the running process chose to stop or was forced to stop by hardware."
    },

    "kernel_preemption": {
        "keywords": [
            "kernel preemption", "preemptive kernel", "non-preemptive kernel", "non preemptive kernel",
            "kernel mode preemption", "reentrant kernel", "spinlocks in kernel"
        ],
        "regex": r"\b(preemptive kernel|non-preemptive kernel|kernel preemption)\b",
        "topic": "Fundamentals",
        "message": (
            "### Preemptive Kernel vs. Non-Preemptive Kernel\n\n"
            "Kernel preemption governs whether a process executing inside **Kernel Mode** (e.g., handling a system call) can be preempted.\n\n"
            "#### 1. Non-Preemptive Kernel\n"
            "* Does not allow a process running in kernel mode to be preempted.\n"
            "* A kernel-mode process runs until it exits kernel mode, blocks on I/O, or voluntarily yields CPU.\n"
            "* **Advantage**: Simpler architecture; essentially free from race conditions on kernel data structures (like process lists and open file tables).\n"
            "* **Disadvantage**: Unacceptable latency for real-time applications, since a high-priority task may be blocked waiting for an arbitrary system call to complete.\n\n"
            "#### 2. Preemptive Kernel\n"
            "* Allows a process executing kernel code to be preempted when a higher-priority task becomes ready.\n"
            "* **Advantage**: High real-time responsiveness and lower dispatch latency (used in Linux since kernel 2.6 and modern Windows/macOS).\n"
            "* **Requirement**: Kernel data structures must be guarded against race conditions using mutual exclusion locks (mutexes, spinlocks, and disabling local interrupts)."
        ),
        "question": "Why is a preemptive kernel critical for real-time operating systems compared to a non-preemptive kernel?",
        "hint": "Consider how quickly a high-priority real-time task needs to access the CPU when an event occurs."
    },

    "process_vs_program": {
        "keywords": [
            "process vs program", "process and program", "program vs process", "difference between process and program",
            "diffrence between process", "program and process", "passive entity active entity"
        ],
        "regex": r"\b(process vs program|program vs process|difference between process and program)\b",
        "topic": "Fundamentals",
        "message": (
            "### Process vs. Program: Memory Architecture and Execution State\n\n"
            "1. **Program (Passive Entity)**:\n"
            "   * A static collection of compiled binary instructions and data stored passively on non-volatile secondary storage (SSD/HDD), e.g., `/bin/bash` or `app.exe`.\n"
            "   * Consumes storage space, but **zero CPU cycles** and **zero memory (RAM)** while resting on disk.\n"
            "   * Has no dynamic state, no program counter, and no thread of execution.\n\n"
            "2. **Process (Active Entity)**:\n"
            "   * A program loaded into main memory (RAM) and actively being executed by a CPU core.\n"
            "   * Possesses a complete dynamic execution state represented across distinct memory segments:\n"
            "     * **Text Segment**: Compiled read-only executable machine instructions.\n"
            "     * **Data Segment**: Initialized global and static variables.\n"
            "     * **BSS Segment**: Block Started by Symbol (uninitialized global/static variables, zero-filled).\n"
            "     * **Heap**: Dynamically allocated memory at runtime (via `malloc()`, `new`, `brk`/`sbrk`), growing upward.\n"
            "     * **Stack**: Temporary execution frames, local variables, function parameters, and return addresses, growing downward.\n"
            "     * **Process Control Block (PCB)**: Kernel data structure tracking PID, registers, priority, and file descriptors.\n\n"
            "💡 **Analogy**: A printed recipe in a cookbook is a **program**. A chef actively measuring ingredients and cooking in the kitchen is a **process**!\n\n"
            "> **Note**: A single program binary stored on disk can be executed multiple times simultaneously to produce multiple distinct processes, each with its own independent address space and PID."
        ),
        "question": "Can a single program stored on disk be executed multiple times simultaneously to create multiple distinct processes?",
        "hint": "Consider what happens if you launch three separate terminal windows running python."
    },

    "process_states": {
        "keywords": [
            "process state", "process states", "state transition", "state transitions",
            "5-state", "five state model", "new ready running", "blocked state", "waiting state"
        ],
        "regex": r"\b(process states?|5-state|five state|state transitions?)\b",
        "topic": "Fundamentals",
        "message": (
            "### The 5-State Process Life Cycle Model\n\n"
            "During its lifetime, a process transitions through five fundamental states:\n\n"
            "1. **New**: The process is being created (PCB created, PID allocated), but is not yet loaded into main memory or admitted to the ready pool.\n"
            "2. **Ready**: The process is loaded in main memory and waiting in the Ready Queue to be assigned to a CPU core by the short-term scheduler.\n"
            "3. **Running**: The process instructions are currently being executed by the CPU.\n"
            "4. **Waiting (Blocked)**: The process cannot execute because it is waiting for an external event (e.g., I/O completion, IPC message, mutex lock). It cannot run even if CPU is completely idle!\n"
            "5. **Terminated**: The process has finished execution or was aborted; kernel deallocates its memory and resources.\n\n"
            "#### State Transitions:\n"
            "* **Admitted**: $\\text{New} \\to \\text{Ready}$ (Long-term scheduler admits process to memory).\n"
            "* **Scheduler Dispatch**: $\\text{Ready} \\to \\text{Running}$ (Dispatcher allocates CPU to selected process).\n"
            "* **Interrupt / Timeout**: $\\text{Running} \\to \\text{Ready}$ (Time quantum expires or higher-priority job arrives).\n"
            "* **I/O Wait**: $\\text{Running} \\to \\text{Waiting}$ (Process initiates an I/O request or sleeps).\n"
            "* **I/O Completion**: $\\text{Waiting} \\to \\text{Ready}$ (Device interrupts CPU; process placed back in Ready Queue—never directly to Running!).\n"
            "* **Exit**: $\\text{Running} \\to \\text{Terminated}$ (Normal completion or fatal error)."
        ),
        "question": "When an I/O operation finishes for a waiting process, does it move directly to Running, or to the Ready Queue?",
        "hint": "Another process might already be actively executing on the CPU."
    },

    "seven_state_model": {
        "keywords": [
            "7-state", "seven state", "suspended state", "ready suspended", "blocked suspended",
            "swapping", "swap out", "swap in", "suspend"
        ],
        "regex": r"\b(7-state|seven state|ready-suspended|blocked-suspended|suspended states?)\b",
        "topic": "Fundamentals",
        "message": (
            "### The 7-State Process Model: Swapping and Suspended States\n\n"
            "When main memory (RAM) is heavily overcommitted, the operating system's **Medium-Term Scheduler (Swapper)** temporarily moves entire processes out of physical RAM to secondary storage (swap file or swap partition).\n\n"
            "This introduces two suspended states into the life cycle:\n\n"
            "1. **Ready-Suspended (Ready-Suspend)**:\n"
            "   * The process is ready to execute as soon as CPU time is available, but currently resides on secondary storage.\n"
            "   * Swapped in to **Ready** when physical memory becomes free.\n\n"
            "2. **Blocked-Suspended (Waiting-Suspend)**:\n"
            "   * The process is blocked waiting for an I/O event AND resides on secondary storage.\n"
            "   * If the I/O event completes while the process is still on disk, it transitions from **Blocked-Suspended $\\to$ Ready-Suspended**!\n\n"
            "#### Key Transitions:\n"
            "* **Suspend (Swap Out)**: $\\text{Ready} \\to \\text{Ready-Suspended}$ or $\\text{Blocked} \\to \\text{Blocked-Suspended}$.\n"
            "* **Activate (Swap In)**: $\\text{Ready-Suspended} \\to \\text{Ready}$.\n"
            "* **Event Occurs**: $\\text{Blocked-Suspended} \\to \\text{Ready-Suspended}$."
        ),
        "question": "If an I/O operation completes for a process in the Blocked-Suspended state, which state does it transition into?",
        "hint": "It is still residing on disk (secondary storage), but no longer blocked on I/O."
    },

    "pcb": {
        "keywords": ["pcb", "process control block", "task control block", "task_struct", "pcb fields", "pcb contents"],
        "regex": r"\b(pcb|process control block|task_struct)\b",
        "topic": "Fundamentals",
        "message": (
            "### Process Control Block (PCB): Structure and Role\n\n"
            "The **Process Control Block (PCB)** (also called Task Control Block or `struct task_struct` in Linux) is the kernel data structure that stores all metadata needed to manage a process.\n\n"
            "#### Key Fields Stored in a PCB:\n"
            "1. **Process Identifier (PID)**: Unique numeric ID assigned by the OS, plus Parent PID (PPID).\n"
            "2. **Process State**: Current life cycle state (New, Ready, Running, Waiting, Terminated).\n"
            "3. **Program Counter (PC)**: Address of the next machine instruction to execute.\n"
            "4. **CPU Registers**: Accumulators, index registers, stack pointer (ESP/RSP), base pointer (EBP/RBP), instruction pointer (EIP/RIP), condition flags.\n"
            "5. **CPU Scheduling Information**: Priority, remaining burst, pointers to scheduling queues, aging counters.\n"
            "6. **Memory-Management Information**: Base and limit registers, page table pointers (CR3 register in x86).\n"
            "7. **Accounting Information**: CPU time consumed, time limits, user/group IDs.\n"
            "8. **I/O Status Information**: List of allocated devices, open file descriptor table."
        ),
        "question": "Why must CPU register values be saved into the PCB when a process is preempted?",
        "hint": "What would happen to your arithmetic calculations if another program overwrote the registers?"
    },

    "dispatcher_context_switch": {
        "keywords": [
            "dispatcher", "dispatch latency", "context switch", "context switching", "switching context",
            "scheduler vs dispatcher", "dispatcher duties"
        ],
        "regex": r"\b(dispatcher|context switch(ing)?|dispatch latency)\b",
        "topic": "Fundamentals",
        "message": (
            "### CPU Scheduler vs. Dispatcher, Context Switching, and Dispatch Latency\n\n"
            "#### 1. Scheduler vs. Dispatcher\n"
            "* **CPU Scheduler (Short-Term Scheduler)**: An algorithmic decision-maker that chooses *which* process from the Ready Queue should run next.\n"
            "* **Dispatcher**: The low-level kernel module that physically gives control of the CPU to the process selected by the scheduler.\n\n"
            "#### 2. Responsibilities of the Dispatcher\n"
            "1. **Context Switch**: Save CPU registers and Program Counter of the outgoing process to its PCB; load saved registers and PC of the incoming process from its PCB.\n"
            "2. **Switching to User Mode**: Transition CPU execution privilege from Kernel Mode (Ring 0) to User Mode (Ring 3).\n"
            "3. **Jumping to Instruction**: Load the Program Counter with the saved instruction pointer to restart execution.\n\n"
            "#### 3. Dispatch Latency & Context Switch Overhead\n"
            "* **Dispatch Latency**: The exact hardware time elapsed between stopping one process and starting the next.\n"
            "* During context switching, **no useful user work is accomplished**. It is pure operating system overhead.\n"
            "* **Cache Effects**: Context switches invalidate CPU L1/L2 caches and Translation Lookaside Buffer (TLB) entries, degrading execution speed immediately after the switch."
        ),
        "question": "What is the key difference in role between the CPU Scheduler and the Dispatcher?",
        "hint": "One decides *who* runs; the other performs the actual physical handover."
    },

    "context_switch_vs_mode_switch": {
        "keywords": [
            "context switch vs mode switch", "mode switch vs context switch", "mode switch", "user mode to kernel mode",
            "ring 0 ring 3", "system call overhead"
        ],
        "regex": r"\b(context switch vs mode switch|mode switch vs context switch|mode switch)\b",
        "topic": "Fundamentals",
        "message": (
            "### Context Switch vs. Mode Switch: Fundamental Differences\n\n"
            "1. **Mode Switch**:\n"
            "   * A privilege level transition between **User Mode (Ring 3)** and **Kernel Mode (Ring 0)**.\n"
            "   * Triggered by a hardware interrupt, trap, or system call (e.g. `read()`).\n"
            "   * **The same process remains active**! Only the user registers needed to execute kernel code are saved onto the kernel stack.\n"
            "   * Memory address spaces do NOT change; TLB and CPU caches remain valid.\n"
            "   * Overhead: Extremely fast (nanoseconds).\n\n"
            "2. **Context Switch**:\n"
            "   * A full switch from **one process to an entirely different process**.\n"
            "   * Saves complete processor state to outgoing PCB and restores incoming PCB.\n"
            "   * Memory mapping (page tables) is switched (reloading CR3 in x86), causing TLB invalidation and L1/L2 cache misses.\n"
            "   * Overhead: Significantly more expensive (microseconds)."
        ),
        "question": "Does a simple system call that does not block cause a full context switch or just a mode switch?",
        "hint": "Does the CPU change which process it is running, or just execute kernel code on behalf of that same process?"
    },

    "cpu_io_burst": {
        "keywords": [
            "cpu burst", "i/o burst", "io burst", "cpu-bound", "i/o-bound", "io bound", "cpu bound",
            "burst cycle", "burst distribution"
        ],
        "regex": r"\b(cpu burst|i/o burst|io burst|cpu-bound|i/o-bound|burst cycle)\b",
        "topic": "Fundamentals",
        "message": (
            "### The CPU-I/O Burst Cycle and Process Classification\n\n"
            "Process execution consists of an alternating cycle of **CPU bursts** (active computation) and **I/O bursts** (waiting for data transfer).\n\n"
            "#### 1. Process Classification\n"
            "* **CPU-Bound Process**: Spends the overwhelming majority of its time performing computation. Characterized by very long CPU bursts and infrequent, short I/O operations (e.g., matrix multiplication, video encoding, scientific simulations).\n"
            "* **I/O-Bound Process**: Spends the overwhelming majority of its time waiting for I/O devices. Characterized by very short CPU bursts followed by long I/O wait times (e.g., text editors, web browsers, database queries).\n\n"
            "#### 2. Empirical Distribution of CPU Bursts\n"
            "In general operating systems, the frequency curve of CPU bursts shows an exponential distribution: there is a **large frequency of very short bursts** and a **small frequency of very long bursts**.\n"
            "Algorithms like Shortest Job First (SJF) exploit this by prioritizing short bursts to achieve minimal average waiting times."
        ),
        "question": "Does a video rendering program tend to be CPU-bound or I/O-bound?",
        "hint": "Does rendering spend most of its time calculating pixels or waiting for keypresses?"
    },

    "schedulers_types": {
        "keywords": [
            "types of schedulers", "schedulers types", "long-term scheduler", "short-term scheduler",
            "medium-term scheduler", "job scheduler", "swapper", "degree of multiprogramming"
        ],
        "regex": r"\b(long-term scheduler|short-term scheduler|medium-term scheduler|job scheduler|types of schedulers?)\b",
        "topic": "Fundamentals",
        "message": (
            "### The Three Types of Operating System Schedulers\n\n"
            "1. **Long-Term Scheduler (Job Scheduler)**:\n"
            "   * Selects processes from the mass-storage disk pool and loads them into memory for execution.\n"
            "   * **Frequency**: Executes very infrequently (seconds or minutes).\n"
            "   * **Primary Goal**: Controls the **Degree of Multiprogramming** (the total number of processes in memory) and maintains a healthy mix of CPU-bound and I/O-bound jobs.\n\n"
            "2. **Short-Term Scheduler (CPU Scheduler)**:\n"
            "   * Selects which process from the Ready Queue in memory should be allocated the CPU.\n"
            "   * **Frequency**: Executes very frequently (every 10–100 milliseconds).\n"
            "   * **Primary Goal**: Fast decision-making to optimize throughput, latency, and fairness.\n\n"
            "3. **Medium-Term Scheduler (Swapper)**:\n"
            "   * Removes processes from memory to disk (swapping out) when main memory is overcommitted, and brings them back later (swapping in).\n"
            "   * **Primary Goal**: Reduces degree of multiprogramming to prevent thrashing and relieve memory pressure."
        ),
        "question": "Which scheduler controls the degree of multiprogramming by deciding when to admit new processes into memory?",
        "hint": "It runs much less frequently than the CPU scheduler."
    },

    "ready_queue": {
        "keywords": [
            "ready queue", "job queue", "device queue", "waiting queue", "queue management"
        ],
        "regex": r"\b(ready queue|device queue|job queue|waiting queue)\b",
        "topic": "Fundamentals",
        "message": (
            "### Ready Queue Architecture and Queue Types\n\n"
            "Operating systems organize processes into several distinct queues:\n\n"
            "1. **Job Queue**: All processes entering the system (stored on disk).\n"
            "2. **Ready Queue**: All processes residing in main memory, ready and waiting to be allocated CPU time.\n"
            "3. **Device (Waiting) Queues**: Separate queues for each hardware device (e.g., Disk Queue, NIC Network Queue) containing processes waiting for that specific device.\n\n"
            "#### Ready Queue Implementations:\n"
            "* **FIFO Linked List**: Standard in FCFS.\n"
            "* **Binary Min-Heap / Priority Queue**: Standard in SJF and Priority scheduling.\n"
            "* **Circular Linked List**: Standard in Round Robin.\n"
            "* **Multiple Queues / Red-Black Tree**: Standard in MLFQ and Linux CFS."
        ),
        "question": "When a process initiates a disk read, does it remain in the Ready Queue or move to the disk Device Queue?",
        "hint": "Can it execute on the CPU while waiting for the disk head to seek data?"
    },

    # =========================================================================
    # MODULE B: SCHEDULING ALGORITHMS
    # =========================================================================

    "fcfs": {
        "keywords": ["fcfs", "first come first served", "first-come first-served", "fifo scheduling"],
        "regex": r"\b(fcfs|first-come|first come)\b",
        "topic": "FCFS",
        "message": (
            "### First-Come, First-Served (FCFS) Scheduling\n\n"
            "**FCFS** is the simplest CPU scheduling algorithm. Processes are assigned to the CPU in the strict order of their arrival in the Ready Queue using a First-In, First-Out (FIFO) queue.\n\n"
            "* **Characteristics**: Strictly **non-preemptive**. Simple to implement with minimal overhead.\n"
            "* **Starvation**: Zero starvation; every process will eventually execute.\n"
            "* **Primary Weakness**: Highly sensitive to process arrival order, causing high average waiting times.\n\n"
            "#### The Convoy Effect:\n"
            "If a CPU-bound process with a huge burst arrives first, all subsequent short I/O-bound processes become trapped waiting behind it.\n"
            "* **Analogy**: A single slow tractor on a narrow one-lane highway with dozens of sports cars stuck behind it.\n"
            "* **Result**: Substantially inflated average waiting time and underutilized I/O devices."
        ),
        "question": "What is the primary disadvantage of FCFS when a CPU-bound job arrives before multiple short I/O-bound jobs?",
        "hint": "Think of the convoy analogy."
    },

    "convoy_effect": {
        "keywords": ["convoy effect", "convoy", "convoy phenomenon"],
        "regex": r"\b(convoy effect|convoy phenomenon)\b",
        "topic": "FCFS",
        "message": (
            "### The Convoy Effect in First-Come, First-Served Scheduling\n\n"
            "The **Convoy Effect** is a classic scheduling anomaly observed in FCFS where short processes must wait for one long, CPU-bound process to release the CPU.\n\n"
            "#### How It Unfolds:\n"
            "* **Analogy**: A single slow tractor moving down a narrow one-lane highway with a long line of fast cars stuck behind it.\n"
            "1. One large CPU-bound process acquires the CPU and computes for a very long burst (e.g. 100 ms).\n"
            "2. Meanwhile, dozens of short I/O-bound processes arrive in the Ready Queue. They only need 1–2 ms of CPU time, but must wait in line.\n"
            "3. During this entire time, **all I/O devices sit completely idle**!\n"
            "4. When the large process finally completes and initiates I/O, all the short processes quickly execute on the CPU and then all move together to the I/O devices.\n"
            "5. Now, the **CPU sits completely idle** while all tasks wait for I/O!\n\n"
            "#### Impact and Remedy:\n"
            "* Results in very low CPU and device utilization.\n"
            "* **Remedy**: Preemptive scheduling algorithms like **Round Robin** or **SRTF** prevent the convoy effect by breaking long bursts into small time slices."
        ),
        "question": "How does Round Robin scheduling solve the Convoy Effect?",
        "hint": "What does Round Robin do when a process tries to run for a very long time?"
    },

    "sjf_non_preemptive": {
        "keywords": [
            "sjf", "shortest job first", "non-preemptive sjf", "non preemptive sjf",
            "optimal waiting time", "shortest burst first"
        ],
        "regex": r"\b(sjf|shortest job first)\b",
        "topic": "SJF",
        "message": (
            "### Shortest Job First (SJF) Non-Preemptive Scheduling\n\n"
            "**SJF** associates each process with the length of its next CPU burst. When the CPU becomes free, the process with the smallest burst time is scheduled.\n\n"
            "#### Core Properties:\n"
            "* **Provably Optimal**: SJF is provably optimal because it gives the minimum average waiting time for a given set of stationary processes.\n"
            "* **The Catch**: In general operating systems, the kernel cannot know the length of the next CPU burst in advance!\n"
            "* **Burst Prediction**: The OS estimates future burst times using **exponential smoothing**:\n"
            "  $$\\tau_{n+1} = \\alpha t_n + (1 - \\alpha) \\tau_n$$\n"
            "* **Starvation Risk**: If short processes arrive continuously, a long process may suffer from **Starvation (Indefinite Blocking)**."
        ),
        "question": "Why is pure Shortest Job First difficult to implement in general-purpose operating systems?",
        "hint": "How does the OS know how long a program will run before it executes?"
    },

    "srtf_preemptive": {
        "keywords": [
            "srtf", "shortest remaining time first", "preemptive sjf", "preemptive shortest job first"
        ],
        "regex": r"\b(srtf|shortest remaining time first|preemptive sjf)\b",
        "topic": "SRTF",
        "message": (
            "### Shortest Remaining Time First (SRTF) Preemptive Scheduling\n\n"
            "**SRTF** is the preemptive variant of Shortest Job First (SJF).\n\n"
            "#### Mechanism:\n"
            "* When a new process arrives in the Ready Queue, the scheduler compares its burst time against the **remaining burst time** of the currently running process.\n"
            "* If the newly arrived process has a shorter remaining burst time than the runner, the runner is **immediately preempted** and returned to the Ready Queue.\n"
            "* **Tie-breaking**: If remaining times are identical, ties are traditionally broken by arrival order (FCFS) or lower PID.\n\n"
            "#### Trade-offs:\n"
            "* Provides even better average turnaround and response times than non-preemptive SJF for early arriving short jobs.\n"
            "* Introduces high context-switching overhead because preemptions occur frequently.\n"
            "* Suffer from potential **starvation** of long processes if short processes keep arriving."
        ),
        "question": "In SRTF, does the scheduler compare the new arrival's burst against the running process's original burst time or its remaining burst time?",
        "hint": "The running process has already executed for some time units."
    },

    "burst_prediction": {
        "keywords": [
            "exponential smoothing", "predicting cpu burst", "burst prediction", "tau formula",
            "tau_n+1", "alpha smoothing factor"
        ],
        "regex": r"\b(exponential smoothing|burst prediction|tau_{n\+1})\b",
        "topic": "SJF",
        "message": (
            "### Predicting CPU Burst Times via Exponential Smoothing\n\n"
            "Because the OS cannot know future burst lengths in advance, SJF and SRTF predict the next burst length ($\\tau_{n+1}$) using exponential smoothing:\n\n"
            "$$\\tau_{n+1} = \\alpha t_n + (1 - \\alpha) \\tau_n$$\n\n"
            "* $t_n$: Actual length of the $n$-th CPU burst.\n"
            "* $\\tau_n$: Predicted value for the $n$-th CPU burst.\n"
            "* $\\tau_{n+1}$: Predicted value for the next CPU burst.\n"
            "* $\\alpha$: Smoothing factor ($0 \\le \\alpha \\le 1$).\n\n"
            "#### Significance of $\\alpha$:\n"
            "* If $\\alpha = 0$: $\\tau_{n+1} = \\tau_n$ (Recent history has no effect; prediction remains fixed).\n"
            "* If $\\alpha = 1$: $\\tau_{n+1} = t_n$ (Only the most recent burst counts; past history is discarded).\n"
            "* Commonly, $\\alpha = 0.5$, balancing recent behavior and past history equally."
        ),
        "question": "If alpha is set to 1 in the exponential smoothing formula, what determines the predicted burst time?",
        "hint": "What does tau_{n+1} equal when alpha = 1?"
    },

    "priority_scheduling": {
        "keywords": [
            "priority scheduling", "preemptive priority", "non-preemptive priority", "priority convention",
            "internal priority", "external priority"
        ],
        "regex": r"\b(priority scheduling|preemptive priority|non-preemptive priority)\b",
        "topic": "Priority",
        "message": (
            "### Priority Scheduling: Mechanisms, Conventions, and Modes\n\n"
            "In **Priority Scheduling**, each process is assigned an integer priority value. The CPU is allocated to the process with the highest priority in the Ready Queue.\n\n"
            "#### 1. Priority Conventions\n"
            "* **Silberschatz / Unix Convention**: A **smaller integer indicates higher priority** (e.g. 0 = highest priority).\n"
            "* **Alternative Convention (Windows)**: A **larger integer indicates higher priority** (e.g. 31 = highest priority).\n"
            "* *Always verify the stated convention in your problem statement!*\n\n"
            "#### 2. Preemptive vs. Non-Preemptive Priority\n"
            "* **Preemptive Priority**: When a higher-priority process arrives, it immediately preempts the currently running process.\n"
            "* **Non-Preemptive Priority**: The running process completes its current CPU burst even if a higher-priority process arrives in the Ready Queue.\n\n"
            "#### 3. Starvation Issue\n"
            "A major issue in Priority Scheduling is **Starvation (Indefinite Blocking)**: low-priority processes may wait forever if high-priority processes arrive continuously."
        ),
        "question": "In the standard Silberschatz OS textbook convention, does priority 0 represent the highest priority or lowest priority?",
        "hint": "Think of 1st place in a race."
    },

    "starvation_and_aging": {
        "keywords": [
            "starvation", "aging", "indefinite blocking", "how aging works", "prevent starvation"
        ],
        "regex": r"\b(starvation|aging|indefinite blocking)\b",
        "topic": "Priority",
        "message": (
            "### Starvation (Indefinite Blocking) and the Aging Solution\n\n"
            "#### 1. What is Starvation?\n"
            "* **Starvation** is a condition where a runnable process waits indefinitely in the Ready Queue because higher-priority processes continuously monopolize the CPU.\n"
            "* Can occur in **SJF**, **SRTF**, and **Priority Scheduling**.\n"
            "* *Famous Historical Example*: When MIT's IBM 7094 was shut down in 1973, an ordinary low-priority batch job submitted in 1967 was discovered still waiting in the queue to be executed!\n\n"
            "#### 2. The Solution: Aging\n"
            "* **Aging** is a technique that gradually increases the priority of processes that spend extended periods waiting in the Ready Queue.\n"
            "* **Example**: If priorities range from 127 (low) to 0 (high), the OS might decrement the priority number of each waiting process by 1 every 15 minutes.\n"
            "* Eventually, even the lowest-priority process will age into the highest priority in the system and is guaranteed to execute."
        ),
        "question": "How does the aging technique guarantee that a low-priority process will eventually execute?",
        "hint": "What happens to its priority number as it waits longer in the ready queue?"
    },

    "round_robin": {
        "keywords": [
            "round robin", "time quantum", "time slice", "circular queue", "rr scheduling"
        ],
        "regex": r"\b(round robin|time quantum|time slice|\brr\b)\b",
        "topic": "Round Robin",
        "message": (
            "### Round Robin (RR) Scheduling & Time Quantum Mechanism\n\n"
            "**Round Robin** is designed specifically for time-sharing interactive systems.\n\n"
            "* **Mechanism**: The Ready Queue is treated as a circular FIFO queue. The CPU scheduler allocates each process a small slice of CPU time called a **Time Quantum** ($q$, typically 10–100 ms).\n"
            "* **Preemption**: When the timer interrupt fires at the end of the quantum, the running process is preempted and placed at the tail of the Ready Queue.\n"
            "* **Fairness**: With $n$ processes in the ready queue and time quantum $q$, each process gets $1/n$ of the CPU time, and no process waits more than $(n - 1)q$ time units for its turn.\n\n"
            "#### Time Quantum Trade-offs:\n"
            "1. **Quantum Extremely Large ($q \\to \\infty$)**:\n"
            "   * No process gets preempted; Round Robin degrades into **First-Come, First-Served (FCFS)**.\n"
            "2. **Quantum Extremely Small ($q \\to 0$)**:\n"
            "   * Gives the illusion of processor sharing (each process runs at $1/n$ speed).\n"
            "   * However, **context-switch overhead** completely dominates, crippling system throughput.\n"
            "3. **Golden Rule**: About **80% of CPU bursts** should be shorter than the time quantum $q$."
        ),
        "question": "Which algorithm does Round Robin become equivalent to when the time quantum is larger than the longest CPU burst?",
        "hint": "When no preemption ever occurs, what determines execution order?"
    },

    "time_quantum_tradeoffs": {
        "keywords": [
            "quantum size", "quantum trade-off", "quantum trade off", "time quantum trade-off",
            "time quantum trade off", "time quantum tradeoffs", "choosing time quantum",
            "80% rule", "80% rule in time quantum", "small quantum vs large quantum"
        ],
        "regex": r"\b(quantum size|quantum trade-off|80% rule|small quantum)\b",
        "topic": "Round Robin",
        "message": (
            "### Time Quantum Selection Trade-offs in Round Robin\n\n"
            "Selecting the duration of the Time Quantum ($q$) is the critical design decision in Round Robin:\n\n"
            "| Time Quantum Size | Context Switch Overhead | Interactive Responsiveness | Behavioral Outcome |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **Too Large ($q \\to \\infty$)** | Very Low | Poor | Degrades into First-Come, First-Served (FCFS). Long jobs block short interactive jobs. |\n"
            "| **Too Small ($q \\to 0$)** | Catastrophic | Poor (CPU wasted) | CPU spends more time switching context than executing user instructions. |\n"
            "| **Optimal (10–100 ms)** | Moderate (< 1% CPU) | High | Balanced responsiveness and throughput. |\n\n"
            "#### The 80% Rule of Thumb:\n"
            "System designers aim for approximately **80% of CPU bursts** to be shorter than the time quantum $q$. "
            "This ensures that most I/O-bound interactive processes finish their bursts and yield voluntarily without incurring preemption overhead."
        ),
        "question": "If the time quantum is 10 ms and a context switch takes 1 ms, what percentage of CPU time is wasted on context switching?",
        "hint": "Calculate 1 ms overhead out of total 11 ms window."
    },

    "multilevel_queue": {
        "keywords": [
            "multilevel queue", "mlq", "multiple queues", "static queue partition"
        ],
        "regex": r"\b(multilevel queue|\bmlq\b)\b",
        "topic": "Fundamentals",
        "message": (
            "### Multilevel Queue (MLQ) Scheduling\n\n"
            "**Multilevel Queue (MLQ)** partitions the Ready Queue into several separate queues based on process properties (e.g., memory size, priority, or process type):\n\n"
            "* **Queue 1 (Top Priority)**: System processes (e.g., kernel threads).\n"
            "* **Queue 2**: Interactive foreground processes (scheduled via Round Robin).\n"
            "* **Queue 3 (Bottom Priority)**: Batch background processes (scheduled via FCFS).\n\n"
            "#### Fundamental Rule:\n"
            "* Processes are permanently assigned to one queue upon entry and **CANNOT move** between queues.\n"
            "* **Inter-Queue Scheduling**: Can be **Fixed Priority Preemptive** (Queue 1 runs first; Queue 2 only runs if Queue 1 is empty $\\to$ risk of starvation) or **Time-Sliced** (e.g., 80% CPU time to Queue 2, 20% to Queue 3)."
        ),
        "question": "Can processes change which queue they belong to in a standard Multilevel Queue (MLQ) system?",
        "hint": "Think about whether process assignment is static or dynamic."
    },

    "multilevel_feedback_queue": {
        "keywords": [
            "multilevel feedback queue", "mlfq", "feedback queue", "queue migration"
        ],
        "regex": r"\b(multilevel feedback queue|\bmlfq\b)\b",
        "topic": "Fundamentals",
        "message": (
            "### Multilevel Feedback Queue (MLFQ) Scheduling\n\n"
            "**MLFQ** is the most versatile and widely deployed general-purpose scheduling algorithm (used in modern Windows, macOS, and BSD kernels).\n\n"
            "#### Key Difference from MLQ:\n"
            "Unlike MLQ, MLFQ **allows processes to dynamically migrate between queues** based on their observed CPU burst behavior!\n\n"
            "#### Standard MLFQ Rules:\n"
            "1. New processes enter Queue 0 (highest priority, smallest quantum, e.g. 8 ms).\n"
            "2. If a process uses its entire quantum without relinquishing the CPU, it is demoted to Queue 1 (medium priority, larger quantum, e.g. 16 ms).\n"
            "3. If it exhausts Queue 1's quantum, it is demoted to Queue 2 (lowest priority, FCFS).\n"
            "4. If a process yields voluntarily for I/O before its quantum expires, it stays in the high-priority queue (favoring interactive tasks!).\n"
            "5. **Aging**: Periodically, all processes in the system are boosted back to Queue 0 to prevent starvation."
        ),
        "question": "What happens to a CPU-bound process in MLFQ that uses up its entire time quantum without doing I/O?",
        "hint": "Is it promoted or demoted to a lower queue?"
    },

    "algorithm_comparison": {
        "keywords": [
            "compare algorithms", "algorithm comparison", "scheduling trade-offs", "which algorithm is best",
            "comparison matrix", "summary of algorithms"
        ],
        "regex": r"\b(compare algorithms|algorithm comparison|scheduling trade-offs|comparison matrix)\b",
        "topic": "Fundamentals",
        "message": (
            "### Comprehensive Comparison of CPU Scheduling Algorithms\n\n"
            "| Algorithm | Preemptive? | Starvation Risk? | Overhead | Optimal Metric | Ideal Workload |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| **FCFS** | No | Zero | Lowest | Simplicity | Batch systems with similar burst lengths |\n"
            "| **SJF** | No | Yes (long jobs) | Low | Min Average Waiting Time | Systems where burst lengths are predictable |\n"
            "| **SRTF** | Yes | Yes (long jobs) | High | Min Turnaround Time | General batch with varying bursts |\n"
            "| **Round Robin** | Yes | Zero | Medium | Min Response Time | Interactive time-sharing environments |\n"
            "| **Priority** | Both | Yes (low priority) | Medium | Strict Business Logic | Mission-critical and real-time systems |\n"
            "| **MLFQ** | Yes | Bounded (via Aging) | High | Adaptive All-Rounder | Modern general-purpose OS kernels |"
        ),
        "question": "Which scheduling algorithm is provably optimal for minimizing average waiting time for a set of stationary processes?",
        "hint": "It prioritizes processes with the smallest CPU burst."
    },

    # =========================================================================
    # MODULE C: NUMERICAL PROBLEM SOLVING & METRICS
    # =========================================================================

    "metrics_formulas": {
        "keywords": [
            "metrics", "turnaround", "waiting time", "response time", "completion time",
            "cpu utilization", "throughput", "formulas", "tat formula", "wt formula",
            "arrival time", "burst time", "arrival time and burst time", "scheduling criteria",
            "scheduling metrics", "average waiting time", "average turnaround time"
        ],
        "regex": r"\b(metrics|turnaround time|waiting time|response time|completion time|throughput|cpu utilization|arrival time|burst time|\btat\b|\bwt\b|\brt\b|\bct\b)\b",
        "topic": "Metrics",
        "message": (
            "### CPU Scheduling Criteria and Exact Formulas\n\n"
            "Operating systems track five core mathematical criteria to evaluate scheduling algorithms:\n\n"
            "1. **Completion Time (CT)**: The exact clock time when a process finishes its last CPU burst.\n\n"
            "2. **Turnaround Time (TAT)**: Total elapsed time from arrival to completion:\n"
            "   $$\\text{TAT} = \\text{Completion Time (CT)} - \\text{Arrival Time (AT)}$$\n\n"
            "3. **Waiting Time (WT)**: Total time spent waiting in the Ready Queue:\n"
            "   $$\\text{WT} = \\text{Turnaround Time (TAT)} - \\text{Burst Time (BT)}$$\n\n"
            "4. **Response Time (RT)**: Elapsed time from arrival until first CPU allocation:\n"
            "   $$\\text{RT} = \\text{Time of First CPU Execution} - \\text{Arrival Time (AT)}$$\n"
            "   *(Note: In non-preemptive scheduling, $\\text{RT} = \\text{WT}$. In preemptive scheduling, $\\text{RT} \\le \\text{WT}$.)*\n\n"
            "5. **CPU Utilization**: Percentage of time the CPU is actively executing processes ($0\\%$ to $100\\%$).\n\n"
            "6. **Throughput**: Number of completed processes per unit time (e.g. processes per millisecond)."
        ),
        "question": "If a process arrives at time 2 ms, needs 5 ms of burst, and finishes at time 12 ms, what is its waiting time?",
        "hint": "TAT = 12 - 2 = 10 ms. Then WT = TAT - Burst Time (5 ms)."
    },

    "gantt_chart": {
        "keywords": [
            "gantt", "gantt chart", "timeline", "bar chart", "schedule chart", "idle block"
        ],
        "regex": r"\b(gantt|gantt chart|timeline chart)\b",
        "topic": "Metrics",
        "message": (
            "### Understanding and Drawing Gantt Charts\n\n"
            "A **Gantt Chart** in CPU scheduling is a horizontal bar chart illustrating how the CPU core is allocated across continuous time intervals.\n\n"
            "#### Construction Rules:\n"
            "* The horizontal axis marks elapsed time units (typically starting at $t = 0$).\n"
            "* Each block represents a process occupying the CPU.\n"
            "* The numbers at the start and end of each block indicate start and completion times.\n"
            "* **CPU Idle Blocks**: If no process is ready at time $t$, the CPU sits in an *Idle* block until the next process arrives.\n"
            "* In preemptive algorithms (Round Robin, SRTF), a single process may appear multiple times across the timeline.\n\n"
            "```text\n"
            "+-------+-------+-------+\n"
            "|  P1   |  P2   |  P3   |\n"
            "+-------+-------+-------+\n"
            "0       4       7       8\n"
            "```\n\n"
            "* In this chart: P1 runs from $t=0$ to $4$ (CT=4). P2 runs from $t=4$ to $7$ (CT=7). P3 runs from $t=7$ to $8$ (CT=8)."
        ),
        "question": "If the CPU has no ready processes between t=3 and t=6, how should this period be marked on the Gantt chart?",
        "hint": "It represents a period where the CPU is not executing user instructions."
    },

    "idle_time_and_ties": {
        "keywords": [
            "idle time", "cpu idle", "tie breaking", "scheduling ties", "quantum boundary tie"
        ],
        "regex": r"\b(cpu idle|idle time|idle block|tie-breaking|tie breaking)\b",
        "topic": "Metrics",
        "message": (
            "### CPU Idle Periods, Tie-Breaking Rules, and Edge Cases\n\n"
            "#### 1. CPU Idle Periods\n"
            "* When the Ready Queue is completely empty (e.g. at $t=0$ if the first process arrives at $t=2$), the CPU cannot execute user instructions.\n"
            "* The CPU runs an **idle thread** or executes the `HLT` (halt) instruction to save power until a hardware interrupt arrives.\n"
            "* On Gantt charts, this is drawn as an explicit `[IDLE]` interval from $t=0$ to $t=2$.\n\n"
            "#### 2. Tie-Breaking Conventions\n"
            "* If two processes have the same burst time (in SJF) or same remaining time (in SRTF) or same priority:\n"
            "  1. **Primary Tie-Breaker**: Arrival Time (First-Come, First-Served order).\n"
            "  2. **Secondary Tie-Breaker**: Process ID (lower PID wins, e.g. P1 before P2).\n\n"
            "#### 3. Round Robin Quantum-Boundary Arrival\n"
            "* If a running process finishes its time quantum at time $t$, and simultaneously a new process arrives at time $t$:\n"
            "* **Standard Convention**: The new arrival is placed into the Ready Queue **before** the preempted process returning to the tail."
        ),
        "question": "At time t=4, Process P1's quantum expires while new Process P3 arrives simultaneously. Who enters the Ready Queue first?",
        "hint": "New arrivals take precedence over preempted tasks returning to the queue."
    },

    # =========================================================================
    # MODULE D: ADVANCED TOPICS (REAL-TIME, CFS, MULTIPROCESSOR)
    # =========================================================================

    "linux_cfs": {
        "keywords": [
            "cfs", "completely fair scheduler", "vruntime", "virtual runtime", "red-black tree", "nice value"
        ],
        "regex": r"\b(cfs|completely fair scheduler|vruntime|virtual runtime|nice value)\b",
        "topic": "Fundamentals",
        "message": (
            "### Linux Completely Fair Scheduler (CFS)\n\n"
            "CFS is the default CPU scheduling algorithm in the Linux kernel (introduced in Linux 2.6.23).\n\n"
            "#### 1. Core Principle: Virtual Runtime (`vruntime`)\n"
            "* CFS replaces fixed time slices with a metric called **virtual runtime (`vruntime`)**.\n"
            "* `vruntime` records the exact amount of CPU time a task has consumed, scaled inversely by its **nice value (priority weight)**.\n"
            "* High-priority tasks (negative nice values) accumulate `vruntime` slowly; low-priority tasks accumulate `vruntime` quickly.\n\n"
            "#### 2. Red-Black Tree Data Structure\n"
            "* Runnable processes are stored in a self-balancing **Red-Black Tree** ordered by `vruntime`.\n"
            "* The scheduler always picks the **leftmost node** in the tree (the task with the smallest `vruntime`) in $O(1)$ amortized time.\n"
            "* Adding or removing tasks takes $O(\\log n)$ time.\n\n"
            "#### 3. Nice Values\n"
            "* Range from **-20** (highest priority) to **+19** (lowest priority), with 0 as default."
        ),
        "question": "In the Linux CFS scheduler, does the task with the smallest vruntime or largest vruntime get picked to run next?",
        "hint": "It represents the task that has received the least CPU time so far."
    },

    "real_time_scheduling": {
        "keywords": [
            "real-time scheduling", "real time scheduling", "hard real-time", "soft real-time",
            "rate monotonic", "earliest deadline first", "rms", "edf"
        ],
        "regex": r"\b(real-time|hard real-time|soft real-time|rate monotonic|earliest deadline first|\brms\b|\bedf\b)\b",
        "topic": "Fundamentals",
        "message": (
            "### Real-Time CPU Scheduling: Hard vs. Soft, RMS, and EDF\n\n"
            "In real-time systems, correctness depends not only on the logical result of computation, but on the **time at which results are produced**.\n\n"
            "#### 1. Hard vs. Soft Real-Time\n"
            "* **Hard Real-Time**: Missing a deadline is a catastrophic system failure (e.g. automotive airbag controller, pacemaker, flight avionics).\n"
            "* **Soft Real-Time**: Missing a deadline degrades service quality but does not cause system failure (e.g. video streaming, online multiplayer games).\n\n"
            "#### 2. Rate Monotonic Scheduling (RMS)\n"
            "* A **static-priority** algorithm for periodic tasks.\n"
            "* **Rule**: Tasks with shorter periods are assigned higher priorities ($P \\propto 1/T$).\n"
            "* Optimal static priority algorithm; utilization bound: $U \\le n(2^{1/n} - 1)$ (approaches $\\approx 69.3\\%$ for large $n$).\n\n"
            "#### 3. Earliest Deadline First (EDF)\n"
            "* A **dynamic-priority** algorithm.\n"
            "* **Rule**: The process with the closest upcoming deadline is assigned the highest priority.\n"
            "* Optimal dynamic algorithm; can achieve up to **100% CPU utilization** theoretically."
        ),
        "question": "Does Rate Monotonic Scheduling assign higher priority to tasks with shorter periods or longer periods?",
        "hint": "Think of a task that must run 100 times per second vs 1 time per second."
    },

    "multiprocessor_scheduling": {
        "keywords": [
            "multiprocessor", "multi-core", "smp", "symmetric multiprocessing", "asymmetric multiprocessing",
            "processor affinity", "load balancing", "numa"
        ],
        "regex": r"\b(multiprocessor|multi-core|\bsmp\b|processor affinity|load balancing|\bnuma\b)\b",
        "topic": "Fundamentals",
        "message": (
            "### Multiprocessor and Multi-Core CPU Scheduling\n\n"
            "#### 1. Multiprocessor Architecture\n"
            "* **Asymmetric Multiprocessing (AMP)**: One master core handles OS scheduling and I/O; worker cores run user tasks. Simple, but master is a bottleneck.\n"
            "* **Symmetric Multiprocessing (SMP)**: Each CPU core is self-scheduling, either sharing a common ready queue or maintaining private per-core ready queues.\n\n"
            "#### 2. Processor Affinity\n"
            "* A running process populates the local L1/L2 cache of its assigned core.\n"
            "* **Processor Affinity** means the OS tries to keep a process running on the same CPU core to avoid costly cache invalidation.\n"
            "* **Soft Affinity**: The OS attempts to keep the process on the same core, but may migrate it if another core becomes idle.\n"
            "* **Hard Affinity**: The process is strictly locked to specific cores (e.g., via `sched_setaffinity()` in Linux).\n\n"
            "#### 3. Load Balancing\n"
            "* **Push Migration**: A background task periodically checks core loads and pushes processes from overloaded cores to idle cores.\n"
            "* **Pull Migration**: An idle core actively pulls waiting processes from the queue of a busy core."
        ),
        "question": "Why does an operating system prefer to keep a process running on the same CPU core instead of frequently migrating it?",
        "hint": "Consider what happens to the hardware L1 and L2 caches when migrating."
    }
}


# =============================================================================
# MATCHING & RETRIEVAL ENGINE
# =============================================================================

def find_knowledge_entry(query: str, current_topic: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Matches user query against the comprehensive knowledge catalog using specificity scoring.
    Ensures exact multi-word phrases and word-boundary matches beat generic single-word matches.
    """
    q_lower = query.lower()

    best_match = None
    best_score = 0

    for key, data in KNOWLEDGE_CATALOG.items():
        score = 0

        # 1. Check exact multi-word keywords (higher score for longer, more specific phrases)
        for kw in data["keywords"]:
            if " " in kw and kw in q_lower:
                phrase_score = len(kw) * 3
                if phrase_score > score:
                    score = phrase_score

        # 2. Check regex pattern for word boundaries
        if "regex" in data:
            matches = re.findall(data["regex"], q_lower, re.IGNORECASE)
            if matches:
                # Award points based on longest matched word
                for m in matches:
                    matched_str = m[0] if isinstance(m, tuple) else m
                    word_score = len(matched_str) * 2
                    if word_score > score:
                        score = word_score

        # 3. Exact single-word keyword matches (using word boundaries to avoid substring false positives)
        for kw in data["keywords"]:
            if " " not in kw:
                # Escape regex characters
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, q_lower):
                    kw_score = len(kw) * 2
                    if kw_score > score:
                        score = kw_score

        if score > best_score:
            best_score = score
            best_match = data

    # Threshold: must have a meaningful score to avoid spurious matches
    if best_score >= 6:
        return best_match

    return None


def evaluate_catalog_answer(last_assistant_msg: str, user_answer: str) -> Optional[Dict[str, Any]]:
    """
    Evaluates student response against canonical understanding check questions.
    Returns structured feedback if a known question was being answered, else None.
    """
    last_lower = last_assistant_msg.lower()
    ans_lower = user_answer.strip().lower()

    # 1. Preemption check: running to ready circumstance
    if "switch from running to ready" in last_lower or "circumstance does an algorithm switch" in last_lower:
        if any(w in ans_lower for w in ["timer", "interrupt", "timer interrupt", "asynchronous"]):
            return {
                "message": (
                    "**Spot on!** An **asynchronous timer interrupt** forcibly suspends the running process and moves it from Running to Ready. "
                    "This is the hallmark of **preemptive** scheduling.\n\n"
                    "Now, what potential concurrency issue can happen if two processes are preempted while modifying a shared data structure in memory?"
                ),
                "action": "evaluate_answer",
                "question": "What potential concurrency issue can happen if two processes are preempted while modifying a shared data structure in memory?",
                "hint": "Think about race conditions and synchronization locks.",
                "concepts_demonstrated": ["preemption", "timer_interrupt"],
                "misconception": None
            }
        elif any(w in ans_lower for w in ["voluntary", "i/o", "io", "request"]):
            return {
                "message": (
                    "**Good attempt, but here's the key distinction**: When a process issues an I/O request, it voluntarily moves from **Running $\\to$ Waiting (Blocked)**, which is cooperative (non-preemptive).\n\n"
                    "Preemption occurs when an external event like a **hardware timer interrupt** forcibly moves a process from **Running $\\to$ Ready**.\n\n"
                    "Does this distinction between the Waiting and Ready states make sense?"
                ),
                "action": "evaluate_answer",
                "question": "Does this distinction between the Waiting and Ready states make sense?",
                "hint": "Waiting means waiting on an external device; Ready means ready to run on CPU.",
                "concepts_demonstrated": [],
                "misconception": "Confusing Running->Waiting (voluntary I/O) with Running->Ready (preemptive timer interrupt)."
            }

    # 2. Process vs Program: multiple processes from single program
    if "single program stored on disk be executed multiple times" in last_lower:
        if any(w in ans_lower for w in ["yes", "yeah", "can", "possible", "true", "sure", "of course"]):
            return {
                "message": (
                    "**Exactly right!** You can execute multiple instances of the same program binary on disk (for example, opening multiple terminal windows or browser sessions). "
                    "Each instance becomes a distinct **process** with its own PID, stack, heap, and PCB, while sharing the same read-only text segment in RAM.\n\n"
                    "Which kernel data structure maintains this private execution state for each process?"
                ),
                "action": "evaluate_answer",
                "question": "Which kernel data structure maintains this private execution state for each process?",
                "hint": "It contains the PID, saved registers, and program counter.",
                "concepts_demonstrated": ["process_vs_program", "multiple_processes"],
                "misconception": None
            }
        elif any(w in ans_lower for w in ["no", "cannot", "false", "cant", "can't"]):
            return {
                "message": (
                    "**Actually, yes!** Think of opening three separate calculator windows. Each is a separate active process with its own PID and memory space, all created from the same single `calc.exe` program file stored on disk.\n\n"
                    "Does that help clarify the distinction between passive program and active process?"
                ),
                "action": "evaluate_answer",
                "question": "Does that help clarify the distinction between passive program and active process?",
                "hint": "Program is the file on disk; process is an instance in memory.",
                "concepts_demonstrated": [],
                "misconception": "Believing a program file can only create a single process at a time."
            }

    # 3. Process states: I/O completion destination state
    if "i/o operation finishes for a waiting process" in last_lower or "move directly to running, or to the ready queue" in last_lower:
        if "ready" in ans_lower:
            return {
                "message": (
                    "**Precisely!** It moves to the **Ready Queue**. It cannot move directly to Running because another process is likely already executing on the CPU core. "
                    "The dispatcher must select it when the core becomes available.\n\n"
                    "Which scheduler selects a process from the Ready Queue to run: the long-term scheduler or the short-term scheduler?"
                ),
                "action": "evaluate_answer",
                "question": "Which scheduler selects a process from the Ready Queue to run: the long-term scheduler or the short-term scheduler?",
                "hint": "It executes frequently (every 10-100 ms).",
                "concepts_demonstrated": ["process_states", "state_transitions"],
                "misconception": None
            }
        elif "running" in ans_lower:
            return {
                "message": (
                    "**Not quite.** Remember that another process may already be actively executing on the CPU core. "
                    "The process cannot preempt the CPU immediately; it must wait its turn in the **Ready Queue** until selected by the CPU scheduler.\n\n"
                    "Does that distinction between Ready and Running make sense?"
                ),
                "action": "evaluate_answer",
                "question": "Does that distinction between Ready and Running make sense?",
                "hint": "Waiting -> Ready -> Running is the required path.",
                "concepts_demonstrated": [],
                "misconception": "Assuming I/O completion immediately interrupts and seizes the CPU core."
            }

    # 4. Convoy effect: how Round Robin solves it
    if "how does round robin scheduling solve the convoy effect" in last_lower:
        if any(w in ans_lower for w in ["quantum", "slice", "preempt", "timer", "interrupt", "time slice"]):
            return {
                "message": (
                    "**Exactly!** Round Robin enforces a finite **Time Quantum**. Even if a massive CPU-bound job arrives first, "
                    "the OS preempts it after its quantum expires, allowing short I/O-bound processes to quickly execute and proceed to their I/O devices.\n\n"
                    "What happens to average waiting time when short processes don't have to wait for the entire burst of a long process?"
                ),
                "action": "evaluate_answer",
                "question": "What happens to average waiting time when short processes don't have to wait for the entire burst of a long process?",
                "hint": "Does average waiting time decrease or increase?",
                "concepts_demonstrated": ["convoy_effect", "round_robin_solution"],
                "misconception": None
            }

    # 5. SJF: why difficult to implement
    if "why is pure shortest job first difficult to implement" in last_lower:
        if any(w in ans_lower for w in ["know", "future", "burst", "advance", "predict", "length", "cannot know"]):
            return {
                "message": (
                    "**Spot on!** The operating system cannot know the future CPU burst length of a user program before it executes. "
                    "It can only estimate future bursts using exponential smoothing techniques.\n\n"
                    "What mathematical smoothing formula does an OS use to predict the next burst?"
                ),
                "action": "evaluate_answer",
                "question": "What mathematical smoothing formula does an OS use to predict the next burst?",
                "hint": "It involves tau_{n+1} and a smoothing factor alpha.",
                "concepts_demonstrated": ["sjf_implementation_limits"],
                "misconception": None
            }

    # 6. SRTF: remaining vs original burst
    if "compare total burst time or remaining burst time" in last_lower or "original burst time or its remaining burst time" in last_lower:
        if "remaining" in ans_lower:
            return {
                "message": (
                    "**Precisely!** SRTF always compares the new process's burst against the **remaining execution time** of the currently running job. "
                    "If the newcomer needs less time than what remains of the runner, the runner is preempted.\n\n"
                    "What is the primary drawback of frequent preemptions in SRTF?"
                ),
                "action": "evaluate_answer",
                "question": "What is the primary drawback of frequent preemptions in SRTF?",
                "hint": "Think about the overhead of switching processes repeatedly.",
                "concepts_demonstrated": ["srtf_preemption_rule"],
                "misconception": None
            }
        elif any(w in ans_lower for w in ["total", "original", "initial"]):
            return {
                "message": (
                    "**Not quite.** The currently running process has already completed part of its burst. "
                    "SRTF considers only how much time is left (**remaining burst time**). That is why it is called Shortest *Remaining* Time First!"
                ),
                "action": "evaluate_answer",
                "question": "Would a running job with 1 ms left be preempted by a new job with burst 2 ms?",
                "hint": "1 ms remaining is shorter than 2 ms.",
                "concepts_demonstrated": [],
                "misconception": "Evaluating total initial burst rather than remaining time."
            }

    # 7. Priority convention
    if "does priority 0 represent the highest priority or lowest priority" in last_lower:
        if "high" in ans_lower:
            return {
                "message": (
                    "**Spot on!** In standard Operating Systems textbooks (Silberschatz) and Unix environments, 0 is the **highest priority** (think of 1st place in a race).\n\n"
                    "What major issue can occur for low-priority processes if high-priority processes keep arriving continuously?"
                ),
                "action": "evaluate_answer",
                "question": "What major issue can occur for low-priority processes if high-priority processes keep arriving continuously?",
                "hint": "They may wait forever.",
                "concepts_demonstrated": ["priority_convention"],
                "misconception": None
            }
        elif "low" in ans_lower:
            return {
                "message": (
                    "**Careful with conventions!** In the standard Silberschatz OS textbook convention, 0 represents the **highest** priority (think 1st place). "
                    "However, in Windows, larger integers represent higher priorities, so always check the convention stated in the problem!"
                ),
                "action": "evaluate_answer",
                "question": "If priority 0 is highest, will priority 1 preempt priority 3 under preemptive priority scheduling?",
                "hint": "1 is higher priority than 3.",
                "concepts_demonstrated": [],
                "misconception": "Assuming higher integer always means higher priority."
            }

    # 8. Starvation & aging
    if "how does the aging technique guarantee" in last_lower or "mechanism prevents indefinite blocking" in last_lower:
        if any(w in ans_lower for w in ["priority", "increase", "increment", "gradually", "age", "waiting", "time"]):
            return {
                "message": (
                    "**Perfect!** Aging gradually increases the priority of waiting processes over time. "
                    "Eventually, even the lowest-priority process becomes the highest-priority job and is guaranteed execution.\n\n"
                    "Which scheduling algorithms are most vulnerable to starvation without aging?"
                ),
                "action": "evaluate_answer",
                "question": "Which scheduling algorithms are most vulnerable to starvation without aging?",
                "hint": "Think of Priority, SJF, and SRTF.",
                "concepts_demonstrated": ["aging_mechanism", "starvation_prevention"],
                "misconception": None
            }

    # 9. Round Robin degradation
    if "which algorithm does round robin become equivalent to when the time quantum" in last_lower:
        if any(w in ans_lower for w in ["fcfs", "first come", "first-come"]):
            return {
                "message": (
                    "**Spot on!** When the time quantum exceeds the longest CPU burst, no process is ever preempted by the timer, "
                    "and Round Robin behaves identically to **First-Come, First-Served (FCFS)**.\n\n"
                    "What happens if the time quantum is set extremely small (approaching 0) instead?"
                ),
                "action": "evaluate_answer",
                "question": "What happens if the time quantum is set extremely small (approaching 0) instead?",
                "hint": "Think about context switch overhead.",
                "concepts_demonstrated": ["rr_quantum_extremes"],
                "misconception": None
            }

    # 10. Metrics numerical check
    if "what is its waiting time" in last_lower and "needs 5 ms of burst" in last_lower:
        if any(ans_lower == target or ans_lower.startswith(target) for target in ["5", "5 ms", "5ms", "5 milliseconds", "it is 5"]):
            return {
                "message": (
                    "**Excellent calculation!** Turnaround Time $\\text{TAT} = \\text{CT} - \\text{AT} = 12 - 2 = 10$ ms. "
                    "Then Waiting Time $\\text{WT} = \\text{TAT} - \\text{BT} = 10 - 5 = 5$ ms.\n\n"
                    "Would you like to solve a complete problem with multiple processes arriving at different times?"
                ),
                "action": "evaluate_answer",
                "question": "Would you like to solve a complete problem with multiple processes arriving at different times?",
                "hint": "Type 'yes' or 'give me a problem'.",
                "concepts_demonstrated": ["tat_calculation", "wt_calculation"],
                "misconception": None
            }

    # 11. CFS smallest vruntime check
    if "smallest vruntime or largest vruntime" in last_lower:
        if any(w in ans_lower for w in ["smallest", "smaller", "least", "minimum", "leftmost", "lowest"]):
            return {
                "message": (
                    "**Spot on!** The task with the **smallest virtual runtime (`vruntime`)** is always chosen from the leftmost node of the Red-Black Tree. "
                    "This guarantees that processes which have had the least CPU execution time receive service next, maintaining fair CPU allocation.\n\n"
                    "Now, if a process has a **negative nice value** (high priority), does its `vruntime` grow faster or slower than normal?"
                ),
                "action": "evaluate_answer",
                "question": "If a process has a negative nice value (high priority), does its vruntime grow faster or slower than normal?",
                "hint": "Think about whether it needs to stay at the front of the line longer.",
                "concepts_demonstrated": ["cfs_smallest_vruntime", "rbtree_leftmost_node"],
                "misconception": None
            }
        elif any(w in ans_lower for w in ["largest", "larger", "most", "highest"]):
            return {
                "message": (
                    "**Careful!** If CFS picked the largest `vruntime`, the process that has already consumed the most CPU would keep running, starving others!\n\n"
                    "Instead, CFS always selects the task with the **smallest `vruntime`** (the leftmost node in the Red-Black Tree) so tasks that have received the least CPU time get scheduled.\n\n"
                    "Does it make sense why picking the smallest `vruntime` ensures fairness?"
                ),
                "action": "evaluate_answer",
                "question": "Does it make sense why picking the smallest vruntime ensures fairness?",
                "hint": "Virtual runtime measures CPU time consumed so far.",
                "concepts_demonstrated": [],
                "misconception": "Believing CFS picks the process with the largest virtual runtime."
            }

    # 12. Real-Time RMS period priority check
    if "shorter periods or longer periods" in last_lower:
        if any(w in ans_lower for w in ["shorter", "short", "smaller", "shorter period"]):
            return {
                "message": (
                    "**Exactly right!** Rate Monotonic Scheduling (RMS) assigns higher static priorities to tasks with **shorter periods** (higher execution frequencies). "
                    "Mathematically, $P \\propto \\frac{1}{T}$. It is the provably optimal static-priority scheduling algorithm for periodic real-time tasks.\n\n"
                    "In contrast to RMS's static priorities, how does Earliest Deadline First (EDF) dynamically prioritize tasks?"
                ),
                "action": "evaluate_answer",
                "question": "How does Earliest Deadline First (EDF) dynamically prioritize tasks?",
                "hint": "Think about which task has the nearest upcoming deadline.",
                "concepts_demonstrated": ["rms_shorter_period_priority", "real_time_rate_monotonic"],
                "misconception": None
            }

    # 13. Multiprocessor Affinity check
    if "prefer to keep a process running on the same cpu core" in last_lower:
        if any(w in ans_lower for w in ["cache", "l1", "l2", "affinity", "warm cache", "invalidate", "memory", "reload"]):
            return {
                "message": (
                    "**Spot on!** This is called **Processor Affinity**. When a process runs on a CPU core, its active data populates the core's private hardware caches (L1/L2). "
                    "Migrating the process to another core invalidates those warm caches and incurs severe memory latency while reloading lines from RAM.\n\n"
                    "What is the difference between **soft affinity** and **hard affinity** in multi-core operating systems?"
                ),
                "action": "evaluate_answer",
                "question": "What is the difference between soft affinity and hard affinity in multi-core operating systems?",
                "hint": "Think about whether core binding is a preference or an enforced restriction.",
                "concepts_demonstrated": ["processor_affinity", "cache_warmth"],
                "misconception": None
            }

    # 14. Kernel Preemption check
    if "preemptive kernel critical for real-time" in last_lower or "preemptive kernel compared to a non-preemptive kernel" in last_lower:
        if any(w in ans_lower for w in ["latency", "bound", "response", "deadline", "quick", "interrupt", "deterministic", "dispatch"]):
            return {
                "message": (
                    "**Spot on!** In a non-preemptive kernel, a task running in kernel space (e.g. executing a long system call) cannot be interrupted, creating arbitrary latency delays that can cause a real-time task to miss its strict deadline. "
                    "A preemptive kernel allows high-priority tasks to preempt kernel execution immediately, guaranteeing bounded **dispatch latency**.\n\n"
                    "What mechanism does the kernel use to protect shared kernel data structures when kernel preemption is enabled?"
                ),
                "action": "evaluate_answer",
                "question": "What mechanism does the kernel use to protect shared kernel data structures when kernel preemption is enabled?",
                "hint": "Think about mutexes, spinlocks, or disabling interrupts.",
                "concepts_demonstrated": ["preemptive_kernel", "real_time_bounded_latency"],
                "misconception": None
            }
        elif any(w in ans_lower for w in ["faster", "speed", "throughput"]):
            return {
                "message": (
                    "**Good attempt, but here's the crucial nuance**: Preemptive kernels aren't necessarily faster overall; in fact, synchronization adds slight overhead. "
                    "Their critical advantage for real-time systems is **bounded dispatch latency**—ensuring high-priority tasks never wait behind long kernel routines.\n\n"
                    "Does the distinction between raw throughput and predictable responsiveness make sense?"
                ),
                "action": "evaluate_answer",
                "question": "Does the distinction between raw throughput and predictable responsiveness make sense?",
                "hint": "Real-time systems prioritize predictability over throughput.",
                "concepts_demonstrated": [],
                "misconception": "Believing preemptive kernels are primarily designed for throughput rather than predictable low latency."
            }

    # 15. Seven-State Model: Blocked-Suspended completion
    if "blocked-suspended" in last_lower or "i/o operation completes for a process in the blocked-suspended state" in last_lower:
        if any(w in ans_lower for w in ["ready-suspended", "ready suspended", "ready/suspend", "ready suspend"]):
            return {
                "message": (
                    "**Precisely!** When its I/O finishes, the process is no longer blocked waiting for device input, but its memory pages are still swapped out to secondary storage on disk. "
                    "Thus, it transitions to **Ready-Suspended (Ready/Suspend)** until the medium-term scheduler swaps it back into RAM.\n\n"
                    "Which scheduler decides when to swap a suspended process back into main memory: the short-term, medium-term, or long-term scheduler?"
                ),
                "action": "evaluate_answer",
                "question": "Which scheduler decides when to swap a suspended process back into main memory?",
                "hint": "Think of the medium-term scheduler (the swapper).",
                "concepts_demonstrated": ["seven_state_model", "blocked_suspended_transition"],
                "misconception": None
            }
        elif "ready" in ans_lower:
            return {
                "message": (
                    "**Close, but remember memory placement**: It moves to **Ready-Suspended**, not active Ready! "
                    "While it is now ready to run from an I/O perspective, its address space is still swapped out to disk and must be loaded back into RAM by the medium-term scheduler first."
                ),
                "action": "evaluate_answer",
                "question": "Does that distinction between being ready in RAM versus ready on disk make sense?",
                "hint": "Ready means in RAM; Ready-Suspended means in secondary storage.",
                "concepts_demonstrated": [],
                "misconception": "Overlooking that suspended processes reside on disk and cannot execute until swapped in."
            }

    # 16. PCB: register saving
    if "why must cpu register values be saved into the pcb" in last_lower:
        if any(w in ans_lower for w in ["restore", "resume", "state", "continue", "program counter", "registers", "execution", "values", "same"]):
            return {
                "message": (
                    "**Exactly right!** When a process is preempted, its temporary calculation state, Program Counter (PC), stack pointer, and general-purpose registers reside in the CPU's hardware registers. "
                    "Saving them into its **Process Control Block (PCB)** allows the OS to reload the exact same values later so the process resumes seamlessly without corrupting its calculations.\n\n"
                    "Where does the PCB reside in memory: user space or protected kernel space?"
                ),
                "action": "evaluate_answer",
                "question": "Where does the PCB reside in memory: user space or protected kernel space?",
                "hint": "User applications must not be able to modify their own PCB fields like priority or PID.",
                "concepts_demonstrated": ["pcb_register_saving", "context_preservation"],
                "misconception": None
            }

    # 17. Dispatcher vs CPU Scheduler
    if "difference in role between the cpu scheduler and the dispatcher" in last_lower:
        if any(w in ans_lower for w in ["select", "choose", "pick", "switch", "give", "control", "dispatcher switches", "scheduler selects"]):
            return {
                "message": (
                    "**Spot on!** The **CPU Scheduler** is the decision-maker: it executes an algorithm (like Round Robin or SJF) to *select* which process from the Ready Queue should run next. "
                    "The **Dispatcher** is the executor: it actually performs the low-level context switch, switches CPU mode from kernel to user, and jumps to the program counter to let the selected process run.\n\n"
                    "What is the time taken by the dispatcher to stop one process and start another called?"
                ),
                "action": "evaluate_answer",
                "question": "What is the time taken by the dispatcher to stop one process and start another called?",
                "hint": "It is called dispatch latency.",
                "concepts_demonstrated": ["scheduler_vs_dispatcher", "dispatcher_role"],
                "misconception": None
            }

    # 18. Context switch vs mode switch
    if "does a simple system call that does not block cause a full context switch or just a mode switch" in last_lower:
        if any(w in ans_lower for w in ["mode", "mode switch", "just mode", "only mode"]):
            return {
                "message": (
                    "**Exactly right!** It causes only a **mode switch** (from user mode to kernel mode and back). The process remains the current running process on the CPU; memory address spaces and TLB cache entries do not need to be flushed or swapped.\n\n"
                    "Why is a full context switch significantly more expensive in CPU clock cycles than a simple mode switch?"
                ),
                "action": "evaluate_answer",
                "question": "Why is a full context switch significantly more expensive in CPU clock cycles than a simple mode switch?",
                "hint": "Think about cache invalidation, TLB flushing, and saving all architectural registers.",
                "concepts_demonstrated": ["mode_switch_vs_context_switch"],
                "misconception": None
            }

    # 19. CPU vs I/O burst: video rendering
    if "video rendering program tend to be cpu-bound or i/o-bound" in last_lower:
        if any(w in ans_lower for w in ["cpu", "cpu-bound", "cpu bound"]):
            return {
                "message": (
                    "**Spot on!** Video rendering performs heavy mathematical transformations (matrix multiplication, color grading, ray tracing) on frames in memory with few external device interruptions, making it heavily **CPU-bound** with very long CPU bursts.\n\n"
                    "In contrast, what is an everyday example of an I/O-bound process?"
                ),
                "action": "evaluate_answer",
                "question": "What is an everyday example of an I/O-bound process?",
                "hint": "Think of text editors, web browsers, or terminal shells waiting for user keystrokes.",
                "concepts_demonstrated": ["cpu_bound_characteristics"],
                "misconception": None
            }

    # 20. Schedulers types: degree of multiprogramming
    if "controls the degree of multiprogramming" in last_lower:
        if any(w in ans_lower for w in ["long-term", "long term", "job scheduler", "lts", "long"]):
            return {
                "message": (
                    "**Precisely!** The **Long-Term Scheduler (Job Scheduler)** determines which jobs from the disk pool are admitted into main memory as active processes, thereby directly controlling the **degree of multiprogramming** (number of processes concurrently in memory).\n\n"
                    "If the degree of multiprogramming is set too high, what severe operating system problem can occur?"
                ),
                "action": "evaluate_answer",
                "question": "If the degree of multiprogramming is set too high, what severe operating system problem can occur?",
                "hint": "Think of thrashing when RAM is exhausted.",
                "concepts_demonstrated": ["long_term_scheduler", "degree_of_multiprogramming"],
                "misconception": None
            }

    # 21. Ready queue vs Device queue
    if "initiates a disk read, does it remain in the ready queue or move to the disk device queue" in last_lower:
        if any(w in ans_lower for w in ["device", "device queue", "waiting", "blocked", "disk"]):
            return {
                "message": (
                    "**Exactly right!** When a process requests a disk read, it cannot execute further instructions until the data arrives. It voluntarily yields the CPU and moves to the disk's **Device Queue (Waiting / Blocked Queue)**.\n\n"
                    "What hardware mechanism signals the CPU when the disk has finished transferring the requested data blocks?"
                ),
                "action": "evaluate_answer",
                "question": "What hardware mechanism signals the CPU when the disk has finished transferring the requested data blocks?",
                "hint": "Think of hardware I/O interrupts.",
                "concepts_demonstrated": ["device_queue", "running_to_waiting"],
                "misconception": None
            }

    # 22. FCFS disadvantage: Convoy Effect
    if "primary disadvantage of fcfs when a cpu-bound job arrives before multiple short i/o-bound jobs" in last_lower:
        if any(w in ans_lower for w in ["convoy", "convoy effect", "waiting", "bottleneck", "delay", "starve", "wait"]):
            return {
                "message": (
                    "**Spot on!** That is the famous **Convoy Effect**. All the short I/O-bound processes must sit waiting behind the single long CPU-bound process. "
                    "While the CPU job runs, all I/O devices sit idle; when the CPU job finishes, all processes rush to I/O and the CPU sits idle.\n\n"
                    "Which preemptive scheduling algorithm directly cures the Convoy Effect by imposing time limits?"
                ),
                "action": "evaluate_answer",
                "question": "Which preemptive scheduling algorithm directly cures the Convoy Effect by imposing time limits?",
                "hint": "Think of Round Robin.",
                "concepts_demonstrated": ["fcfs_convoy_effect"],
                "misconception": None
            }

    # 23. Burst prediction: alpha = 1
    if "alpha is set to 1 in the exponential smoothing formula" in last_lower:
        if any(w in ans_lower for w in ["recent", "last", "previous", "actual", "t_n", "tn", "latest", "most recent"]):
            return {
                "message": (
                    "**Precisely!** The exponential smoothing formula is $\\tau_{n+1} = \\alpha t_n + (1 - \\alpha)\\tau_n$. If $\\alpha = 1$, the formula reduces to $\\tau_{n+1} = t_n$, "
                    "meaning the prediction relies entirely on the **most recent actual CPU burst**, ignoring all older history!\n\n"
                    "Conversely, what does setting $\\alpha = 0$ mean for the prediction?"
                ),
                "action": "evaluate_answer",
                "question": "What does setting alpha = 0 mean for the prediction?",
                "hint": "Recent history is completely ignored, keeping the initial estimate constant.",
                "concepts_demonstrated": ["exponential_smoothing_alpha_extremes"],
                "misconception": None
            }

    # 24. Time quantum tradeoffs: 10 ms quantum with 1 ms switch
    if "quantum is 10 ms and a context switch takes 1 ms" in last_lower:
        if any(w in ans_lower for w in ["9", "10", "9.09", "9%", "10%", "one tenth", "1/11", "9.1"]):
            return {
                "message": (
                    "**Spot on!** If a process runs for 10 ms and the dispatcher takes 1 ms to context switch, the total CPU allocation cycle is 11 ms. "
                    "The overhead is $\\frac{1}{11} \\approx 9.09\\%$ (or roughly $10\\%$ of execution time) wasted purely on administrative switching rather than productive user work.\n\n"
                    "As a general rule of thumb from Silberschatz, what percentage of CPU bursts should be shorter than the time quantum in a well-tuned system?"
                ),
                "action": "evaluate_answer",
                "question": "What percentage of CPU bursts should be shorter than the time quantum in a well-tuned system?",
                "hint": "Textbooks recommend roughly 80%.",
                "concepts_demonstrated": ["context_switch_overhead_percentage"],
                "misconception": None
            }

    # 25. Multilevel Queue: process mobility
    if "can processes change which queue they belong to in a standard multilevel queue" in last_lower:
        if any(w in ans_lower for w in ["no", "cannot", "cant", "can't", "false", "permanent", "fixed"]):
            return {
                "message": (
                    "**Exactly right!** In standard **Multilevel Queue (MLQ)** scheduling, processes are permanently assigned to a specific queue (e.g. Foreground vs. Background) based on their intrinsic nature and cannot migrate between queues.\n\n"
                    "What upgraded algorithm was created to allow processes to dynamically move between queues based on their runtime behavior?"
                ),
                "action": "evaluate_answer",
                "question": "What upgraded algorithm was created to allow processes to dynamically move between queues based on their runtime behavior?",
                "hint": "Think of Multilevel Feedback Queue (MLFQ).",
                "concepts_demonstrated": ["mlq_fixed_assignment"],
                "misconception": None
            }

    # 26. Multilevel Feedback Queue: CPU-bound demotion
    if "uses up its entire time quantum without doing i/o" in last_lower or "happens to a cpu-bound process in mlfq" in last_lower:
        if any(w in ans_lower for w in ["demot", "lower", "lower queue", "drops", "next queue", "moved down", "down"]):
            return {
                "message": (
                    "**Spot on!** If a process uses its entire quantum without relinquishing the CPU for I/O, MLFQ infers that it is CPU-bound and **demotes it to the next lower-priority queue**. "
                    "In that lower queue, it receives a longer time quantum but lower priority.\n\n"
                    "What essential mechanism does MLFQ employ to ensure that these demoted processes do not starve?"
                ),
                "action": "evaluate_answer",
                "question": "What essential mechanism does MLFQ employ to ensure that these demoted processes do not starve?",
                "hint": "Think of periodic Priority Boost / Aging.",
                "concepts_demonstrated": ["mlfq_demotion_rule"],
                "misconception": None
            }

    # 27. Algorithm comparison: provably optimal
    if "provably optimal for minimizing average waiting time" in last_lower:
        if any(w in ans_lower for w in ["sjf", "shortest job", "srtf", "shortest remaining"]):
            return {
                "message": (
                    "**Precisely!** **Shortest Job First (SJF)** (and its preemptive counterpart SRTF) is mathematically provable to minimize the average waiting time for any given set of stationary processes "
                    "because scheduling shorter tasks earlier reduces the queue wait time for all subsequent tasks.\n\n"
                    "If SJF is optimal, why isn't it universally used for all desktop operating systems?"
                ),
                "action": "evaluate_answer",
                "question": "If SJF is optimal, why isn't it universally used for all desktop operating systems?",
                "hint": "The OS cannot know the future length of the next CPU burst in advance.",
                "concepts_demonstrated": ["sjf_optimality_proof"],
                "misconception": None
            }

    # 28. Gantt chart: idle period
    if "no ready processes between t=3 and t=6" in last_lower:
        if any(w in ans_lower for w in ["idle", "cpu idle", "empty", "blank"]):
            return {
                "message": (
                    "**Exactly right!** That period is marked as **CPU Idle** (often written as `[3 - 6: CPU Idle]`). It indicates that no processes were in the Ready Queue, so the CPU was either executing the idle loop or placed in a low-power halt state.\n\n"
                    "Does CPU idle time count towards a process's Turnaround Time or Waiting Time?"
                ),
                "action": "evaluate_answer",
                "question": "Does CPU idle time count towards a process's Turnaround Time or Waiting Time?",
                "hint": "Turnaround Time is strictly Completion Time minus Arrival Time.",
                "concepts_demonstrated": ["gantt_idle_representation"],
                "misconception": None
            }

    # 29. Idle time and ties: simultaneous arrival and quantum expiration
    if "quantum expires while new process p3 arrives simultaneously" in last_lower or "who enters the ready queue first" in last_lower:
        if any(w in ans_lower for w in ["new", "p3", "arrival", "newly arrived", "convention", "first"]):
            return {
                "message": (
                    "**Spot on!** By standard textbook convention (Silberschatz), a **newly arrived process (P3)** is placed into the Ready Queue *before* a running process whose quantum just expired (P1). "
                    "This gives incoming tasks an immediate chance at service and prevents preempted tasks from monopolizing the front of the queue.\n\n"
                    "Would you like to solve a complete problem where simultaneous arrivals and ties are demonstrated in a Gantt chart?"
                ),
                "action": "evaluate_answer",
                "question": "Would you like to solve a complete problem where simultaneous arrivals and ties are demonstrated in a Gantt chart?",
                "hint": "Type 'yes' or 'show example'.",
                "concepts_demonstrated": ["tie_breaking_rules"],
                "misconception": None
            }

    # 30. Follow-up: Concurrency race condition
    if "concurrency issue can happen if two processes are preempted while modifying a shared data structure" in last_lower:
        if any(w in ans_lower for w in ["race", "race condition", "corruption", "inconsistency", "data corruption"]):
            return {
                "message": (
                    "**Spot on!** That is a **Race Condition**: when two or more processes concurrently access and manipulate shared data, "
                    "and the outcome depends on the particular order in which access takes place. To prevent this, operating systems use critical section synchronization primitives like mutexes and semaphores.\n\n"
                    "Would you like to explore how modern preemptive kernels solve this synchronization problem?"
                ),
                "action": "evaluate_answer",
                "question": "Would you like to explore how modern preemptive kernels solve this synchronization problem?",
                "hint": "Type 'yes' or ask about spinlocks and mutexes.",
                "concepts_demonstrated": ["race_conditions", "preemption_concurrency"],
                "misconception": None
            }

    # 31. Follow-up: Kernel data structure holding private execution state
    if "which kernel data structure maintains this private execution state for each process" in last_lower:
        if any(w in ans_lower for w in ["pcb", "process control block", "task_struct"]):
            return {
                "message": (
                    "**Exactly right!** The **Process Control Block (PCB)** (called `task_struct` in Linux) is the kernel data structure that encapsulates all per-process state: PID, saved register contents, page tables, open file descriptors, and scheduling priority.\n\n"
                    "Would you like to explore context switching mechanics or process state transitions next?"
                ),
                "action": "evaluate_answer",
                "question": "Would you like to explore context switching mechanics or process state transitions next?",
                "hint": "Type 'context switching' or 'state transitions'.",
                "concepts_demonstrated": ["pcb_role", "linux_task_struct"],
                "misconception": None
            }

    # 32. Follow-up: Dispatch latency
    if "time taken by the dispatcher to stop one process and start another called" in last_lower:
        if any(w in ans_lower for w in ["dispatch latency", "latency"]):
            return {
                "message": (
                    "**Spot on!** That is **Dispatch Latency**: the total elapsed time between when the short-term scheduler decides to stop one process and when the new process begins executing on the CPU core. "
                    "In real-time operating systems, minimizing dispatch latency is the primary engineering objective.\n\n"
                    "Would you like to explore how real-time schedulers like RMS and EDF bound this latency?"
                ),
                "action": "evaluate_answer",
                "question": "Would you like to explore how real-time schedulers like RMS and EDF bound this latency?",
                "hint": "Type 'yes' or ask about RMS and EDF.",
                "concepts_demonstrated": ["dispatch_latency_definition"],
                "misconception": None
            }

    # 33. Follow-up: MLFQ Priority Boost
    if "mechanism does mlfq employ to ensure that these demoted processes do not starve" in last_lower:
        if any(w in ans_lower for w in ["boost", "priority boost", "aging", "periodic boost"]):
            return {
                "message": (
                    "**Exactly right!** MLFQ uses a periodic **Priority Boost** (Rule 5: After some time period $S$, move all jobs in the system to the top queue). "
                    "This guarantees that starving CPU-bound jobs get a chance to run again, and allows processes whose behavior changed from CPU-bound to I/O-bound to be treated appropriately!\n\n"
                    "Would you like to see a complete worked example showing how MLFQ demotes and boosts processes?"
                ),
                "action": "evaluate_answer",
                "question": "Would you like to see a complete worked example showing how MLFQ demotes and boosts processes?",
                "hint": "Type 'yes' or 'show example'.",
                "concepts_demonstrated": ["mlfq_priority_boost", "mlfq_starvation_prevention"],
                "misconception": None
            }

    return None

