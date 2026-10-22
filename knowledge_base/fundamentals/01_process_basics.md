# Process Fundamentals and CPU Execution Concepts

## Process vs Program
A **program** is a passive entity, such as a file containing a list of instructions stored on disk (an executable). In contrast, a **process** is an active entity—a program in execution. A process requires system resources, including CPU time, memory, files, and I/O devices, to accomplish its task.

When a program is executed, the operating system loads its instructions into memory and creates a Process Control Block (PCB) to track its execution context:
- **Text section**: The compiled program code.
- **Program counter (PC)**: Indicates the address of the next instruction to execute.
- **CPU registers**: Contents of general-purpose and condition registers.
- **Stack**: Contains temporary data such as function parameters, return addresses, and local variables.
- **Data section**: Contains global and static variables.
- **Heap**: Memory dynamically allocated during process runtime.

## Process States and State Transitions
During its lifetime, a process transitions through several fundamental states:
1. **New**: The process is being created.
2. **Ready**: The process is in main memory waiting to be assigned to a CPU. All ready processes reside in the **ready queue**.
3. **Running**: Instructions are currently being executed on the CPU.
4. **Waiting (Blocked)**: The process cannot execute because it is waiting for some external event (such as completion of an I/O operation or reception of a signal).
5. **Terminated**: The process has finished execution and its resources are reclaimed.

Key transitions include:
- `Ready -> Running`: The CPU scheduler selects a process from the ready queue and dispatches it.
- `Running -> Ready`: A timer interrupt occurs (in preemptive scheduling), or a higher-priority process arrives.
- `Running -> Waiting`: The process requests an I/O operation or system call that requires waiting.
- `Waiting -> Ready`: The I/O operation completes, and the process is placed back into the ready queue.
- `Running -> Terminated`: The process completes its execution or encounters a fatal error.

## CPU Bursts and I/O Bursts
Process execution consists of a cycle of **CPU execution** and **I/O wait**:
- A **CPU burst** is a contiguous duration where the process performs calculations and executes machine instructions on the CPU without blocking.
- An **I/O burst** is the duration spent waiting for input/output devices (disk, network, user keyboard input).

Processes can be broadly characterized as:
- **CPU-bound processes**: Characterized by a few very long CPU bursts and short/infrequent I/O bursts (e.g., scientific computing, numerical simulations, video encoding).
- **I/O-bound processes**: Characterized by many short CPU bursts interspersed with long I/O bursts (e.g., text editors, web browsers, database queries).
