# Common Misconceptions in Operating Systems CPU Scheduling

## Misconception 1: Waiting Time and Response Time are the Same
- **The Error**: Many students assume Waiting Time and Response Time are identical because they coincide in non-preemptive algorithms when a process runs uninterrupted.
- **The Reality**: 
  - **Response Time** is measured only until the process gets the CPU for the *first* time: $RT = \text{FirstStart} - AT$.
  - **Waiting Time** is the *total* time spent waiting in the ready queue throughout the process's entire life cycle: $WT = TAT - BT$.
  - In preemptive algorithms (such as Round Robin or SRTF), a process may start immediately (RT = 0), but then get interrupted multiple times, accumulating significant waiting time.

## Misconception 2: High Time Quantum Always Improves Throughput
- **The Error**: Believing that larger time quantums always make systems run faster or produce higher throughput.
- **The Reality**: Increasing the quantum decreases context switching overhead, which helps CPU utilization. However, if the quantum is too large, Round Robin degrades into FCFS, causing long response times for interactive processes and convoy effects.

## Misconception 3: Smaller Numerical Priority Always Means Lower Priority
- **The Error**: Assuming priority numbers always work like scores (where bigger number = better).
- **The Reality**: In standard UNIX and academic OS textbooks (Silberschatz, Galvin, Gagne), lower numbers denote higher priority (Priority 0 is top priority, Priority 127 is lowest). Always check the convention stated in the problem.

## Misconception 4: Preemption Always Requires Re-sorting the Entire Ready Queue
- **The Error**: Believing that every preemption in Round Robin triggers complex priority re-evaluation.
- **The Reality**: In standard Round Robin, preemption simply moves the expired process to the tail of the FIFO queue. Newly arrived processes at the boundary take precedence before the requeued process.

## Misconception 5: FCFS is Starvation-Free, So It is Always Fair
- **The Error**: Believing that because FCFS has no starvation, it provides good fairness.
- **The Reality**: While FCFS prevents infinite starvation, it can be extremely unfair in terms of average waiting time. A 1 ms job arriving 1 microsecond after a 100-hour job must wait 100 hours to run!
