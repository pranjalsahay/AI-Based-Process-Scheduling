# Linux Completely Fair Scheduler (CFS)

## 1. Introduction and Philosophy
The **Completely Fair Scheduler (CFS)** is the default CPU scheduling algorithm for normal (non-real-time) tasks in the Linux kernel since version 2.6.23 (developed by Ingo Molnar).

Unlike classic multi-level feedback queues or priority-slice schedulers, CFS models an **"Ideal Multi-tasking CPU"** on actual hardware:
* In an ideal system with $N$ runnable tasks, each task would receive $1/N$ of the CPU's power continuously and simultaneously (pure processor sharing).
* On real hardware with a single CPU, only one task can execute at any instant. CFS achieves fairness by tracking how much execution time each task has had and running the task that has received the least CPU time.

---

## 2. Virtual Runtime (`vruntime`)
The cornerstone metric of CFS is **Virtual Runtime (`vruntime`)**.
* `vruntime` measures the normalized execution time that a process has consumed on the CPU, scaled by its priority (nice level).
* In nanoseconds: when a process executes for real physical time $\Delta \text{exec}$, its `vruntime` increases as:

$$\Delta \text{vruntime} = \Delta \text{exec} \times \frac{\text{NICE\_0\_LOAD}}{\text{weight}}$$

Where:
* `NICE_0_LOAD` = $1024$ (the baseline weight corresponding to nice value 0).
* `weight` = the assigned weight of the process based on its nice value.

### Key Insights:
1. **Nice 0 Process**: $\text{weight} = 1024$. Here, $\Delta \text{vruntime} = \Delta \text{exec} \times \frac{1024}{1024} = \Delta \text{exec}$. Virtual time progresses at 1:1 real time.
2. **High-Priority Process (Negative Nice, e.g. nice = -5)**: $\text{weight} > 1024$. Here, $\frac{\text{NICE\_0\_LOAD}}{\text{weight}} < 1$. Virtual time accumulates **slower** than real time, allowing it to run longer before its `vruntime` catches up.
3. **Low-Priority Process (Positive Nice, e.g. nice = +5)**: $\text{weight} < 1024$. Virtual time accumulates **faster** than real time, causing it to yield the CPU sooner.

---

## 3. Data Structure: The Time-Ordered Red-Black Tree
Instead of maintaining traditional FIFO runqueues per priority level:
* CFS stores all runnable processes in a **Red-Black Tree (`struct rb_root_cached`)**, a self-balancing binary search tree.
* **Key**: The tree is keyed by `vruntime`.
* **Selection ($O(1)$)**: The process with the smallest `vruntime` is located at the leftmost node of the tree (`rb_leftmost`). CFS always selects the leftmost node to execute next.
* **Insertion & Deletion ($O(\log N)$)**: When a process completes its time slice or blocks, its new `vruntime` is computed, and it is re-inserted into the tree in $O(\log N)$ time.

---

## 4. Latency Target and Granularity
Rather than fixing a rigid time slice (like Round Robin's 100 ms):
* CFS dynamically calculates each task's slice based on a configurable **Scheduling Latency (`sysctl_sched_latency`)**, typically 6 to 24 milliseconds.
* The time slice $\tau_i$ allocated to process $i$ within period $T$ is:

$$\tau_i = \text{sched\_latency} \times \frac{\text{weight}_i}{\sum_{j=1}^N \text{weight}_j}$$

### Protection Against Thrashing:
* If $N$ becomes huge, $\tau_i$ could become microscopically small, causing context-switch overhead to dominate.
* CFS enforces a lower bound called **Minimum Granularity (`sysctl_sched_min_granularity`)**, typically 0.75 ms to 1.5 ms.
* If $N \times \text{min\_granularity} > \text{sched\_latency}$, the period expands dynamically to $N \times \text{min\_granularity}$.

---

## 5. Nice Values and Weights
Linux supports 40 nice levels from $-20$ (highest priority) to $+19$ (lowest priority). Each step represents approximately a **10% CPU allocation difference**:
```c
const int prio_to_weight[40] = {
    /* -20 */ 88761,  71755,  56483,  46273,  36291,
    /* -15 */ 29154,  23254,  18705,  14949,  11916,
    /* -10 */  9548,   7620,   6100,   4904,   3906,
    /*  -5 */  3121,   2501,   1991,   1586,   1277,
    /*   0 */  1024,    820,    655,    526,    423,
    /*   5 */   335,    272,    215,    172,    137,
    /*  10 */   110,     87,     70,     56,     45,
    /*  15 */    36,     29,     23,     18,     15,
};
```
Each decrease in nice level increases weight by roughly a factor of $1.25$ ($\approx 5/4$), which guarantees that a process with 1 nice level higher gets roughly 10% more CPU time relative to its peer.

---

## 6. Sleeping and Waking Processes (Fairness Compensation)
* If a process sleeps (e.g., waiting for user keystrokes) for 10 seconds, its real-world `vruntime` would freeze while other tasks advance by 10,000,000,000 ns.
* If it simply woke up with its old `vruntime`, it would starve every other process in the system for 10 full seconds!
* **CFS Solution**: When a sleeping task wakes up, its `vruntime` is reset to:
  $$\text{vruntime}_{\text{wake}} = \max(\text{vruntime}_{\text{old}}, \text{min\_vruntime} - \Delta_{\text{latency}})$$
  Where `min_vruntime` is the minimum `vruntime` among all runnable tasks in the queue. This prevents starvation while still giving interactive jobs an immediate responsiveness boost!
