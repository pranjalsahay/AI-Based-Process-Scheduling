# Evaluation, Queuing Analysis, and Comprehensive Comparative Matrix of CPU Schedulers

## 1. Quantitative Evaluation Methodologies for Scheduling Algorithms

Operating systems researchers and system architects employ four complementary methodologies to evaluate and compare CPU scheduling algorithms:

### A. Deterministic Modeling (Analytic Evaluation)
Deterministic modeling takes a predefined, predetermined workload (a fixed trace of process arrival times and CPU burst times) and calculates the exact mathematical performance metrics (turnaround time, waiting time, response time, CPU utilization) for each algorithm on that specific workload.
* **Advantages**: Simple, fast, deterministic, produces exact numerical figures for side-by-side comparison.
* **Limitations**: Workloads are artificial; results are valid only for the specific input scenario and cannot be broadly generalized without extensive workload sampling.

---

### B. Queuing Models and Little's Law
In modern multi-user, multi-tasking operating systems, process arrival and CPU burst executions are stochastic (probabilistic). A computer system is modeled as a network of servers (CPUs, storage controllers, network cards) with waiting queues.

#### Little's Formula (Fundamental Theorem of Queuing Theory):
Established by John Little (1961), Little's Law states that under steady-state conditions, the average number of processes in a queuing system ($N$) equals the average arrival rate ($\lambda$) multiplied by the average time a process spends in the system ($W$):

$$N = \lambda \times W$$

Similarly, for the waiting queue alone:
$$N_q = \lambda \times W_q$$

Where:
* $N$: Average number of processes in the system.
* $N_q$: Average number of processes waiting in the ready queue.
* $\lambda$: Average arrival rate of processes (e.g. processes per millisecond).
* $W$: Average turnaround time (waiting time + service time).
* $W_q$: Average waiting time in the ready queue.

#### M/M/1 Queuing System:
For a single CPU server with Poisson arrivals (parameter $\lambda$) and exponentially distributed service times with mean service rate $\mu$:
1. **Server Utilization ($\rho$)**:
   $$\rho = \frac{\lambda}{\mu} \quad (\text{Stability condition: } \rho < 1)$$
2. **Average Number of Processes in System ($N$)**:
   $$N = \frac{\rho}{1 - \rho} = \frac{\lambda}{\mu - \lambda}$$
3. **Average Turnaround Time ($W$)**:
   $$W = \frac{1}{\mu - \lambda} = \frac{1}{\mu(1 - \rho)}$$
4. **Average Waiting Time in Ready Queue ($W_q$)**:
   $$W_q = W - \frac{1}{\mu} = \frac{\lambda}{\mu(\mu - \lambda)} = \frac{\rho}{\mu(1 - \rho)}$$

*As CPU utilization $\rho$ approaches 1 (100%), average waiting time and queue length explode exponentially towards infinity.*

---

### C. Simulation Modeling
Simulations programmatically emulate the components of the operating system:
* A clock variable tracks simulated time.
* Data structures represent PCBs, ready queues, and device queues.
* Event-driven simulators generate events from either:
  1. **Synthetic probability distributions** (exponential, uniform, hyperexponential).
  2. **Trace files**: Real execution logs captured by kernel probes (e.g. Linux `ftrace`, `eBPF`, `perf`) recording actual process arrival times, CPU burst lengths, and disk I/O requests.

---

### D. Direct Implementation and Kernel Profiling
The ultimate evaluation involves implementing the scheduling algorithm directly inside the kernel (e.g. writing a new scheduling class in the Linux kernel) and measuring performance on physical hardware under real production workloads.
* **Challenges**: High software engineering complexity, risk of kernel crashes/data corruption, hardware dependency, high cost.

---

## 2. Comprehensive Comparative Matrix of CPU Scheduling Algorithms

