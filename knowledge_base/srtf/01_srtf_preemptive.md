# Shortest Remaining Time First (SRTF) Preemptive Scheduling

## 1. Algorithmic Principle and Mechanics
**Shortest Remaining Time First (SRTF)** (also known as Preemptive SJF) is the preemptive counterpart of Shortest Job First.

### The Decision Rule:
Whenever a new process arrives in the Ready Queue at time $t$:
1. The scheduler compares the burst time of the newly arrived process ($BT_{\text{new}}$) with the **remaining CPU execution time** of the currently running process ($RT_{\text{current}}$).
2. **Preemption Condition**:
   $$\text{If } BT_{\text{new}} < RT_{\text{current}} \implies \text{Preempt running process!}$$
   * The currently running process is interrupted, its state (registers, program counter) is saved into its PCB, and it is placed back into the Ready Queue.
   * The newly arrived process is dispatched immediately.
3. **Equal Remaining Time (No Preemption on Tie)**:
   $$\text{If } BT_{\text{new}} = RT_{\text{current}} \implies \text{Running process continues!}$$
   * To prevent unnecessary and wasteful context switching, a tie in remaining time does **not** trigger preemption. The currently running job retains the CPU.

---

## 2. Dynamic Event-Driven Scheduling
In SRTF, scheduling decisions occur at two distinct types of events:
1. **Process Completion**: The running process finishes its burst. The scheduler selects the process in the Ready Queue with the shortest remaining time.
2. **Process Arrival**: A new process arrives while another is executing. A preemption evaluation is triggered immediately.

---

## 3. Worked Step-by-Step Example

Consider 4 processes:
| Process | Arrival Time (AT) | Burst Time (BT) |
| :--- | :--- | :--- |
| **P1** | 0 ms | 8 ms |
| **P2** | 1 ms | 4 ms |
| **P3** | 2 ms | 9 ms |
| **P4** | 3 ms | 5 ms |

### Chronological Execution:
* **t = 0 ms**: Only **P1** is ready. P1 begins executing.
* **t = 1 ms**: **P2** arrives with burst 4 ms. P1 has remaining time $8 - 1 = 7$ ms.
  * Since $BT(P2) = 4 < RT(P1) = 7$, **P1 is preempted**!
  * Ready Queue: P1 (rem: 7).
  * **P2** begins executing.
* **t = 2 ms**: **P3** arrives with burst 9 ms. P2 has remaining time $4 - 1 = 3$ ms.
  * $BT(P3) = 9 > RT(P2) = 3$. No preemption. P2 continues.
  * Ready Queue: P1 (rem: 7), P3 (rem: 9).
* **t = 3 ms**: **P4** arrives with burst 5 ms. P2 has remaining time $3 - 1 = 2$ ms.
  * $BT(P4) = 5 > RT(P2) = 2$. No preemption. P2 continues.
  * Ready Queue: P1 (rem: 7), P4 (rem: 5), P3 (rem: 9).
* **t = 5 ms**: **P2 completes**!
  * Ready Queue remaining times: P4 (5 ms), P1 (7 ms), P3 (9 ms).
  * Minimum is **P4** (5 ms). **P4 runs** from $t = 5$ to $t = 10$ ms.
* **t = 10 ms**: **P4 completes**!
  * Ready Queue remaining times: P1 (7 ms), P3 (9 ms).
  * Minimum is **P1** (7 ms). **P1 resumes** from $t = 10$ to $t = 17$ ms.
* **t = 17 ms**: **P1 completes**!
  * Only **P3** remains. **P3 runs** from $t = 17$ to $t = 26$ ms.
* **t = 26 ms**: All processes completed.

### Gantt Chart:
```text
[0-1]: P1 | [1-5]: P2 | [5-10]: P4 | [10-17]: P1 | [17-26]: P3
0         1           5            10            17            26
```

### Metrics:
* **P1**: CT = 17, TAT = 17 - 0 = 17 ms, WT = 17 - 8 = 9 ms
* **P2**: CT = 5, TAT = 5 - 1 = 4 ms, WT = 4 - 4 = 0 ms
* **P3**: CT = 26, TAT = 26 - 2 = 24 ms, WT = 24 - 9 = 15 ms
* **P4**: CT = 10, TAT = 10 - 3 = 7 ms, WT = 7 - 5 = 2 ms
* **Average Turnaround Time**: $(17 + 4 + 24 + 7) / 4 = 13.00$ ms
* **Average Waiting Time**: $(9 + 0 + 15 + 2) / 4 = 6.50$ ms

---

## 4. Overhead and Trade-offs
1. **Context Switching Overhead**: Preempting running processes incurs register saves, cache misses, and pipeline flushes. If bursts are short, frequent preemption can significantly reduce net CPU throughput.
2. **Severe Starvation**: Long jobs suffer even worse starvation under SRTF than under non-preemptive SJF, because an ongoing long job can be repeatedly interrupted whenever any short burst arrives.
