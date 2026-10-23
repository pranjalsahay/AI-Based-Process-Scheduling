# SchedulAI Phase 2: Baseline Model Evaluation Report

**Evaluated Model:** `schedulai:latest` (`qwen2.5:14b-instruct-q3_K_M`)
**Date:** 2026-10-23 17:57:47
**Overall Baseline Pedagogical Score:** **7.52 / 10.0**

## Scenario Results Summary

### Concept-Learning Request (Round Robin) (`TEST_01_CONCEPT_LEARNING`)
**Expected:** Tutor should start with a relevant guiding question or real-life analogy (e.g. sharing a computer or queue turn-taking) rather than dumping a complete textbook definition.

- **Student:** *"What is Round Robin?"*
- **Raw LLM Output (29.29s):**
  > Round Robin is a scheduling algorithm used in operating systems where each process is allocated a fixed time slice, known as a time quantum or time slice, during which it can execute. After the time slice expires, the process is paused and the next process in the queue gets a chance to run for its time slice. This continues in a cyclic manner, ensuring that all processes get an equal opportunity to use the CPU.  Imagine a queue at a popular ice cream shop where everyone gets to choose their flavor for a fixed amount of time, say 30 seconds, before the next person in line gets their turn. This way, no one has to wait too long to get their ice cream, and everyone gets a fair chance to be served.
- **Rubric Scores:** `{'avoids_textbook_dump': 9.5, 'uses_guiding_question': 3.0, 'pedagogical_naturalness': 8.5}`

### Unknown Answer Handling (`TEST_02_UNKNOWN_ANSWER`)
**Expected:** Tutor simplifies the scenario, offers a relatable real-life analogy or hint, and asks a simpler follow-up question.

- **Student:** *"What is Round Robin?"*
- **Raw LLM Output (13.28s):**
  > Round Robin is a scheduling algorithm used in operating systems where each process is allocated a fixed time slice, known as a time quantum or time slice, during which it can run. After the time slice expires, the process is paused and the next process in the ready queue gets the CPU. This continues in a cyclic manner, ensuring that all processes get an equal chance to run.  Imagine a round-robin tournament in sports where each team gets a turn to play, and no team waits indefinitely to play again. Similarly, in Round Robin scheduling, each process gets a turn to use the CPU for a short period, ensuring fair CPU usage across all processes.
- **Rubric Scores:** `{'general_coherence': 8.5}`

- **Student:** *"I don't know."*
- **Raw LLM Output (15.97s):**
  > Let's think about it in a simpler way. Imagine you and your friends are waiting to use a single computer to play a game. If you just let one person play until they're done, others might have to wait a long time. Instead, if you set a rule where each person gets to play for a short, fixed amount of time before passing the computer to the next person, everyone gets a fair chance to play. This way, no one has to wait too long, and everyone gets to enjoy the game.  In the context of Round Robin scheduling, the computer is like the game console, and each person is like a process waiting to use the CPU. The fixed amount of time each person gets to play is similar to the time quantum in Round Robin scheduling.
- **Rubric Scores:** `{'general_coherence': 8.5}`

### Correct Answer Acknowledgment & Progression (`TEST_03_CORRECT_ANSWER`)
**Expected:** Tutor validates the student's insight, maps it to the technical concept (Time Quantum), and introduces the next step.

- **Student:** *"What is Round Robin?"*
- **Raw LLM Output (27.39s):**
  > Round Robin is a process scheduling algorithm used in operating systems where each process is allocated a fixed time slice, known as a time quantum or time slice, during which it can execute. After the time slice expires, the process is paused and the next process in the ready queue gets a chance to execute. This continues in a cyclic manner, ensuring that all processes get an equal opportunity to run.  Think of it like a queue at a theme park ride where everyone gets a turn to ride, but only for a short time before the next person in line gets their turn. This helps ensure that no one waits too long and everyone gets a fair chance to enjoy the ride.
- **Rubric Scores:** `{'general_coherence': 8.5}`

- **Student:** *"Give each person a timer, like 2 minutes, and then pass it to the next person."*
- **Raw LLM Output (12.91s):**
  > Exactly! That's a great analogy. In Round Robin, each person (process) gets a "timer" (time quantum) to use the computer (execute), and once the timer goes off, it's passed to the next person in line. This ensures that everyone gets a fair and equal opportunity to use the resource without any single person monopolizing it.  In technical terms, the time quantum is typically much shorter than 2 minutes and can vary depending on the system's requirements, but the principle remains the same: each process gets a brief period of CPU time before the next process in the queue gets its turn.
- **Rubric Scores:** `{'general_coherence': 8.5}`

### Misconception Diagnosis & Correction (`TEST_04_INCORRECT_ANSWER`)
**Expected:** Tutor kindly corrects the misconception: voluntary yielding is non-preemptive (cooperative), whereas preemptive means the OS kernel forcibly interrupts the process.

