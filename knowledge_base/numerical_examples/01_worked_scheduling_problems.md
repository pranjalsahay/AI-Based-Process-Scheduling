# Worked CPU Scheduling Numerical Problems and Step-by-Step Solutions

## Problem 1: FCFS with Staggered Arrivals
Given four processes:
- P1: Arrival Time = 0, Burst Time = 5
- P2: Arrival Time = 1, Burst Time = 3
- P3: Arrival Time = 2, Burst Time = 8
- P4: Arrival Time = 3, Burst Time = 6

### Execution Timeline (Gantt Chart):
`[P1: 0-5] [P2: 5-8] [P3: 8-16] [P4: 16-22]`

### Calculations:
- **P1**: CT = 5, TAT = 5 - 0 = 5, WT = 5 - 5 = 0, RT = 0 - 0 = 0
- **P2**: CT = 8, TAT = 8 - 1 = 7, WT = 7 - 3 = 4, RT = 5 - 1 = 4
- **P3**: CT = 16, TAT = 16 - 2 = 14, WT = 14 - 8 = 6, RT = 8 - 2 = 6
- **P4**: CT = 22, TAT = 22 - 3 = 19, WT = 19 - 6 = 13, RT = 16 - 3 = 13

### Averages:
- Average Turnaround Time: $(5 + 7 + 14 + 19) / 4 = 45 / 4 = 11.25$
- Average Waiting Time: $(0 + 4 + 6 + 13) / 4 = 23 / 4 = 5.75$
- Average Response Time: $(0 + 4 + 6 + 13) / 4 = 5.75$

---

## Problem 2: SRTF Preemptive with Staggered Arrivals
Given processes:
- P1: Arrival Time = 0, Burst Time = 8
- P2: Arrival Time = 1, Burst Time = 4
- P3: Arrival Time = 2, Burst Time = 9
- P4: Arrival Time = 3, Burst Time = 5

### Execution Steps:
1. $t=0$: P1 starts. At $t=1$, P1 has 7 remaining. P2 arrives with burst 4 ($4 < 7$). Preempt P1!
2. $t=1$: P2 starts. At $t=2$, P3 arrives (burst 9; P2 has 3 left). P2 continues.
3. $t=3$: P4 arrives (burst 5; P2 has 2 left). P2 continues.
4. $t=5$: P2 completes. Ready: P1 (rem 7), P3 (rem 9), P4 (rem 5). Shortest is P4.
5. $t=5-10$: P4 executes to completion.
6. $t=10-17$: P1 executes its remaining 7 units and completes.
7. $t=17-26$: P3 executes to completion.

### Gantt Chart:
`[P1: 0-1] [P2: 1-5] [P4: 5-10] [P1: 10-17] [P3: 17-26]`

### Calculations:
- **P1**: CT = 17, TAT = 17 - 0 = 17, WT = 17 - 8 = 9, RT = 0 - 0 = 0
- **P2**: CT = 5, TAT = 5 - 1 = 4, WT = 4 - 4 = 0, RT = 1 - 1 = 0
- **P3**: CT = 26, TAT = 26 - 2 = 24, WT = 24 - 9 = 15, RT = 17 - 2 = 15
- **P4**: CT = 10, TAT = 10 - 3 = 7, WT = 7 - 5 = 2, RT = 5 - 3 = 2

### Averages:
- Average Turnaround Time: $(17 + 4 + 24 + 7) / 4 = 52 / 4 = 13.0$
- Average Waiting Time: $(9 + 0 + 15 + 2) / 4 = 26 / 4 = 6.5$
- Average Response Time: $(0 + 0 + 15 + 2) / 4 = 17 / 4 = 4.25$
