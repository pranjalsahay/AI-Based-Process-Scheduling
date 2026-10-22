# Proportional-Share Scheduling: Lottery and Stride Scheduling

## 1. Concept of Proportional-Share Scheduling
Unlike priority-based schedulers that aim to maximize turnaround time or enforce strict urgency, **Proportional-Share (Fair-Share) Schedulers** guarantee that each process receives a predetermined fraction of total CPU time:
* If process A has weight 75 and process B has weight 25, Process A is guaranteed 75% of the CPU and Process B receives 25%.

---

## 2. Lottery Scheduling (Randomized Proportional Share)
Pioneered by Carl Waldspurger and William Weihl (1994):
* The fundamental currency is the **Lottery Ticket**.
* If 100 total tickets are issued, and Process A holds 75 tickets ($0-74$) while Process B holds 25 tickets ($75-99$):
  1. At every scheduling quantum, the scheduler draws a random number from $[0, 99]$.
  2. The process holding the winning ticket executes for that quantum.
* Over time, by the **Law of Large Numbers**, Process A receives approximately 75% of the CPU and Process B receives 25%.

### Ticket Mechanisms:
1. **Ticket Currency**: A user can allocate local tickets within their own tasks, which the OS converts to global tickets based on the user's overall allocation.
2. **Ticket Transfer**: A client process can temporarily transfer its tickets to a server process handling its Remote Procedure Call (RPC) to accelerate completion and eliminate priority inversion.
3. **Ticket Inflation**: In mutually trusting environments, a process can temporarily boost its own tickets when executing an urgent sub-routine, then deflate them afterwards.

---

## 3. Stride Scheduling (Deterministic Proportional Share)
While Lottery Scheduling is simple and elegant, randomness causes short-term deviations from the exact fair share. Waldspurger developed **Stride Scheduling** as a purely **deterministic** proportional-share algorithm.

### The Algorithm:
1. Choose a large constant integer, such as $L = 10,000$.
2. For each process $i$ with tickets $T_i$, compute its **Stride ($S_i$)**:
   $$S_i = \frac{L}{T_i}$$
   *(More tickets $\implies$ smaller stride).*
3. Each process maintains a variable called **Pass Value ($P_i$)**, initialized to 0.
4. **Scheduling Rule**:
   * Always pick the process with the **lowest pass value** ($P_i$).
   * Run it for one time quantum.
   * Increment its pass value by its stride:
     $$P_i \leftarrow P_i + S_i$$

### Example:
Processes A, B, and C have tickets 100, 50, and 250 with $L = 10,000$:
* $S_A = 10,000 / 100 = 100$
* $S_B = 10,000 / 50 = 200$
* $S_C = 10,000 / 250 = 40$
Because Process C has the smallest stride (40), its pass value grows slowest, so it gets selected much more frequently (exactly 5x as often as B and 2.5x as often as A) with zero random variance!