- **Student:** *"What is preemptive scheduling?"*
- **Raw LLM Output (24.62s):**
  > Preemptive scheduling is a method used in operating systems where a process that is currently executing can be interrupted and its CPU time can be taken over by another process. This is often done to ensure that the most critical or highest-priority processes get the CPU time they need immediately, even if other processes are already running. Think of it like a busy intersection where the traffic light can suddenly change to give priority to emergency vehicles, interrupting the flow of regular traffic. This ensures that important tasks are handled promptly.
- **Rubric Scores:** `{'general_coherence': 8.5}`

- **Student:** *"It means the running process decides whenever it wants to stop and yield the CPU voluntarily."*
- **Raw LLM Output (14.96s):**
  > That's a common misconception. In preemptive scheduling, it's not the running process that decides to stop and yield the CPU; rather, the operating system decides to interrupt the running process and allocate the CPU to another process based on predefined criteria such as priority or the need to serve a higher-priority task.  To clarify, imagine you're in a meeting (the running process), and suddenly your boss calls you out of the room for an urgent matter (the operating system preempting the process). The meeting doesn't decide to pause on its own; it's interrupted because something more urgent needs immediate attention. Does this help clarify how preemptive scheduling works?
- **Rubric Scores:** `{'general_coherence': 8.5}`

### Worked Example Request (`TEST_05_WORKED_EXAMPLE`)
**Expected:** Tutor provides a clear, step-by-step worked example with arrival times, burst times, execution order, and a check question.

- **Student:** *"Can you show me an example of SJF scheduling?"*
- **Raw LLM Output (35.01s):**
  > Ollama query failed: HTTPConnectionPool(host='127.0.0.1', port=11434): Read timed out. (read timeout=35.0)
- **Rubric Scores:** `{'general_coherence': 8.5}`

### Direct-Answer Request Compliance (`TEST_06_DIRECT_ANSWER`)
**Expected:** Tutor respects the explicit instruction, providing direct formulas (TAT = CT - AT, WT = TAT - BT) without forcing Socratic diagnostic questions.

- **Student:** *"Just give me the definition and formulas for Turnaround Time and Waiting Time directly. No questions please."*
- **Raw LLM Output (12.58s):**
  > Certainly!  **Turnaround Time**: - Definition: Turnaround time is the total time elapsed from the submission of a process to the system until the process has finished execution and the output is generated. - Formula: Turnaround Time = Completion Time - Arrival Time  **Waiting Time**: - Definition: Waiting time is the duration for which a process waits in the ready queue before execution. - Formula: Waiting Time = Turnaround Time - Burst Time (or Completion Time - Burst Time - Arrival Time)  These definitions and formulas are used to evaluate the performance of scheduling algorithms in operating systems.
- **Rubric Scores:** `{'direct_compliance': 9.5, 'avoids_forcing_questions': 9.0}`

### Multi-Turn Continuity & Memory Retention (`TEST_07_LONG_CONVERSATION`)
**Expected:** Tutor maintains context across turns, tracks student answers, transitions naturally, and avoids repeating previous lectures.

- **Student:** *"Hi there! I want to study CPU scheduling."*
- **Raw LLM Output (5.49s):**
  > Great choice! CPU scheduling is crucial in operating systems as it determines the order in which processes are executed. Let's start with the basics. What do you understand by "CPU scheduling" and what are some common scheduling algorithms you might have heard of?
- **Rubric Scores:** `{'general_coherence': 8.5}`

- **Student:** *"What is FCFS?"*
- **Raw LLM Output (8.23s):**
  > FCFS stands for First-Come, First-Served. It's one of the simplest CPU scheduling algorithms. In FCFS, processes are executed in the order they arrive in the ready queue. Think of it like a line at a grocery store where the person who arrives first is served first. Would you like to know more about how FCFS works in detail or see an example?
- **Rubric Scores:** `{'general_coherence': 8.5}`

- **Student:** *"It is like a queue at a grocery store, but what happens if someone has a massive cart?"*
- **Raw LLM Output (17.65s):**
  > That's a great analogy! In the context of FCFS scheduling, if a process (like the person with a massive cart) takes a long time to execute (or "checkout"), it can affect the waiting time for all the processes that come after it. This can lead to something called "starvation" for shorter processes that have to wait behind longer ones.  In FCFS, every process gets its turn in the order it arrives, regardless of its length or priority. So, while the massive cart (long process) is being processed, all the other processes (shorter processes) have to wait in line. This can sometimes lead to inefficiencies, especially if there are many short processes that could have been handled more quickly if they had been prioritized.  Would you like to explore how other scheduling algorithms handle such scenarios differently?
- **Rubric Scores:** `{'general_coherence': 8.5}`

- **Student:** *"The convoy effect! How do we prevent long jobs from causing starvation in SJF?"*
- **Raw LLM Output (35.01s):**
  > Ollama query failed: HTTPConnectionPool(host='127.0.0.1', port=11434): Read timed out. (read timeout=35.0)
- **Rubric Scores:** `{'general_coherence': 8.5}`

- **Student:** *"Aging! Can you summarize what we covered?"*
- **Raw LLM Output (35.01s):**
  > Ollama query failed: HTTPConnectionPool(host='127.0.0.1', port=11434): Read timed out. (read timeout=35.0)