| Algorithm | Preemption Mode | Starvation Risk | Context Switch Overhead | Provable Optimality | Primary Metric Optimized | Real-World Adoption & Best Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **First-Come, First-Served (FCFS)** | Non-Preemptive | Provably Starvation-Free | Minimum ($N$ switches for $N$ jobs) | None | Simplicity, fairness of arrival | Batch processing, background print queues, device driver I/O requests |
| **Shortest Job First (SJF)** | Non-Preemptive | High (Long jobs starve if short jobs stream in) | Low | Provably optimal minimum average waiting time for simultaneous arrivals | Average Waiting Time | Long-term batch scheduling where job runtimes are declared in advance |
| **Shortest Remaining Time First (SRTF)** | Preemptive | High (Long jobs starve if short jobs stream in) | Moderate to High (frequent preemptions on short arrivals) | Optimal minimum average waiting time for dynamic arrivals | Average Waiting Time & Turnaround Time | General batch systems with predictable burst lengths |
| **Round Robin (RR)** | Preemptive (Timer-driven) | Provably Starvation-Free | High if quantum $q$ is small; Low if $q$ is balanced | None | Interactive Response Time | General-purpose time-sharing OS, user interactive command lines |
| **Priority Scheduling** | Preemptive or Non-Preemptive | Severe for low priority tasks (mitigated by Aging) | Moderate (preemption on higher priority arrival) | None | Urgency, criticality, business priority | Real-time kernels, embedded microcontrollers, system daemon isolation |
| **Highest Response Ratio Next (HRRN)** | Non-Preemptive | Provably Starvation-Free (Aging built into formula) | Low (no mid-burst preemption) | Balances short job bias with starvation prevention | Waiting Time / Turnaround Time ratio ($R = 1 + W/S$) | Batch operating systems, long-running scientific compute jobs |
| **Multilevel Queue (MLQ)** | Preemptive (Fixed Priority between queues) | Severe for lower queues unless time-sliced | Moderate | None | Process classification isolation | Legacy systems separating system, interactive, batch, and student jobs |
| **Multilevel Feedback Queue (MLFQ)** | Preemptive (Dynamic feedback) | Prevented by periodic Priority Boost (Rule 5) | Moderate | Approximates SJF dynamically without advance burst knowledge | Response time for I/O tasks; Throughput for CPU tasks | Modern desktop & server OS (macOS, Windows NT, BSD schedulers) |
| **Completely Fair Scheduler (CFS)** | Preemptive (Dynamic virtual runtime) | Provably Starvation-Free ($vruntime$ bounded) | Low ($O(\log N)$ tree update, $O(1)$ selection, `min_granularity`) | Proportional fairness, maximum resource equity | Proportional CPU fairness, interactive latency | Linux kernel (default since 2.6.23), Android OS, high-density containers |
| **Rate Monotonic Scheduling (RMS)** | Preemptive (Static rate-based) | Low for admissible task sets; non-admissible tasks miss deadlines | Moderate | Provably optimal static priority algorithm on uniprocessors | Meeting hard deadlines for periodic tasks | Avionics, automotive engine controllers, robotics (VxWorks, FreeRTOS) |
| **Earliest Deadline First (EDF)** | Preemptive (Dynamic deadline-based) | Low up to 100% utilization | Moderate to High | Provably optimal dynamic algorithm; achieves up to 100% schedulability | Meeting hard deadlines with dynamic priorities | Multimedia streaming, digital signal processing, hard real-time systems |
| **Lottery Scheduling** | Preemptive (Probabilistic time-slice) | Vanishingly low over large $N$ | Low to Moderate | Proportional share over long time horizons | Flexible proportional share, ticket transfer | Virtual machine hypervisors, cloud multi-tenant resource sharing |
| **Stride Scheduling** | Preemptive (Deterministic pass value) | Provably Starvation-Free | Low to Moderate ($O(\log N)$ priority queue) | Exact proportional share with zero random variance | Deterministic proportional allocation | High-precision scientific simulation, deterministic container quotas |
