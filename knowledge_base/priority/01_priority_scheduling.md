# Priority Scheduling: Preemption, Inversion, and Mitigation

## 1. Principles of Priority Scheduling
In **Priority Scheduling**, each process is assigned an integer priority value, and the CPU is allocated to the ready process with the highest priority.

### Priority Conventions:
* **Lower Value = Higher Priority** (Standard in Unix, Linux, Silberschatz textbook):
  * Priority 0 is the highest priority; Priority 100 is low priority.
* **Higher Value = Higher Priority** (Used in Windows NT, macOS, real-time Mach kernel):
  * Priority 31 is real-time high priority; Priority 0 is idle thread.
* **SchedulAI Convention**: By default, SchedulAI follows the textbook convention where **smaller integer represents higher priority**.

---

## 2. Preemptive vs. Non-Preemptive Priority Scheduling
1. **Preemptive Priority**: When a process arrives with a priority strictly higher than the currently executing process, the CPU preempts the running process and dispatches the newcomer immediately.
2. **Non-Preemptive Priority**: The newly arrived high-priority process is placed at the head of the Ready Queue, but the currently running process is allowed to finish its CPU burst before yielding.

---

## 3. The Starvation Problem and Aging
* **Indefinite Blocking (Starvation)**: A major risk in priority scheduling is that low-priority processes may never execute if high-priority processes keep arriving continuously.
* Rumor from the MIT IBM 7094 shutdown (1973): When the system was finally turned off, a low-priority process submitted in 1967 was discovered still sitting in the queue waiting to run!

### Solution: Aging
**Aging** gradually increments the priority of processes that wait in the system for long periods.
* Formula example:
  $$\text{Priority}_{\text{effective}} = \text{Priority}_{\text{base}} - \lfloor \frac{\text{Wait Time}}{k} \rfloor$$
  *(Where lower integer = higher priority).*
* Over time, an aging low-priority process will reach priority 0 and run, guaranteeing progress.

---

## 4. Priority Inversion and the Mars Pathfinder Case Study
A classic and critical phenomenon in preemptive priority systems is **Priority Inversion**.

### The Scenario:
Imagine three tasks with priorities:
$$\text{High } (H) > \text{Medium } (M) > \text{Low } (L)$$
1. **Low ($L$)** acquires a shared mutually exclusive resource (e.g. Mutex lock $R$).
2. **High ($H$)** wakes up and preempts $L$. $H$ attempts to acquire Mutex $R$, but finds it locked. $H$ enters the blocked/waiting state.
3. Now, **Medium ($M$)** becomes runnable. $M$ does *not* need Mutex $R$. Because $M > L$, $M$ preempts $L$ and runs!
4. **The Inversion**: $H$ is now indirectly waiting for $M$! Because $M$ keeps running and preventing $L$ from finishing and unlocking $R$, the highest-priority task $H$ is starved by an unrelated medium-priority task $M$!

### Real-World Incident: Mars Pathfinder (July 1997)
On Mars, the Pathfinder rover began experiencing recurring system resets.
* An information bus mutex was held by a low-priority meteorological task.
* An urgent high-priority attitude control task attempted to acquire the mutex and blocked.
* A medium-priority communications task preempted the low-priority task for extended periods.
* The watchdog timer detected that the high-priority task had not executed, assumed a software crash, and reset the entire spacecraft computer!

### Solutions to Priority Inversion:
1. **Priority Inheritance Protocol (PIP)**:
   * When high-priority task $H$ blocks waiting for a lock held by low-priority task $L$, $L$ temporarily **inherits the high priority of $H$**!
   * Medium task $M$ cannot preempt $L$ because $L$ is temporarily running at priority $H$.
   * $L$ quickly finishes its critical section, releases lock $R$, returns to its normal low priority, and $H$ immediately runs.
2. **Priority Ceiling Protocol (PCP)**:
   * Each resource is assigned a priority ceiling equal to the highest priority task that can ever lock it.
   * Prevents chained blocking and guarantees deadlock-free execution.
