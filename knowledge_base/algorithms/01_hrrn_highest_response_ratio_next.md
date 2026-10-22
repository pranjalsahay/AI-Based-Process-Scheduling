# Highest Response Ratio Next (HRRN) Scheduling

## 1. Overview and Core Philosophy
**Highest Response Ratio Next (HRRN)** is a non-preemptive scheduling algorithm developed by Brinch Hansen to mitigate the severe starvation problem of Shortest Job First (SJF) while retaining its low average waiting time benefits.

In Shortest Job First, if short processes continuously arrive in the Ready Queue, a long-burst process can wait indefinitely (starvation). HRRN solves this dynamically by taking into account both:
1. The **service time** (CPU burst time) required by the process.
2. The **waiting time** the process has spent in the Ready Queue.

---

## 2. The Response Ratio Formula
Whenever the CPU becomes free, the scheduler calculates the **Response Ratio ($R$)** for every process currently waiting in the Ready Queue:

$$R = \frac{W + S}{S} = 1 + \frac{W}{S}$$

Where:
* $W$ = Waiting time of the process in the Ready Queue so far ($W = \text{Current Time} - \text{Arrival Time}$).
* $S$ = Expected CPU burst time (Service time).
* $R$ = Response Ratio (Priority factor).

The scheduler dispatches the process with the **highest Response Ratio ($R$)**.

---

## 3. Mathematical Analysis and Properties

### A. Favoring Short Jobs (SJF Characteristic)
* When processes have just arrived ($W \approx 0$), $R \approx 1$.
* If multiple processes have small waiting times, the process with the smallest service time $S$ has a significantly larger $\frac{W}{S}$ growth rate.
* Thus, shorter jobs naturally attain higher response ratios faster, ensuring low average waiting times similar to SJF.

### B. Starvation Prevention (Aging Characteristic)
* As a long process waits in the Ready Queue, its waiting time $W$ increases monotonically.
* As $W$ grows large, the numerator $(W + S)$ grows proportionally, increasing $R$.
* Even a job with a very large CPU burst $S$ will eventually achieve a higher Response Ratio than newly arrived short jobs, guaranteeing execution and completely eliminating starvation.

### C. Non-Preemptive Execution
* Once a process is selected, it runs to completion (or until it blocks for I/O).
* There is zero context switch overhead while a job is running.

---

## 4. Worked Step-by-Step Example

Consider 4 processes:
| Process | Arrival Time (AT) | Burst Time (BT) |
| :--- | :--- | :--- |
| **P1** | 0 ms | 3 ms |
| **P2** | 2 ms | 6 ms |
| **P3** | 4 ms | 4 ms |
| **P4** | 6 ms | 2 ms |

### Timeline:
1. **t = 0 ms**: Only **P1** is in the Ready Queue. P1 runs from $t = 0$ to $t = 3$ ms.
2. **t = 3 ms**: P1 completes. In the Ready Queue:
   * **P2**: $AT = 2$, $W = 3 - 2 = 1$ ms, $S = 6$ ms.
     $$R(P2) = \frac{1 + 6}{6} = \frac{7}{6} \approx 1.17$$
   * Only P2 is ready. **P2** runs from $t = 3$ to $t = 9$ ms.
3. **t = 9 ms**: P2 completes. Both P3 and P4 are waiting in the Ready Queue:
   * **P3**: $AT = 4$, $W = 9 - 4 = 5$ ms, $S = 4$ ms.
     $$R(P3) = \frac{5 + 4}{4} = \frac{9}{4} = 2.25$$
   * **P4**: $AT = 6$, $W = 9 - 6 = 3$ ms, $S = 2$ ms.
     $$R(P4) = \frac{3 + 2}{2} = \frac{5}{2} = 2.50$$
   * Since $R(P4) = 2.50 > R(P3) = 2.25$, **P4** is selected!
   * P4 runs from $t = 9$ to $t = 11$ ms.
4. **t = 11 ms**: P4 completes. Only **P3** is waiting.
   * P3 runs from $t = 11$ to $t = 15$ ms.

### Metrics Summary:
* **P1**: CT = 3, TAT = 3 - 0 = 3, WT = 3 - 3 = 0 ms
* **P2**: CT = 9, TAT = 9 - 2 = 7, WT = 7 - 6 = 1 ms
* **P4**: CT = 11, TAT = 11 - 6 = 5, WT = 5 - 2 = 3 ms
* **P3**: CT = 15, TAT = 15 - 4 = 11, WT = 11 - 4 = 7 ms
* **Average Turnaround Time**: $(3 + 7 + 5 + 11) / 4 = 6.50$ ms
* **Average Waiting Time**: $(0 + 1 + 3 + 7) / 4 = 2.75$ ms

---

## 5. Comparison with Other Algorithms
| Feature | FCFS | SJF | HRRN | Round Robin |
| :--- | :--- | :--- | :--- | :--- |
| **Preemptive?** | No | No | No | Yes |
| **Starvation Possible?** | No | Yes (long jobs) | **No (built-in aging)** | No |
| **Overhead** | Minimal | High (burst estimation) | High (ratio calculation on each schedule) | Moderate (context switches) |
| **Average Waiting Time**| High (convoy effect) | Mathematically minimal | Very close to SJF | Moderate |
