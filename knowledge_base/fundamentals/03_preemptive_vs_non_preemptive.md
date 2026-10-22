# Preemptive vs Non-Preemptive CPU Scheduling: Comprehensive Guide

## 1. Core Definitions and Fundamental Distinction

In Operating Systems, CPU scheduling policies are fundamentally divided into two major paradigms based on how the operating system manages running processes:

### Non-Preemptive Scheduling (Cooperative Scheduling)
* **Definition**: Once the CPU has been allocated to a process, that process keeps control of the CPU until it voluntarily yields it.
* **Release Conditions**: The process gives up the CPU only when:
  1. It terminates (finishes execution and exits).
  2. It explicitly transitions to the **Waiting (Blocked)** state (e.g., requesting an I/O operation, waiting for an IPC message, or invoking a blocking system call like `sleep()` or `wait()`).
* **Kernel Intervention**: The operating system kernel **never forcibly interrupts** or takes the CPU away from a running process during its CPU burst.
* **Standard Examples**: First-Come, First-Served (FCFS), standard Shortest Job First (non-preemptive SJF), and Non-Preemptive Priority scheduling.

### Preemptive Scheduling
* **Definition**: The operating system kernel retains the authority to interrupt and suspend a currently executing process before its CPU burst has completed, moving it back to the **Ready** state and allocating the CPU to another process.
* **Preemption Triggers**:
  1. **Hardware Timer Interrupt**: The hardware clock timer expires (e.g., in Round Robin when the process exhausts its allocated Time Quantum).
  2. **Higher-Priority Arrival**: A newly arrived process enters the Ready Queue with a strictly higher priority (in Preemptive Priority) or a strictly shorter remaining burst time (in Shortest Remaining Time First / SRTF).
  3. **I/O Completion Interrupt**: An external device completes an I/O request for a higher-priority process that was waiting, making it ready.
* **Standard Examples**: Round Robin (RR), Shortest Remaining Time First (SRTF / Preemptive SJF), and Preemptive Priority scheduling.

---

## 2. The Four Scheduling Decision Circumstances (Silberschatz Criteria)

A CPU scheduling decision may take place under four specific operating circumstances:

1. **Running $\to$ Waiting**: When a process initiates an I/O request or waits for an event.
   * *Classification*: **Non-preemptive**. The running process voluntarily gives up the CPU.
2. **Running $\to$ Ready**: When an interrupt occurs (e.g., hardware clock interrupt or system timer).
   * *Classification*: **Preemptive**. The OS forcibly removes the running process.
3. **Waiting $\to$ Ready**: When an asynchronous event completes (e.g., I/O finished for a process).
   * *Classification*: **Preemptive** (if the newly ready process preempts the currently executing one) or non-preemptive (if it simply joins the ready queue and waits).
4. **Terminates**: When a process completes its final instruction or calls `exit()`.
   * *Classification*: **Non-preemptive**. The process is finished.

> **Key Rule**: If scheduling occurs ONLY under circumstances 1 and 4, the scheduling scheme is strictly **Non-Preemptive**. If scheduling can also occur under circumstances 2 or 3, the scheduling scheme is **Preemptive**.

---

## 3. Detailed Architectural Comparison Table

| Feature / Dimension | Non-Preemptive (Cooperative) | Preemptive |
| :--- | :--- | :--- |
| **Control of CPU** | Process holds CPU until voluntary yield/exit | OS Kernel can revoke CPU at any moment |
| **Hardware Requirement** | Requires minimal hardware support | Requires hardware clock timer interrupt |
| **Response Time** | High / Poor (can vary widely depending on bursts) | Low / Excellent (ideal for interactive/real-time systems) |
| **Context Switch Overhead** | Low (switches occur only at natural boundaries) | High (frequent interrupts trigger state saves/restores) |
| **Shared Data Concurrency** | Simple; avoids race conditions on shared data | Complex; requires mutexes/locks to prevent race conditions |
| **Kernel Design Complexity** | Simple kernel design | Complex; kernel must be preemptive or use critical section locks |
| **Starvation Risk** | Possible in SJF/Priority, but absent in FCFS | High in SRTF/Priority without aging |
| **Throughput & Efficiency** | High throughput for batch workloads | Optimized for user responsiveness, slightly lower raw throughput |

---

## 4. Concurrency, Race Conditions, and Kernel Preemption

Preemptive scheduling introduces critical system design challenges:

1. **Shared Data Access in User Space**:
   * If Process A is in the middle of modifying a shared memory buffer and is preempted, and Process B is scheduled and reads or writes that same buffer, inconsistent state (race conditions) can occur.
   * **Solution**: Synchronization primitives (mutexes, semaphores, atomic operations).

2. **Kernel Preemption (Preemptive Kernel vs Non-Preemptive Kernel)**:
   * **Non-Preemptive Kernel**: A process running in kernel mode (servicing a system call) cannot be preempted until it exits kernel mode or blocks. This simplifies kernel design because kernel data structures are free of race conditions.
   * **Preemptive Kernel**: Allows a process running in kernel mode to be preempted by another kernel task. Essential for hard real-time systems to minimize dispatch latency.

---

## 5. Summary Worked Decision Example

Consider two processes:
* P1 arrives at $t = 0$ with Burst Time = 8 ms.
* P2 arrives at $t = 2$ with Burst Time = 2 ms.

* **Under Non-Preemptive Scheduling (e.g., FCFS or Non-preemptive SJF)**:
  * At $t = 2$, P2 arrives, but P1 is currently running.
  * P1 CANNOT be interrupted. P1 runs to completion at $t = 8$.
  * P2 must wait from $t = 2$ to $t = 8$ (Waiting Time = 6 ms).
* **Under Preemptive Scheduling (e.g., SRTF)**:
  * At $t = 2$, P1 has remaining burst $8 - 2 = 6$ ms.
  * P2 arrives with burst 2 ms ($2 < 6$).
  * The CPU Scheduler **preempts** P1, moves P1 back to Ready Queue, and dispatches P2.
  * P2 completes at $t = 4$. P2 Waiting Time = 0 ms!
