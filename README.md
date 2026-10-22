# SchedulAI — An Intelligent Socratic Tutor for CPU Process Scheduling

SchedulAI is a locally runnable, adaptive AI tutoring application built to teach Operating Systems principles with an initial deep specialization in CPU process scheduling.

Unlike generic question-answering bots, SchedulAI implements an adaptive **Socratic tutoring cycle**:
```
ASSESS → QUESTION → EVALUATE → EXPLAIN → PRACTISE → VERIFY → ADAPT
```

The system assesses a learner's prerequisite knowledge, asks one targeted question at a time, identifies partial understanding and misconceptions, provides scaffolded hints, explains concepts when requested, and uses an independent, deterministic Python scheduling engine to verify student calculations.

---

## 1. Key Features

- **6 Explicit Pedagogical Tutoring Modes**:
  1. **Diagnostic Mode**: Assesses baseline knowledge using one targeted question per turn.
  2. **Socratic Mode**: Guides discovery through progressive questioning and hints without prematurely revealing answers.
  3. **Explanation Mode**: Triggers when the student says "explain directly" or "I don't understand," delivering a 6-part structured lesson (Intuitive Analogy, Formal Definition, Mechanism, Worked Example, Misconception, Check Question).
  4. **Guided Practice Mode**: Guides students step-by-step through numerical scheduling problems, validating intermediate decisions.
  5. **Independent Practice Mode**: Presents unassisted scheduling problems and evaluates full submissions against authoritative ground truth.
  6. **Revision Mode**: Focuses specifically on previously identified misconceptions and weak concepts.

- **Deterministic CPU Scheduling Engine**:
  - Implements **FCFS**, non-preemptive **SJF**, preemptive **SRTF**, **Priority** (non-preemptive and preemptive with configurable priority convention), and **Round Robin** (with exact quantum-boundary arrival tie-breaking rules).
  - Computes completion time ($CT$), turnaround time ($TAT = CT - AT$), waiting time ($WT = TAT - BT$), response time ($RT = \text{FirstStart} - AT$), averages, CPU utilization, throughput, and idle intervals.
  - Generates text/ASCII Gantt charts with aligned timeline boundaries.
  - Multi-algorithm side-by-side benchmark comparison.

- **Production RAG Pipeline**:
  - Built on **ChromaDB** and SentenceTransformers (`all-MiniLM-L6-v2`).
  - Supports Markdown (`.md`), text (`.txt`), PDF (`.pdf`), and Word (`.docx`).
  - Chunks text while preserving section headings and applying configurable overlap.
  - Idempotent upsert ensuring zero chunk duplication upon re-indexing.
  - Grounded citations displayed in the chat interface.

- **Adaptive Learner State & Persistence**:
  - SQLite + SQLAlchemy persistence tracking student proficiency, mastered concepts, review concepts, questions attempted, accuracy, and recent misconceptions.
  - Dynamic 3-tier difficulty: **Beginner**, **Intermediate**, and **Advanced** with automatic promotion and regression logic.

- **Minimalist ChatGPT-Style Frontend**:
  - Clean HTML5, CSS3, and Vanilla JavaScript UI.
  - Sidebar with session switcher, topic selector, and tutoring mode indicators.
  - Interactive **Scheduling Sandbox** modal allowing direct process configuration and live Gantt chart execution.
  - Collapsible learner proficiency drawer with live mastery progress bar.

---

## 2. Architecture & Directory Structure

