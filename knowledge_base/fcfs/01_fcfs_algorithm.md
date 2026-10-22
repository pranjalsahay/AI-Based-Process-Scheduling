# First-Come, First-Served (FCFS) Scheduling: Comprehensive Theory & Analysis

## 1. Algorithmic Principle and Queue Architecture
**First-Come, First-Served (FCFS)** (also known as FIFO - First-In, First-Out) is the most fundamental CPU scheduling algorithm.
* **Mechanism**: Processes are dispatched strictly in the chronological order of their arrival into the Ready Queue.
* **Queue Data Structure**: Managed via a standard FIFO queue of Process Control Blocks (PCBs). Arriving processes are appended to the queue tail (`enqueue`), and the scheduler dispatches from the queue head (`dequeue`).
* **Non-Preemptive Nature**: Once a process obtains the CPU, it runs uninterrupted until it either:
  1. Terminates (calls `exit()`).
  2. Blocks voluntarily for an I/O operation or system event (moves to the Waiting/Blocked state).
* **Context Switch Minimization**: FCFS produces the minimum possible number of context switches ($N$ context switches for $N$ CPU-bound jobs), as no job is ever preempted mid-burst.

---

## 2. Mathematical Performance and Convoy Effect Analysis

### A. Waiting Time Sensitivity to Arrival Permutations
The average waiting time under FCFS is notoriously sensitive to the permutation of process arrivals.

#### Case 1 (Long Process First):
Processes P1 (Burst 24 ms), P2 (Burst 3 ms), P3 (Burst 3 ms) all arrive at $t=0$ in order $[P1, P2, P3]$:
* P1 runs: $t = 0 \to 24$ ms (Waiting Time = 0 ms).
* P2 runs: $t = 24 \to 27$ ms (Waiting Time = 24 ms).
* P3 runs: $t = 27 \to 30$ ms (Waiting Time = 27 ms).
* **Average Waiting Time (AWT)**:
  $$\text{AWT} = \frac{0 + 24 + 27}{3} = \frac{51}{3} = 17.0\text{ ms}$$

#### Case 2 (Short Processes First):
If the same processes arrive in order $[P2, P3, P1]$:
* P2 runs: $t = 0 \to 3$ ms (Waiting Time = 0 ms).
* P3 runs: $t = 3 \to 6$ ms (Waiting Time = 3 ms).
* P1 runs: $t = 6 \to 30$ ms (Waiting Time = 6 ms).
* **Average Waiting Time (AWT)**:
  $$\text{AWT} = \frac{0 + 3 + 6}{3} = \frac{9}{3} = 3.0\text{ ms}$$

**Conclusion**: The exact same workload experiences a **5.67x reduction** in average waiting time simply by changing the arrival sequence!

### B. The Convoy Effect Mechanism
The **Convoy Effect** occurs when a long CPU-bound process holds the CPU while numerous short, I/O-bound processes wait behind it in the Ready Queue:
1. The CPU-bound process executes for a long duration.
2. During this time, all I/O-bound processes queue up in the Ready Queue. Their corresponding I/O devices (disks, network interfaces) sit completely **idle**.
3. When the CPU-bound process finally blocks for I/O, all short I/O-bound processes execute quickly in succession and immediately issue I/O requests.
4. Now, the **CPU sits idle** while all I/O devices are saturated!
5. The CPU-bound process finishes its I/O and returns to monopolize the CPU, restarting the convoy cycle.
* **Impact**: Drastically reduced overall system throughput and suboptimal hardware resource utilization across both CPU and I/O subsystems.

---

## 3. Starvation and Fairness Characteristics
* **Starvation-Free**: FCFS is provably starvation-free for finite processes. Because arrival times form a strictly monotonic sequence, every process eventually reaches the front of the queue.
* **Fairness**: Strictly fair in chronological order, but unfair in terms of proportional execution time (short jobs wait disproportionately long compared to their burst lengths).

---

## 4. Edge Cases in Implementation
1. **CPU Idle Periods**: If process $P_i$ completes at time $t_1$, but the next process $P_{i+1}$ does not arrive until $t_2 > t_1$, the CPU must enter the **Idle state** from $t_1$ to $t_2$. Waiting time calculations must not accumulate idle gaps as process waiting time.
2. **Arrival Time Ties**: If two processes arrive at the exact same millisecond ($AT_1 = AT_2$), ties are broken deterministically by Process ID (e.g. lowest PID first) or insertion order in the kernel table.
3. **Zero Burst Time**: A process with burst time 0 (e.g. immediate abort) completes instantly at its arrival time with $TAT = 0$ and $WT = 0$.
