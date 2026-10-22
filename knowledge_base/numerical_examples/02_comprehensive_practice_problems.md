# Comprehensive Worked Practice Problems Across CPU Scheduling Algorithms

## Problem 1: Non-Preemptive SJF with Initial CPU Idle Period and Tie-Breaking

### Workload Specification:
| Process | Arrival Time (AT) | Burst Time (BT) |
| :--- | :--- | :--- |
| **P1** | 2 ms | 6 ms |
| **P2** | 3 ms | 2 ms |
| **P3** | 3 ms | 4 ms |
| **P4** | 5 ms | 2 ms |

### Chronological Execution Breakdown:
1. **$t = 0 \to 2$ ms**: Ready queue is empty! The CPU remains **IDLE** for 2 ms.
2. **$t = 2$ ms**: Only **P1** has arrived. Since the CPU is idle, P1 is dispatched immediately and runs non-preemptively from $t = 2$ to $t = 8$ ms.
3. **During P1's run**:
   - At $t=3$ ms, P2 (BT=2) and P3 (BT=4) arrive.
   - At $t=5$ ms, P4 (BT=2) arrives.
4. **$t = 8$ ms**: P1 completes. In the Ready Queue:
   - P2: BT = 2, AT = 3
   - P3: BT = 4, AT = 3
   - P4: BT = 2, AT = 5
   - *Tie-Breaking*: Both P2 and P4 have the minimum burst time (2 ms). By standard arrival-order tie-breaking, P2 arrived earlier ($t=3$ vs $t=5$), so **P2** is scheduled from $t = 8 \to 10$ ms.
5. **$t = 10$ ms**: P2 completes. Ready: P4 (BT=2), P3 (BT=4). **P4** runs from $t = 10 \to 12$ ms.
6. **$t = 12$ ms**: P4 completes. Only P3 remains. **P3** runs from $t = 12 \to 16$ ms.

### Gantt Chart:
`[IDLE: 0-2] [P1: 2-8] [P2: 8-10] [P4: 10-12] [P3: 12-16]`

### Metrics Table:
| Process | AT | BT | Completion Time (CT) | Turnaround Time (TAT = CT - AT) | Waiting Time (WT = TAT - BT) | Response Time (RT = First Run - AT) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P1** | 2 | 6 | 8 | $8 - 2 = 6$ | $6 - 6 = 0$ | $2 - 2 = 0$ |
| **P2** | 3 | 2 | 10 | $10 - 3 = 7$ | $7 - 2 = 5$ | $8 - 3 = 5$ |
| **P3** | 3 | 4 | 16 | $16 - 3 = 13$ | $13 - 4 = 9$ | $12 - 3 = 9$ |
| **P4** | 5 | 2 | 12 | $12 - 5 = 7$ | $7 - 2 = 5$ | $10 - 5 = 5$ |

### Performance Summary:
* Total Elapsed Time: 16 ms (CPU Busy: 14 ms, Idle: 2 ms)
* CPU Utilization: $\frac{14}{16} \times 100\% = 87.5\%$
* Average Turnaround Time (ATT): $\frac{6 + 7 + 13 + 7}{4} = \frac{33}{4} = 8.25$ ms
* Average Waiting Time (AWT): $\frac{0 + 5 + 9 + 5}{4} = \frac{19}{4} = 4.75$ ms
* Average Response Time (ART): $\frac{0 + 5 + 9 + 5}{4} = 4.75$ ms

---

## Problem 2: Round Robin ($q = 3$ ms) with Staggered Arrivals and Queue Trace

### Workload Specification:
| Process | Arrival Time (AT) | Burst Time (BT) |
| :--- | :--- | :--- |
| **P1** | 0 ms | 7 ms |
| **P2** | 2 ms | 4 ms |
| **P3** | 4 ms | 1 ms |
| **P4** | 5 ms | 4 ms |

### Ready Queue Trace (Quantum Boundary Rule: Newly arriving processes join BEFORE preempted process):
1. **$t = 0$ ms**: Ready Queue = `[P1]`. P1 starts executing with remaining burst 7.
2. **During P1's time slice ($t = 0 \to 3$ ms)**:
   - At $t = 2$ ms, P2 arrives.
3. **$t = 3$ ms**: P1 exhausts its 3 ms quantum. Remaining burst for P1 = $7 - 3 = 4$ ms.
   - Newly arrived process P2 is already in queue.
   - P1 is appended behind P2: Ready Queue = `[P2, P1]`.
   - **P2** executes.
4. **During P2's time slice ($t = 3 \to 6$ ms)**:
   - At $t = 4$ ms, P3 arrives.
   - At $t = 5$ ms, P4 arrives.
5. **$t = 6$ ms**: P2 exhausts 3 ms quantum (remaining = $4 - 3 = 1$ ms).
   - Incoming queue had P3 and P4. Preempted P2 is placed at tail: Ready Queue = `[P1, P3, P4, P2]`.
   - **P1** executes.
6. **$t = 6 \to 9$ ms**: P1 runs for 3 ms (remaining = $4 - 3 = 1$ ms).
   - Preempted P1 goes to tail: Ready Queue = `[P3, P4, P2, P1]`.
   - **P3** executes.
7. **$t = 9 \to 10$ ms**: P3 needs only 1 ms! Completes early at $t = 10$ ms.
   - Ready Queue = `[P4, P2, P1]`.
   - **P4** executes.
8. **$t = 10 \to 13$ ms**: P4 runs for 3 ms (remaining = $4 - 3 = 1$ ms).
   - Ready Queue = `[P2, P1, P4]`.
   - **P2** executes.
