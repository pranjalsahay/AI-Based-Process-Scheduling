# Round Robin (RR) CPU Scheduling and Time Quantum Trade-offs

## Principle and Mechanism
The **Round Robin (RR)** scheduling algorithm is designed specifically for time-sharing systems. It is similar to FCFS, but preemption is added to switch between processes.

A small unit of time, called a **time quantum** (or time slice), is defined (typically between 10 to 100 milliseconds):
1. The ready queue is treated as a circular FIFO queue.
2. The CPU scheduler picks the process at the head of the ready queue, sets an interrupt timer to expire after 1 time quantum, and dispatches the process.
3. If the process has a remaining burst time less than or equal to the time quantum:
   - The process runs until it finishes, releases the CPU voluntarily, and terminates.
4. If the process has a remaining burst time longer than the time quantum:
   - The timer goes off and generates a hardware interrupt to the OS.
   - A context switch occurs: the running process is placed at the tail of the ready queue.
   - The CPU scheduler then selects the next process at the head of the ready queue.

## Queue Management at Quantum Boundary
When an incoming process arrives at the exact instant $t$ that the currently executing process exhausts its time quantum:
- Standard OS convention dictates that the newly arrived process joins the ready queue **first**.
- The preempted process is then appended **behind** the newly arrived process.

## Selecting the Time Quantum: Trade-offs
The performance of Round Robin depends heavily on the choice of the time quantum $q$:
- **Extremely Large Quantum ($q \to \infty$)**: If the time quantum is larger than the longest burst time, Round Robin degenerates into **FCFS**.
- **Extremely Small Quantum ($q \to 0$)**: The policy is called **processor sharing** (in theory, appearing as though each of $n$ processes has its own $1/n$ speed CPU). However, each quantum expiration incurs a context switch. If the quantum is comparable to the context-switch time (e.g., $q = 1$ ms with context-switch time of $0.2$ ms), up to 20% of total CPU capacity is wasted on pure switching overhead.

### Rule of Thumb
As a practical heuristic, **80 percent of the CPU bursts should be shorter than the time quantum**. This balances rapid response time for interactive I/O-bound tasks while avoiding excessive context switching for CPU-bound tasks.
