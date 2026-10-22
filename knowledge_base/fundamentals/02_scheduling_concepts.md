# CPU Scheduling Architecture: Schedulers, Dispatchers, and Preemption

## The CPU Scheduler (Short-Term Scheduler)
Whenever the CPU becomes idle, the operating system must select one of the processes in the ready queue to be executed. This selection is carried out by the **short-term scheduler** (or CPU scheduler). The scheduler executes frequently (typically every few milliseconds) and must make fast, lightweight decisions using an algorithm such as FCFS, SJF, SRTF, Priority, or Round Robin.

## The Dispatcher and Dispatch Latency
The **dispatcher** is the kernel module that gives physical control of the CPU to the process selected by the short-term scheduler. The dispatcher's responsibilities include:
1. **Switching context**: Saving the CPU state (registers, program counter) of the outgoing process into its PCB and restoring the state of the incoming process from its PCB.
2. **Switching to user mode**: Changing the processor execution privilege mode from kernel mode (supervisor mode) to user mode.
3. **Jumping to the proper location**: Loading the program counter with the saved instruction pointer of the incoming program to restart or continue its execution.

**Dispatch Latency** is the exact elapsed time required for the dispatcher to stop one process and start another running. During dispatch latency, no productive user-level computation occurs. Minimizing dispatch latency is crucial for system responsiveness.

## Preemptive vs Non-Preemptive Scheduling
CPU-scheduling decisions take place under four operating circumstances:
1. When a process switches from the **Running** state to the **Waiting** state (e.g., as the result of an I/O request).
2. When a process switches from the **Running** state to the **Ready** state (e.g., when a hardware timer interrupt occurs).
3. When a process switches from the **Waiting** state to the **Ready** state (e.g., at completion of I/O).
4. When a process **Terminates**.

### Non-Preemptive (Cooperative) Scheduling
Under non-preemptive scheduling, once the CPU has been allocated to a process, the process keeps the CPU until it releases it either by terminating (case 4) or by switching to the waiting state (case 1). The OS kernel never forcibly interrupts a running process to allocate the CPU to another task. Examples: FCFS, standard SJF, non-preemptive Priority.

### Preemptive Scheduling
Under preemptive scheduling, the operating system kernel can interrupt and suspend a currently running process before its CPU burst has completed (cases 2 and 3). Preemption is driven by hardware clock interrupts, priority comparisons, or arrival of shorter remaining jobs. Examples: SRTF (preemptive SJF), Preemptive Priority, and Round Robin.
Preemptive scheduling provides superior responsiveness for interactive systems but incurs context-switching overhead and requires careful synchronization of shared kernel data structures.