```text
schedulai/
├── app/
│   ├── main.py                  # FastAPI application entry point & static file mount
│   ├── config.py                # Environment configuration & hardware inspection
│   ├── api/                     # REST API routers
│   │   ├── health.py            # Health check for Ollama, ChromaDB, DB, and RAM
│   │   ├── chat.py              # Conversational turns & tutoring cycle
│   │   ├── sessions.py          # Session creation, listing, detail, reset, delete
│   │   ├── progress.py          # Learner proficiency metrics & mastery score
│   │   ├── scheduling.py        # Deterministic scheduling engine endpoints
│   │   └── knowledge.py         # Knowledge base inspection & RAG querying
│   ├── core/                    # Tutoring & LLM logic
│   │   ├── llm_client.py        # Ollama local API integration with fallback
│   │   ├── prompt_builder.py    # Socratic prompt assembly with RAG & engine data
│   │   ├── response_parser.py   # Pydantic JSON validation & repair
│   │   ├── learner_model.py     # Mastery heuristics & adaptive difficulty
│   │   └── tutoring_engine.py   # Master tutoring orchestrator
│   ├── rag/                     # Retrieval-Augmented Generation
│   │   ├── chunking.py          # Section-aware overlapping text splitter
│   │   ├── ingestion.py         # Multi-format document parser
│   │   ├── embeddings.py        # SentenceTransformers / Chroma ONNX embedder
│   │   ├── retriever.py         # ChromaDB persistent vector search
│   │   └── citations.py         # Citation formatter & prompt protector
│   ├── scheduling/              # Deterministic CPU scheduling engine
│   │   ├── models.py            # Process, GanttSegment, and SchedulingResult
│   │   ├── validation.py        # Input verification (negative/zero burst, ties)
│   │   ├── metrics.py           # Invariant calculations (CT, TAT, WT, RT, averages)
│   │   ├── fcfs.py              # First-Come, First-Served implementation
│   │   ├── sjf.py               # Non-preemptive Shortest Job First
│   │   ├── srtf.py              # Preemptive Shortest Remaining Time First
│   │   ├── priority.py          # Priority scheduling (preemptive & non-preemptive)
│   │   ├── round_robin.py       # Round Robin with quantum boundary rules
│   │   └── gantt_renderer.py    # ASCII Gantt chart renderer
│   ├── database/                # SQLite Persistence layer
│   │   ├── connection.py        # SQLAlchemy engine and session factory
│   │   ├── models.py            # Session, Message, LearnerState, PracticeAttempt
│   │   └── repository.py        # Data access repository (CRUD)
│   ├── schemas/                 # Pydantic interface contracts
│   │   ├── chat.py              # ChatRequest, ChatResponse, TutorStructuredResponse
│   │   ├── session.py           # Session models
│   │   ├── scheduling.py        # ProcessInput, SchedulingCalculateRequest
│   │   └── learner.py           # LearnerProgressResponse
│   └── evaluation/              # Benchmark evaluation datasets
│       ├── tutoring_cases.json  # 8 benchmark pedagogical intent test cases
│       └── retrieval_cases.json # 6 benchmark RAG retrieval test cases
├── frontend/                    # Web Interface
│   ├── index.html               # Semantic HTML5 UI layout
│   ├── styles.css               # Modern dark-mode styling
│   └── app.js                   # Client-side reactivity & API integration
├── knowledge_base/              # Authoritative course starter material
│   ├── fundamentals/            # Process vs program, PCB, states, scheduler, dispatcher
│   ├── fcfs/                    # FCFS mechanism & Convoy Effect
│   ├── sjf/                     # Non-preemptive SJF & optimality proof
│   ├── srtf/                    # Preemptive SRTF mechanism & preemption rules
│   ├── priority/                # Priority conventions, starvation, and aging
│   ├── round_robin/             # Time quantum selection & queue rules
│   ├── metrics/                 # Mathematical formulas for AT, BT, CT, TAT, WT, RT
│   ├── numerical_examples/      # Reference worked scheduling problems
│   └── misconceptions/          # Common OS student misconceptions
├── scripts/
│   ├── ingest_knowledge.py      # CLI script for indexing course documents
│   └── evaluate_tutor.py        # Automated RAG & intent evaluation runner
├── tests/                       # Automated Pytest suite (30 passing tests)
│   ├── test_fcfs.py
│   ├── test_sjf.py
│   ├── test_srtf.py
│   ├── test_priority.py
│   ├── test_round_robin.py
│   ├── test_metrics.py
│   ├── test_rag.py
│   ├── test_api.py
│   └── test_tutoring.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## 3. Installation & Setup

### Prerequisites
- Python 3.10 or 3.11
- [Ollama](https://ollama.com/) installed and running locally
- Recommended RAM: 8 GB or higher (16 GB for 14B models; 8 GB for 7B/8B or 3B models)

### Step 1: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 2: Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```
Default configuration:
```ini
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="qwen2.5:14b-instruct-q3_K_M"
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
CHROMA_PERSIST_DIRECTORY="./data/chroma"
DATABASE_URL="sqlite:///./data/schedulai.db"
```

### Step 3: Download Local LLM Model
Ensure Ollama is running (`ollama serve`), then pull your preferred model:
```bash
# Recommended for 16GB RAM:
ollama pull qwen2.5:14b-instruct-q3_K_M

# Or lightweight alternative for 8GB RAM / fast CPU:
ollama pull llama3.1:latest
# or
ollama pull qwen2.5:7b
```

### Step 4: Ingest Course Knowledge Base
Populate ChromaDB with the included course documents:
```bash
python scripts/ingest_knowledge.py --kb-dir knowledge_base --chroma-dir data/chroma
```
Expected output:
```text
--- Ingestion Summary ---
Files processed: 10
Chunks indexed:  49
Distinct document titles in index: 10
Ingestion completed successfully!
```

---

## 4. Running the Application

Start the FastAPI application with Uvicorn:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to:
- **Interactive Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **System Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 5. Automated Testing & Evaluation

### Run Full Pytest Suite
Execute all 30 automated tests covering scheduling algorithms, metrics, edge cases, RAG ingestion, API endpoints, and tutoring behavior:
```bash
python -m pytest tests/ -v
```
All 30 unit and integration tests pass cleanly in under 7 seconds.

