# Multi-Processor and Thread Scheduling

## 1. Multi-Processor Architectures
When multiple physical CPU cores are available, CPU scheduling becomes significantly more complex than single-core scheduling.

### Architectures:
1. **Asymmetric Multiprocessing (AMP)**:
   * A single "master" CPU handles all scheduling decisions, I/O processing, and system tasks.
   * "Worker" cores only execute user code directed by the master.
   * Simple, but the master CPU becomes a severe performance bottleneck.
2. **Symmetric Multiprocessing (SMP)**:
   * Each processor is self-scheduling.
   * All processors can execute in kernel mode simultaneously.
   * Modern operating systems (Linux, Windows, macOS) all employ SMP.

---

## 2. Queue Architectures in SMP

### A. Single Global Queue (SQMS - Single-Queue Multiprocessor Scheduling)
* All runnable processes reside in a single shared ready queue.
* Whenever any CPU core becomes idle, it locks the queue, picks the next process, and unlocks the queue.
* **Drawbacks**:
  * **Lock Contention**: Severe scalability bottleneck as core counts grow (16, 64, 128 cores).
  * **Poor Cache Affinity**: A process might execute on Core 0, get preempted, and resume on Core 3, blowing away L1/L2 cache data.

### B. Per-CPU Multi-Queue (MQMS - Multi-Queue Multiprocessor Scheduling)
* Each CPU core possesses its own private runqueue (e.g. Linux CFS per-CPU runqueues).
* Tasks assigned to a core run exclusively on that core unless explicitly migrated.
* **Advantages**: Zero lock contention between cores; excellent cache warmth.
* **Challenge**: **Load Imbalance** (one core is overwhelmed with work while another core sits idle).

---

## 3. Load Balancing: Push and Pull Migration
To resolve imbalance in Multi-Queue architectures:
1. **Push Migration**: A periodic kernel watchdog task inspects all per-CPU runqueues. If an imbalance is detected, it "pushes" excess tasks from overloaded cores to idle cores.
2. **Pull Migration**: When a CPU core finds its own runqueue completely empty, it actively "pulls" (steals) a runnable task from an overloaded neighboring core's queue (**Work Stealing**).

---

## 4. Processor Affinity and NUMA
Processors have high-speed private L1 and L2 caches containing memory pages recently accessed by the running process.
* **Processor Affinity**: A process has an affinity for the CPU core on which it is currently executing to avoid cache invalidation overhead.
  * **Soft Affinity**: The OS attempts to keep a process on the same core, but will migrate it if load balancing strictly demands it.
  * **Hard Affinity**: A process explicitly pins itself to specific cores using system calls (e.g., Linux `sched_setaffinity()` with a CPU affinity mask).

### NUMA (Non-Uniform Memory Access):
* In large multi-socket server architectures, CPUs share physical address space, but each CPU socket has **local memory** and **remote memory**.
* Accessing local memory attached to the CPU's own memory bus is up to 3x faster than accessing remote memory over interconnect buses (UPI / Infinity Fabric).
* **NUMA-Aware Schedulers**: The OS schedules threads on the CPU cores directly attached to the memory nodes where the thread's memory was allocated!

---

## 5. Thread Scheduling: PCS vs. SCS
Threads are the actual schedulable units in modern operating systems:
1. **Process Contention Scope (PCS)**:
   * In Many-to-One and Many-to-Many thread models.
   * User-level thread libraries schedule user threads onto available kernel threads (Lightweight Processes / LWPs).
   * Contention for the CPU happens strictly among threads belonging to the **same process**.
2. **System Contention Scope (SCS)**:
   * In One-to-One thread models (used by Linux, Windows, macOS).
   * Every user thread corresponds directly to a kernel schedulable entity.
   * Contention for CPU cores occurs across **all threads in the entire system**.

---

## 6. Gang Scheduling and Co-Scheduling
In parallel and High-Performance Computing (HPC) applications:
* Multiple cooperating threads frequently communicate and synchronize via spinlocks and barriers.
* If Thread 1 is scheduled on Core 0 while its communicating peer Thread 2 is preempted on Core 1, Thread 1 wastes massive CPU time spinning uselessly on a lock!
* **Gang Scheduling**: The OS schedules a group ("gang") of related cooperating threads **simultaneously across multiple CPU cores** in the exact same time slice. If one is preempted, all are preempted together.
