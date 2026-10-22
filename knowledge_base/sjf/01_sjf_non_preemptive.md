# Shortest Job First (SJF) Non-Preemptive Scheduling: In-Depth Reference

## 1. Algorithmic Principle
**Shortest Job First (SJF)** (also known as Shortest Process Next - SPN) selects the process with the smallest CPU burst time from the Ready Queue whenever the CPU becomes available.

### Operating Characteristics:
1. **Non-Preemptive Execution**: Once a process is dispatched, it runs to completion (or until it blocks for I/O). Arriving shorter processes cannot interrupt it.
2. **Tie-Breaking Rule**: If multiple processes in the Ready Queue share the identical burst time, ties are broken by **earliest arrival time (FCFS)**, followed by process ID (PID).

---

## 2. Mathematical Proof of Optimality
SJF is mathematically **optimal** for minimizing average waiting time for a set of stationary processes arriving simultaneously.

### The Proof (Rearrangement Inequality / Exchange Argument):
Consider $n$ processes with burst times $p_1, p_2, \dots, p_n$ arriving at $t=0$.
Under any non-preemptive schedule, the waiting time for the $k$-th executed process is:
$$W_k = \sum_{j=1}^{k-1} p_j$$
The total waiting time across all $n$ processes is:
$$\text{Total WT} = \sum_{k=1}^n W_k = (n - 1)p_1 + (n - 2)p_2 + \dots + 1 \cdot p_{n-1} + 0 \cdot p_n$$
Notice that the burst time of the first process ($p_1$) is multiplied by $(n - 1)$, the second by $(n - 2)$, and the last process contributes 0 to the waiting time of others.
* To minimize the sum $\sum_{k=1}^n (n - k)p_k$, by the **Rearrangement Inequality**, the largest coefficients $(n - 1, n - 2, \dots)$ must be paired with the smallest values of $p_k$.
* Therefore:
  $$p_1 \le p_2 \le p_3 \le \dots \le p_n$$
* Any inversion where a longer job runs before a shorter job strictly increases total waiting time. Thus, **SJF yields the provable minimum average waiting time**.

---

## 3. Estimating Future CPU Bursts: Exponential Smoothing
In real operating systems, future CPU burst lengths cannot be known with certainty. The kernel predicts the next burst $\tau_{n+1}$ using **Exponential Smoothing (Exponential Average)** of historical measurements:

$$\tau_{n+1} = \alpha t_n + (1 - \alpha)\tau_n$$

Where:
* $t_n$ = Actual length of the $n$-th CPU burst just completed.
* $\tau_n$ = Predicted value for the $n$-th CPU burst.
* $\tau_{n+1}$ = Predicted value for the upcoming $(n+1)$-th CPU burst.
* $\alpha \in [0, 1]$ = Smoothing weight parameter (commonly chosen as $\alpha = 0.5$).

### Expansion into Historical Geometric Series:
By recursively expanding the formula:
$$\tau_{n+1} = \alpha t_n + (1 - \alpha)\alpha t_{n-1} + (1 - \alpha)^2\alpha t_{n-2} + \dots + (1 - \alpha)^j\alpha t_{n-j} + (1 - \alpha)^{n+1}\tau_0$$
* Because $(1 - \alpha) < 1$, older bursts have exponentially decaying weights.
* **If $\alpha = 0$**: $\tau_{n+1} = \tau_0$. Recent history is ignored; the initial belief persists.
* **If $\alpha = 1$**: $\tau_{n+1} = t_n$. Only the most recent burst matters; older history is discarded.
* **If $\alpha = 0.5$**: Equal weighting between the most recent burst and the cumulative historical average.

---

## 4. Starvation and Remediation via Aging
### The Starvation Hazard:
* If short jobs arrive continuously at a rate higher than the service rate, the Ready Queue always contains short jobs.
* Long-burst processes are postponed indefinitely (**Starvation** or **Indefinite Blocking**).
* In extreme cases, a long process may never receive CPU time.

### Remediation via Aging:
* **Aging** gradually increases the effective priority of a process the longer it waits in the Ready Queue.
* In SJF adaptations (like HRRN), the priority metric incorporates waiting time:
  $$\text{Effective Burst} = \text{Actual Burst} - k \cdot W$$
  Eventually, even a process requiring a 1000 ms burst will look "shorter" than newly arrived 2 ms bursts, ensuring it executes.
