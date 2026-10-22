# Process States, Transitions, and Process Control Block (PCB)

## 1. Process States and The 5-State Life Cycle Model

As a process executes, its execution state changes. The standard Operating System 5-state model consists of:

1. **New**: The process is being created (memory allocated, PCB initialized) but is not yet admitted into the ready pool.
2. **Ready**: The process is loaded into main memory and is waiting to be allocated a CPU core by the short-term scheduler. All resources except the CPU are acquired.
3. **Running**: The process instructions are currently being executed by the physical processor core.
4. **Waiting (Blocked)**: The process cannot execute because it is waiting for an external event to occur (such as completion of an I/O request, receipt of a signal, or acquisition of a lock/semaphore).
5. **Terminated**: The process has finished executing its code or was forcibly aborted by the OS, and its resources are being deallocated.

### Life Cycle State Transitions:
* **Admitted** ($\text{New} \to \text{Ready}$): The long-term scheduler admits the process into the ready queue.
* **Scheduler Dispatch** ($\text{Ready} \to \text{Running}$): The CPU scheduler selects the process and the dispatcher allocates the CPU.
* **Interrupt / Timeout** ($\text{Running} \to \text{Ready}$): A hardware timer interrupt occurs (time quantum expires) or a higher-priority process arrives, causing preemption.
* **I/O or Event Wait** ($\text{Running} \to \text{Waiting}$): The process requests I/O or blocks on an event/resource.
* **I/O or Event Completion** ($\text{Waiting} \to \text{Ready}$): The I/O hardware device finishes and signals the kernel; the process moves back to the ready queue (never directly back to running!).
* **Exit** ($\text{Running} \to \text{Terminated}$): The process executes its final statement or calls `exit()`.

---

## 2. Process Control Block (PCB / Task Control Block)

The **Process Control Block (PCB)** is the fundamental data structure used by the operating system kernel to maintain all metadata and execution context for a specific process:

1. **Process State**: Current state (New, Ready, Running, Waiting, Terminated).
2. **Process Identifier (PID)**: Unique numerical identifier assigned to the process.
3. **Program Counter (PC)**: Address of the next machine instruction to be executed for this process.
4. **CPU Registers**: Includes accumulators, index registers, stack pointers, general-purpose registers, and condition-code flags. When an interrupt occurs, these must be saved into the PCB so the process can be restored later without loss of work.
5. **CPU-Scheduling Information**: Process priority, pointers to scheduling queues, and other scheduling parameters (e.g., remaining burst time, aging counters).
6. **Memory-Management Information**: Base and limit registers, page tables, or segment tables depending on the memory architecture used by the OS.
7. **Accounting Information**: Amount of CPU used, execution time limits, account numbers, process owner.
8. **I/O Status Information**: List of I/O devices allocated to the process, list of open files (file descriptor table).

---

## 3. The CPU-I/O Burst Cycle

Process execution consists of a cycle of **CPU execution** and **I/O wait**:
* **CPU Burst**: A period of active mathematical or logical computation on the CPU.
* **I/O Burst**: A period of waiting for data transfer between memory and peripheral devices.
* **Workload Characteristics**:
  * **CPU-Bound Process**: Spends the majority of its lifetime in very long CPU bursts with infrequent, short I/O bursts (e.g., scientific simulations, rendering, video encoding).
  * **I/O-Bound Process**: Spends the majority of its lifetime waiting for I/O, characterized by many very short CPU bursts followed by long I/O bursts (e.g., text editors, web browsers, database queries).
* A system with only CPU-bound processes suffers from low device utilization. A balanced scheduler mixes both to keep both the CPU and I/O devices saturated.