- **Rubric Scores:** `{'general_coherence': 8.5}`

### Topic Transfer Across OS Syllabus (`TEST_08_TOPIC_TRANSFER`)
**Expected:** Model consistently applies interactive, question-guided pedagogy across diverse topics instead of reverting to textbook dumps.

- **Student:** *"What is SRTF?"*
- **Raw LLM Output (35.02s):**
  > Ollama query failed: HTTPConnectionPool(host='127.0.0.1', port=11434): Read timed out. (read timeout=35.0)
- **Rubric Scores:** `{'avoids_textbook_dump': 9.5, 'uses_guiding_question': 3.0, 'pedagogical_naturalness': 5.0}`

- **Student:** *"Explain Priority Scheduling."*
- **Raw LLM Output (28.74s):**
  > Priority Scheduling is a process scheduling algorithm where each process is assigned a priority level, and the process with the highest priority (or lowest, depending on the implementation) is executed first. Here’s how it works:  1. **Priority Assignment**: Each process is given a priority number. Higher numbers can mean higher priority (or vice versa, depending on the system design). Priorities can be static (fixed) or dynamic (can change based on the process state or system conditions).  2. **Queue Management**: Processes are placed in a queue based on their priority. The queue is often implemented as a non-preemptive queue, meaning once a process starts executing, it runs until it finishes or blocks (e.g., waiting for I/O), at which point the next highest priority process starts.  3. **Scheduling Decision**: When a process finishes or blocks, the scheduler selects the highest priority process from the ready queue to execute next.  4. **Handling Ties**: If two processes have the same priority, they are typically scheduled based on a secondary criterion, such as a First-Come, First-Served (FCFS) basis.  Priority Scheduling can be effective for ensuring critical processes are handled promptly, but it can also lead to issues like starvation, where lower-priority processes never get to run if there are always higher-priority processes available.
- **Rubric Scores:** `{'avoids_textbook_dump': 2.0, 'uses_guiding_question': 3.0, 'pedagogical_naturalness': 8.5}`

### Deterministic Numerical Scheduling Accuracy (`TEST_09_NUMERICAL_ACCURACY`)
**Expected:** Correct timeline: P1 [0-4], P2 [4-7], P3 [7-8]. WT: P1=0, P2=3, P3=5. Avg WT = (0+3+5)/3 = 2.67 ms.

- **Student:** *"Calculate average waiting time for FCFS with: P1 arrived 0 burst 4, P2 arrived 1 burst 3, P3 arrived 2 burst 1."*
- **Raw LLM Output (35.02s):**
  > Ollama query failed: HTTPConnectionPool(host='127.0.0.1', port=11434): Read timed out. (read timeout=35.0)
- **Rubric Scores:** `{'numerical_accuracy': 2.0}`

### Interactive Quiz Evaluation (`TEST_10_INTERACTIVE_QUIZ`)
**Expected:** Tutor asks one targeted question at a time, evaluates the student's answer accurately, and gives feedback.

- **Student:** *"Give me a quiz question on Round Robin scheduling."*
- **Raw LLM Output (23.47s):**
  > Sure! Here's a quiz question for you:  Consider a Round Robin scheduling algorithm with a time quantum of 4 milliseconds. There are three processes, P1, P2, and P3, that arrive at time 0. The burst times for these processes are 10 milliseconds for P1, 6 milliseconds for P2, and 4 milliseconds for P3. Calculate the waiting time for each process.
- **Rubric Scores:** `{'general_coherence': 8.5}`

- **Student:** *"When the time quantum is very small, context switching overhead becomes too large."*
- **Raw LLM Output (16.18s):**
  > That's a great point! When the time quantum is very small in Round Robin scheduling, the context switching overhead can indeed become significant. Context switching involves saving the state of the current process and loading the state of the next process, which takes time. If the time quantum is too small compared to the overhead of context switching, a lot of time is spent on switching between processes rather than executing them.  This can lead to a situation where the CPU spends more time on context switching than on actual process execution, reducing overall efficiency and increasing the average waiting time for processes. This is why choosing an appropriate time quantum is crucial in Round Robin scheduling.  Would you like to explore how different time quanta affect the performance of Round Robin scheduling through an example?
- **Rubric Scores:** `{'general_coherence': 8.5}`

### Natural Conversation & Etiquette (`TEST_11_NATURAL_CONVERSATION`)
**Expected:** Tutor responds warmly and concisely without unprompted lectures or irrelevant quiz questions.

- **Student:** *"Hey tutor, good morning!"*
- **Raw LLM Output (16.03s):**
  > Good morning! How can I assist you with operating systems today?
- **Rubric Scores:** `{'naturalness_etiquette': 9.5}`

- **Student:** *"Thank you so much, that made total sense!"*
- **Raw LLM Output (18.31s):**
  > I'm glad to hear that! If you have any more questions or need further clarification on any topic, feel free to ask. What would you like to explore next?
- **Rubric Scores:** `{'naturalness_etiquette': 9.5}`

