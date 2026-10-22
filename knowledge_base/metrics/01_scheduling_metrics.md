# CPU Scheduling Criteria and Performance Metrics

## Core Scheduling Metrics and Mathematical Definitions

When evaluating and comparing scheduling algorithms, operating system designers rely on standardized quantitative criteria:

### 1. Arrival Time (AT)
The exact point in system time at which a process enters the ready queue and becomes eligible for CPU scheduling ($AT \ge 0$).

### 2. Burst Time (BT)
The total duration of CPU execution time required by the process to complete its current computing phase ($BT > 0$).

### 3. Completion Time (CT)
The exact point in time at which the process finishes its final CPU instruction and terminates.

### 4. Turnaround Time (TAT)
The total elapsed interval from the moment the process arrives in the system until its completion:
$$\text{Turnaround Time} = \text{Completion Time} - \text{Arrival Time}$$
$$\text{TAT} = CT - AT$$
Turnaround time includes all time spent waiting in the ready queue, executing on the CPU, and performing I/O.

### 5. Waiting Time (WT)
The total amount of time a process spends sitting in the ready queue waiting to be allocated the CPU.
For a non-blocking process:
$$\text{Waiting Time} = \text{Turnaround Time} - \text{Burst Time}$$
$$\text{WT} = TAT - BT = (CT - AT) - BT$$
Important: Waiting time does not include time spent doing productive computation on the CPU or waiting for I/O devices.

### 6. Response Time (RT)
The elapsed time from process submission (Arrival Time) until the CPU produces its first response—i.e., when the process is allocated the CPU for the very first time:
$$\text{Response Time} = \text{First CPU Start Time} - \text{Arrival Time}$$
$$\text{RT} = \text{Start}_1 - AT$$
Response time is the paramount metric in interactive, time-sharing, and GUI environments where users expect prompt feedback.

### 7. CPU Utilization
The percentage of total elapsed time that the CPU is actively executing user or system processes rather than sitting idle:
$$\text{CPU Utilization} = \left(\frac{\text{Total Busy Time}}{\text{Total Elapsed Time}}\right) \times 100\%$$
In real systems, CPU utilization typically ranges from 40% (lightly loaded) to 90% (heavily loaded).

### 8. Throughput
The count of processes completed per unit of time:
$$\text{Throughput} = \frac{\text{Number of Completed Processes}}{\text{Total Elapsed Time}}$$

## Metric Optimization Goals
An optimal CPU scheduler seeks to:
- **Maximize**: CPU Utilization and Throughput.
- **Minimize**: Turnaround Time, Waiting Time, and Response Time.
In real-world systems, trade-offs must be made: minimizing response time (as in Round Robin) often increases turnaround time and context-switching overhead.

---

## 9. Advanced Scheduling Metrics & Fairness

### Response Time vs. Waiting Time in Preemptive Systems
* In **Non-Preemptive** algorithms (e.g. FCFS, non-preemptive SJF):
  $$\text{Response Time (RT)} \equiv \text{Waiting Time (WT)}$$
  Because a process never gets interrupted, the time it spends waiting for its first run is identical to its total waiting time!
* In **Preemptive** algorithms (e.g. Round Robin, SRTF, Preemptive Priority):
  $$\text{Response Time (RT)} \le \text{Waiting Time (WT)}$$
  The process receives an initial slice quickly (low RT), but is then preempted and waits in the Ready Queue between subsequent slices, causing total WT to grow larger than RT.

### Calculating Waiting Time across Multiple Preemption Slices
For a process executing across multiple disjoint intervals $[s_1, e_1], [s_2, e_2], \dots, [s_k, e_k]$:
$$\text{Waiting Time} = (s_1 - AT) + \sum_{j=2}^k (s_j - e_{j-1})$$
Or equivalently and much more simply:
$$\text{Waiting Time} = \text{Turnaround Time} - \text{Total Burst Time} = (CT - AT) - \sum \text{Burst}$$

### Jain's Fairness Index
To mathematically quantify fairness among $n$ processes receiving allocated throughput or execution ratios $x_1, x_2, \dots, x_n$:
$$\mathcal{J}(x_1, x_2, \dots, x_n) = \frac{\left(\sum_{i=1}^n x_i\right)^2}{n \sum_{i=1}^n x_i^2}$$
* Range: $\frac{1}{n} \le \mathcal{J} \le 1.0$.
* If all processes receive equal share ($x_i = c$), $\mathcal{J} = 1.0$ (100% perfectly fair).
* If 1 process monopolizes all resources and others receive 0, $\mathcal{J} = \frac{1}{n}$ (completely unfair).