9. **$t = 13 \to 14$ ms**: P2 needs only 1 ms! Completes at $t = 14$ ms.
   - Ready Queue = `[P1, P4]`.
   - **P1** executes.
10. **$t = 14 \to 15$ ms**: P1 needs only 1 ms! Completes at $t = 15$ ms.
    - Ready Queue = `[P4]`.
    - **P4** executes.
11. **$t = 15 \to 16$ ms**: P4 finishes its last 1 ms and completes at $t = 16$ ms.

### Gantt Chart:
`[P1: 0-3] [P2: 3-6] [P1: 6-9] [P3: 9-10] [P4: 10-13] [P2: 13-14] [P1: 14-15] [P4: 15-16]`

### Metrics Table:
| Process | AT | BT | CT | TAT = CT - AT | WT = TAT - BT | RT = First Run - AT |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P1** | 0 | 7 | 15 | $15 - 0 = 15$ | $15 - 7 = 8$ | $0 - 0 = 0$ |
| **P2** | 2 | 4 | 14 | $14 - 2 = 12$ | $12 - 4 = 8$ | $3 - 2 = 1$ |
| **P3** | 4 | 1 | 10 | $10 - 4 = 6$ | $6 - 1 = 5$ | $9 - 4 = 5$ |
| **P4** | 5 | 4 | 16 | $16 - 5 = 11$ | $11 - 4 = 7$ | $10 - 5 = 5$ |

### Performance Summary:
* Average Turnaround Time: $\frac{15 + 12 + 6 + 11}{4} = \frac{44}{4} = 11.0$ ms
* Average Waiting Time: $\frac{8 + 8 + 5 + 7}{4} = \frac{28}{4} = 7.0$ ms
* Average Response Time: $\frac{0 + 1 + 5 + 5}{4} = \frac{11}{4} = 2.75$ ms

---

## Problem 3: Preemptive Priority Scheduling with Aging

### Priority Convention: Lower number = Higher priority.
Workload:
* **P1**: AT = 0, BT = 10, Initial Priority = 4
* **P2**: AT = 2, BT = 3, Initial Priority = 2
* **Aging Rule**: For every 3 ms a process spends waiting in the ready queue without CPU execution, its priority improves by 1 (e.g. priority drops from 4 to 3).

### Execution Timeline:
1. **$t = 0 \to 2$ ms**: P1 begins executing (P1 priority = 4). Remaining burst = 8 ms.
2. **$t = 2$ ms**: P2 arrives with Priority = 2 ($2 < 4$). P2 has higher urgency and **preempts P1**!
   - P1 placed in Ready Queue at $t=2$ ms with Priority = 4, remaining burst = 8 ms.
3. **$t = 2 \to 5$ ms**: P2 executes for 3 ms and completes at $t = 5$ ms.
4. **$t = 5$ ms**: P1 has been waiting in the queue from $t=2$ to $t=5$ ms ($3$ ms total).
   - By the Aging Rule, P1's priority improves from 4 to 3!
   - P1 resumes and runs from $t = 5 \to 13$ ms, completing at $t = 13$ ms.

### Metrics Table:
* **P1**: CT = 13, TAT = 13, WT = $13 - 10 = 3$ ms, RT = 0 ms
* **P2**: CT = 5, TAT = $5 - 2 = 3$ ms, WT = $3 - 3 = 0$ ms, RT = $2 - 2 = 0$ ms
* Average Waiting Time: $\frac{3 + 0}{2} = 1.5$ ms
* Average Turnaround Time: $\frac{13 + 3}{2} = 8.0$ ms

---

## Problem 4: Real-Time RMS vs. EDF Comparison

### Task Set:
* $\tau_1$: Execution Time $C_1 = 1$ ms, Period $T_1 = 3$ ms ($U_1 = 1/3 \approx 0.333$)
* $\tau_2$: Execution Time $C_2 = 2$ ms, Period $T_2 = 4$ ms ($U_2 = 2/4 = 0.500$)
* Total Utilization: $U = 0.333 + 0.500 = 0.833$ (83.3%)
* Hyperperiod $H = \text{lcm}(3, 4) = 12$ ms.

### Rate Monotonic Scheduling (RMS):
* Static Priority: $T_1 = 3 < T_2 = 4 \implies \text{Priority}(\tau_1) > \text{Priority}(\tau_2)$.
* **Liu & Layland Bound for $n=2$**:
  $$U_{bound} = 2(2^{1/2} - 1) = 2(1.414 - 1) = 0.828 \text{ (82.8\%)}$$
  *Notice that $U = 0.833 > 0.828$, so RMS schedulability is NOT guaranteed by the utilization bound!*
* **Response-Time Analysis (RTA) for $\tau_2$**:
  - $R_2^{(0)} = C_2 = 2$
  - $R_2^{(1)} = C_2 + \lceil R_2^{(0)} / T_1 \rceil C_1 = 2 + \lceil 2 / 3 \rceil \times 1 = 2 + 1 = 3$
  - $R_2^{(2)} = 2 + \lceil 3 / 3 \rceil \times 1 = 2 + 1 = 3$ (Converged at $R_2 = 3$ ms $\le D_2 = 4$ ms!)
  - *Conclusion: Despite exceeding the Liu & Layland bound, the task set is schedulable under RMS!*

### Earliest Deadline First (EDF):
* Total Utilization: $U = 0.833 \le 1.0$.
* *Because $U \le 1.0$, the task set is guaranteed to meet 100% of its deadlines under dynamic EDF!*
