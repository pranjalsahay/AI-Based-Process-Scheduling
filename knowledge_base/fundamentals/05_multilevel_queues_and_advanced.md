# Multilevel Queues and Multilevel Feedback Queues (MLFQ)

## 1. Multilevel Queue (MLQ) Scheduling
When processes in an operating system have fundamentally divergent requirements:
* **Interactive (Foreground) Tasks**: Require rapid response times (low latency) for human interaction (text editors, terminals, browsers).
* **Batch (Background) Tasks**: Require high throughput and long execution slices without frequent interruptions (compilers, database indexing).

In a **Multilevel Queue (MLQ)** system:
1. The Ready Queue is permanently partitioned into several separate queues (e.g. System, Interactive, Interactive Editing, Batch, Student).
2. Each process is permanently assigned to one queue upon entry based on its properties (memory size, priority, process type).
3. Each queue has its own scheduling algorithm:
   * Foreground queue: Round Robin (RR) with a small quantum (e.g. 8 ms).
   * Background queue: First-Come, First-Served (FCFS).

### Inter-Queue Scheduling Policies:
* **Fixed Priority Preemptive**: No process in a lower-priority queue can run if there are any processes in a higher-priority queue. (Severe starvation risk for lower queues).
* **Time-Slice Partitioning**: Each queue gets a fixed fraction of total CPU time (e.g., 80% to Foreground RR queue, 20% to Background FCFS queue).

---

## 2. Multilevel Feedback Queue (MLFQ)
The limitation of basic MLQ is rigidity: processes are stuck in one queue forever. If an interactive process begins heavy calculation, or a batch process needs user input, MLQ cannot adapt.

**Multilevel Feedback Queue (MLFQ)** (introduced by Corbato in CTSS, 1962, and foundational to modern schedulers) allows processes to **move dynamically between queues** based on their demonstrated CPU burst behavior.

### The 5 Foundational Rules of MLFQ (OSTEP Framework):
* **Rule 1**: If $\text{Priority}(A) > \text{Priority}(B)$, process $A$ runs (process $B$ does not).
* **Rule 2**: If $\text{Priority}(A) = \text{Priority}(B)$, processes $A$ and $B$ run in Round Robin using the time quantum of that queue.
* **Rule 3**: When a new process enters the system, it is placed at the topmost (highest priority) queue.
* **Rule 4 (Accounting & Anti-Gaming)**: Once a job uses up its total time allotment at a given level (regardless of how many times it has voluntarily yielded the CPU), its priority is reduced (moves down one queue).
* **Rule 5 (Priority Boost / Aging)**: After some time period $S$, move all the jobs in the system to the topmost queue.

---

## 3. Key Design Mechanics in MLFQ

### A. Learning Process Behavior (Approximating SJF)
* Because every new job starts at the top queue (Rule 3), if it is a short interactive job, it completes quickly in the top queue with tiny response time (like SJF!).
* If it is a long-running CPU-bound batch job, it consumes its time slice, gets demoted to the next queue, consumes that slice, and drifts down to the lowest queue where it receives large time slices under FCFS/long-quantum RR.
* Thus, MLFQ **automatically approximates Shortest Job First without needing to predict future burst times**!

### B. Preventing Gaming of the Scheduler (Vulnerability of Simple MLFQ)
* In naive MLFQ: a process could execute for 99% of the quantum, issue an empty I/O write before the quantum expires, retain its high-priority queue position, and monopolize 99% of the CPU!
* **Rule 4 Solution**: The OS tracks the **cumulative time allotment** consumed at that queue level. Even if a process yields 100 times after 1 ms each, once its total CPU time at that level hits 10 ms, it is demoted!

### C. Preventing Starvation via Priority Boost (Rule 5)
* If many interactive jobs keep arriving, lower-level batch jobs will starve.
* After a global timer period $S$ (e.g. every 1 second), the OS performs a **Priority Boost**: all processes anywhere in the system are moved to the top queue.
* This ensures that long batch jobs make guaranteed forward progress, and if a batch job transitions into an interactive phase, it receives high responsiveness again!
