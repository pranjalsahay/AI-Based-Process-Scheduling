# Real-Time CPU Scheduling: RMS and EDF

## 1. Fundamentals of Real-Time Systems
A **Real-Time Operating System (RTOS)** must guarantee not only logical correctness of calculations, but also **temporal correctness**—completing tasks within strict **deadlines**.

### Real-Time Classifications:
1. **Hard Real-Time**: Missing a single deadline leads to catastrophic system failure (e.g., automotive braking, aircraft flight control, cardiac pacemakers).
2. **Soft Real-Time**: Deadlines are important, but missing an occasional deadline only degrades Quality of Service (QoS) without catastrophic harm (e.g., video streaming, audio playback, online gaming).

---

## 2. The Periodic Task Model
In real-time systems, tasks are typically periodic:
* $C_i$ = Worst-Case Execution Time (WCET) or computation time.
* $T_i$ = Period of task $i$ (time interval between successive release events).
* $D_i$ = Relative deadline (frequently assumed $D_i = T_i$, implicit deadline model).
* $U_i = \frac{C_i}{T_i}$ = CPU Utilization contributed by task $i$.
* **Total System Utilization**:
  $$U = \sum_{i=1}^n \frac{C_i}{T_i}$$

If $U > 1.0$ (100%), no single-core CPU scheduler can schedule all tasks without missing deadlines.

---

## 3. Rate Monotonic Scheduling (RMS)
**Rate Monotonic Scheduling (RMS)** is the optimal **static (fixed) priority** algorithm for periodic real-time tasks with implicit deadlines ($D_i = T_i$).

### Priority Assignment Rule:
$$\text{Shorter Period } (T_i) \implies \text{Higher Priority}$$
* The task that executes most frequently (highest rate $1/T_i$) is assigned the highest static priority.
* Tasks are strictly preemptive: if a shorter-period task releases, it interrupts any longer-period task.

### Schedulability Test: Liu & Layland Bound
Liu and Layland (1973) proved that a set of $n$ independent periodic tasks is **guaranteed to be schedulable** under RMS if:

$$U = \sum_{i=1}^n \frac{C_i}{T_i} \le n(2^{1/n} - 1)$$

| Number of Tasks ($n$) | Utilization Bound $n(2^{1/n} - 1)$ |
| :--- | :--- |
| **1** | $1.000$ (100.0%) |
| **2** | $2(\sqrt{2} - 1) \approx 0.828$ (82.8%) |
| **3** | $3(2^{1/3} - 1) \approx 0.780$ (78.0%) |
| **5** | $\approx 0.743$ (74.3%) |
| $\mathbf{n \to \infty}$ | $\mathbf{\ln 2 \approx 0.693}$ (69.3%) |

#### Practical Rule of Thumb:
* If $U \le \ln 2 \approx 69.3\%$, the task set is **always schedulable** under RMS.
* If $69.3\% < U \le 100\%$, it *may* be schedulable (requires Exact Response-Time Analysis / Time-Demand Analysis $W_i(t) = C_i + \sum_{j \in hp(i)} \lceil \frac{t}{T_j} \rceil C_j$).
* If $U > 100\%$, it is never schedulable.

---

## 4. Earliest Deadline First (EDF)
**Earliest Deadline First (EDF)** is an optimal **dynamic priority** scheduling algorithm.

### Priority Assignment Rule:
$$\text{Closest Absolute Deadline } (d_{i,k}) \implies \text{Highest Priority}$$
* Absolute deadline for instance $k$ arriving at $r_{i,k}$: $d_{i,k} = r_{i,k} + D_i$.
* As time moves forward, task priorities are recalculated dynamically based on remaining time until the next deadline.
* When a task with a nearer absolute deadline becomes ready, it immediately preempts the running task.

### Schedulability Test for EDF:
For periodic tasks with $D_i = T_i$, a task set is schedulable under EDF **if and only if**:

$$U = \sum_{i=1}^n \frac{C_i}{T_i} \le 1.0 \quad (100\%)$$

Unlike RMS (capped at ~69.3%), EDF can theoretically achieve **100% CPU utilization** without missing any deadlines!

---

## 5. Comparative Evaluation: RMS vs. EDF
| Criteria | Rate Monotonic (RMS) | Earliest Deadline First (EDF) |
| :--- | :--- | :--- |
| **Priority Assignment** | Static (fixed at design time) | Dynamic (changes at runtime) |
| **Maximum Guaranteed Utilization** | $n(2^{1/n} - 1) \to \ln 2 \approx 69.3\%$ | **$100\%$ ($U \le 1.0$)** |
| **Implementation Complexity** | Simple, very low OS overhead | Moderate, requires priority re-sorting |
| **Behavior under Overload ($U > 1$)** | Predictable: lower-priority tasks miss deadlines, highest-priority tasks survive | Unpredictable: cascading "domino effect" where many tasks can fail |
| **Commercial Adoption** | Widely used in avionics, automotive (AUTOSAR) | Used when CPU resources must be maximized |