### Run System Evaluation Benchmark
Run the automated evaluation benchmark on retrieval Hit@K and pedagogical intent alignment:
```bash
python scripts/evaluate_tutor.py
```
Benchmark Results:
```text
================ FINAL REPORT ================
Retrieval Top-3 Document Hit Rate: 100.0% (6/6)
Keyword Coverage Rate:             100.0% (6/6)
Tutoring Mode Intent Accuracy:     100.0% (8/8)
==============================================
```

---

## 6. Demonstration Conversations

### Scenario 1: Socratic Diagnostic & Misconception Correction
```text
Student: "Test my knowledge on CPU scheduling."

SchedulAI (Diagnostic Mode | Action: ask_question):
"Welcome! Let's start with a foundational concept: When the operating system manages running applications, what is the core difference between a passive program stored on disk and an active process in memory?"

Student: "They are the same thing, just one is in RAM."

SchedulAI (Socratic Mode | Action: provide_hint | Misconception: "Viewing program and process as identical except for storage location"):
"💡 Misconception Detected: A program is merely a passive file containing binary instructions.
Think about what extra execution context the operating system must allocate once execution begins—such as CPU registers, the Program Counter, and memory segments. What specific kernel structure tracks this state?"

Student: "The Process Control Block (PCB) with stack, heap, and registers."

SchedulAI (Socratic Mode | Action: ask_question | Concept Mastered: "process_pcb_state"):
"Exactly right! The PCB maintains the process context. Now, once a process is loaded into memory ready to run, in which queue does it wait for CPU allocation?"
```

### Scenario 2: Explicit Explanation Request (6-Part Direct Instruction)
```text
Student: "I don't understand how Round Robin works. Please just explain it directly to me."

SchedulAI (Explanation Mode | Action: explain_concept):
"1. Intuitive Explanation: Imagine a chess coach playing 10 students simultaneously, spending exactly 30 seconds at each board before moving to the next.

2. Formal Definition: Round Robin (RR) is a preemptive scheduling policy where the CPU is allocated to ready processes in FIFO order for a bounded slice called a time quantum (q).

3. How It Works:
   - Processes wait in a circular ready queue.
   - The scheduler dispatches the head process and sets an interrupt timer for q.
   - If the burst <= q, the process releases the CPU and terminates.
   - If the burst > q, a clock interrupt fires, context switch occurs, and the process is appended to the tail of the ready queue.

4. Worked Example:
   Processes P1 (BT=5) and P2 (BT=3) arrive at t=0 with quantum q=2:
   Timeline: [P1: 0-2] [P2: 2-4] [P1: 4-6] [P2: 6-7 (finish)] [P1: 7-8 (finish)].

5. Common Misconception: Increasing the time quantum does not always improve performance. If q is too large, Round Robin degrades into FCFS with high response times.

6. Understanding Check: If three processes have bursts 4, 4, 4 with quantum q=10, does any preemption occur?"
```

### Scenario 3: Deterministic Numerical Problem Solving
Given processes:
- $P_1$: Arrival = $0$, Burst = $8$
- $P_2$: Arrival = $1$, Burst = $4$
- $P_3$: Arrival = $2$, Burst = $9$
- $P_4$: Arrival = $3$, Burst = $5$

Algorithm: **Shortest Remaining Time First (SRTF)**

Verified Gantt Chart Output:
```text
+-------+-------+-------+-------+-------+
|  P1   |  P2   |  P4   |  P1   |  P3   |
+-------+-------+-------+-------+-------+
0       1       5       10      17      26
```

Metric Calculations:
| Process | Arrival Time | Burst Time | Completion Time | Turnaround ($CT - AT$) | Waiting ($TAT - BT$) | Response Time |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **P1** | 0 | 8 | 17 | 17 | 9 | 0 |
| **P2** | 1 | 4 | 5 | 4 | 0 | 0 |
| **P3** | 2 | 9 | 26 | 24 | 15 | 15 |
| **P4** | 3 | 5 | 10 | 7 | 2 | 2 |

- **Average Turnaround Time**: $(17 + 4 + 24 + 7) / 4 = 13.0$
- **Average Waiting Time**: $(9 + 0 + 15 + 2) / 4 = 6.5$
- **Average Response Time**: $(0 + 0 + 15 + 2) / 4 = 4.25$
- **CPU Utilization**: $100.0\%$

---

## 7. Known Limitations & Future Roadmap

- **Model Sizing on CPU**: A 14B model (`qwen2.5:14b-instruct-q3_K_M`) on pure CPU inference typically produces 2–4 tokens/second. For faster local response times on lightweight laptops, use `qwen2.5:7b` or `llama3.1:latest`.
- **Course Scope**: SchedulAI currently focuses exclusively on CPU Process Scheduling. Future releases will expand modules to:
  - Process Synchronization (Semaphores, Mutexes, Monitors, Classical IPC problems)
  - Deadlocks (Banker's Algorithm, Resource Allocation Graphs)
  - Memory Management (Paging, Page Replacement Algorithms: FIFO, LRU, Optimal)
  - File Systems (Allocation methods, Inodes, Disk Scheduling).
