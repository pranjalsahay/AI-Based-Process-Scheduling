"""
generate_figures_v2.py
Generates clean, high-resolution (300 DPI) Black & White / Monochrome vector-style
flowcharts and diagrams with ZERO TEXT OR ARROW OVERLAPS.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = r"c:\pranjalos\figures"
os.makedirs(OUT_DIR, exist_ok=True)

# Set global matplotlib font styling for clean academic B&W figures
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['text.color'] = '#000000'
plt.rcParams['axes.edgecolor'] = '#000000'
plt.rcParams['axes.linewidth'] = 1.2

def draw_system_architecture():
    """Generates Figure 3.1: High-Level End-to-End System Architecture Flowchart (Spacious & Clean)."""
    fig, ax = plt.subplots(figsize=(11, 9.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 9.5)
    ax.axis('off')

    # Top: Client Layer
    box_client = patches.FancyBboxPatch(
        (1.0, 8.4), 9.0, 0.75,
        boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.8
    )
    ax.add_patch(box_client)
    ax.text(5.5, 8.77, "STUDENT WEB CLIENT INTERFACE", ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(5.5, 8.52, "(Modern HTML5 / CSS3 / Vanilla JavaScript Single-Page Chat Interface)", ha='center', va='center', fontsize=9.0)

    # Arrow Down to API Gateway
    ax.annotate(
        '', xy=(5.5, 7.35), xytext=(5.5, 8.4),
        arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.2, headwidth=6, headlength=7)
    )
    ax.text(5.5, 7.85, "HTTP REST POST /chat  { session_id, message }",
            ha='center', va='center', fontsize=8.5, style='italic',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', lw=0.6))

    # Gateway & Router
    box_api = patches.FancyBboxPatch(
        (1.8, 6.55), 7.4, 0.75,
        boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.5
    )
    ax.add_patch(box_api)
    ax.text(5.5, 6.95, "FASTAPI ASYNCHRONOUS REST GATEWAY & QUERY CLASSIFIER", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(5.5, 6.70, "Pydantic Request Validation • Session State Lookup • Intent Branching", ha='center', va='center', fontsize=8.5)

    # Branch Left Arrow (Numerical)
    ax.annotate(
        '', xy=(2.7, 5.25), xytext=(4.0, 6.55),
        arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.2, headwidth=6, headlength=7)
    )
    ax.text(2.6, 5.9, "Numerical Scheduling\nProblem / Trace", ha='center', va='center', fontsize=8.0, style='italic',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', lw=0.5))

    # Branch Right Arrow (Socratic)
    ax.annotate(
        '', xy=(8.3, 5.25), xytext=(7.0, 6.55),
        arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.2, headwidth=6, headlength=7)
    )
    ax.text(8.4, 5.9, "Conceptual Question /\nInteractive Inquiry", ha='center', va='center', fontsize=8.0, style='italic',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', lw=0.5))

    # Left Box: Deterministic Solver
    box_solver = patches.FancyBboxPatch(
        (0.6, 2.95), 4.4, 2.25,
        boxstyle='round,pad=0.25', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.6
    )
    ax.add_patch(box_solver)
    ax.text(2.8, 4.90, "DETERMINISTIC SIMULATION ENGINE", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(2.8, 4.60, "(app/core/scheduling_solver.py)", ha='center', va='center', fontsize=8.0, style='italic')
    solver_bullets = (
        "• Cycle-by-Cycle Discrete Event Clock Loop\n"
        "• Zero-Hallucination Integer Arithmetic\n"
        "• 11 Algorithms (FCFS, SJF, SRTF, RR, MLFQ, etc.)\n"
        "• Exact Metrics: CT, TAT, WT, RT, Utilization\n"
        "• Automated Monospace ASCII Gantt Generator"
    )
    ax.text(0.9, 3.65, solver_bullets, ha='left', va='center', fontsize=8.5, linespacing=1.4)

    # Right Box: Socratic Engine
    box_socratic = patches.FancyBboxPatch(
        (6.0, 2.95), 4.4, 2.25,
        boxstyle='round,pad=0.25', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.6
    )
    ax.add_patch(box_socratic)
    ax.text(8.2, 4.90, "SOCRATIC PEDAGOGICAL FSM", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(8.2, 4.60, "(app/core/socratic_engine.py)", ha='center', va='center', fontsize=8.0, style='italic')
    socratic_bullets = (
        "• 4-Stage Pedagogical Progression Loop:\n"
        "   Stage 1: Real-Life Analogy / Hook\n"
        "   Stage 2: Intuitive Deduction\n"
        "   Stage 3: Technical Formalization\n"
        "   Stage 4: Verification & Mini Practice\n"
        "• Diagnostic Misconception Evaluator"
    )
    ax.text(6.3, 3.65, socratic_bullets, ha='left', va='center', fontsize=8.5, linespacing=1.3)

    # Prompt Assembler & RAG Layer
    box_llm = patches.FancyBboxPatch(
        (0.6, 1.25), 4.4, 1.35,
        boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.4
    )
    ax.add_patch(box_llm)
    ax.text(2.8, 2.25, "PROMPT ASSEMBLER & LLM GATEWAY", ha='center', va='center', fontsize=9.5, fontweight='bold')
    llm_bullets = (
        "• Context Synthesis (Solver Metrics + State)\n"
        "• Strict Socratic Stage Roleplay Guardrails\n"
        "• Local Ollama / Qwen2.5-7B or OpenAI Engine"
    )
    ax.text(0.9, 1.65, llm_bullets, ha='left', va='center', fontsize=8.0, linespacing=1.3)

    box_rag = patches.FancyBboxPatch(
        (6.0, 1.25), 4.4, 1.35,
        boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.4
    )
    ax.add_patch(box_rag)
    ax.text(8.2, 2.25, "CHROMADB VECTOR RAG KNOWLEDGE STORE", ha='center', va='center', fontsize=9.5, fontweight='bold')
    rag_bullets = (
        "• 170+ Curated OS Scheduling Chunks\n"
        "• Silberschatz & Arpaci-Dusseau Grounding\n"
        "• Semantic Cosine Similarity Lookup (k=3)"
    )
    ax.text(6.3, 1.65, rag_bullets, ha='left', va='center', fontsize=8.0, linespacing=1.3)

    # Horizontal connector between RAG and LLM
    ax.annotate('', xy=(5.0, 1.9), xytext=(6.0, 1.9),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(5.5, 2.1, "Grounding\nPassages", ha='center', va='center', fontsize=7.5, style='italic')

    # Down from Solver to LLM
    ax.annotate('', xy=(2.8, 2.65), xytext=(2.8, 2.95),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))

    # Down from Socratic to RAG
    ax.annotate('', xy=(8.2, 2.65), xytext=(8.2, 2.95),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))

    # Bottom: SQLite Layer
    box_db = patches.FancyBboxPatch(
        (0.6, 0.15), 9.8, 0.75,
        boxstyle='square,pad=0.15', facecolor='#F5F5F5', edgecolor='#000000', linewidth=1.5
    )
    ax.add_patch(box_db)
    ax.text(5.5, 0.58, "SQLITE3 RELATIONAL PERSISTENCE & CONVERSATION MEMORY LAYER", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(5.5, 0.32, "Tables: sessions • chat_history • tutoring_states • misconception_logs • quiz_evaluations (Normalized 3NF)", ha='center', va='center', fontsize=8.0)

    # Down arrows to SQLite
    ax.annotate('', xy=(2.8, 0.93), xytext=(2.8, 1.25),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.annotate('', xy=(8.2, 0.93), xytext=(8.2, 1.25),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "arch_flowchart_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

def draw_process_state():
    """Generates Figure 3.2: Operating Systems Process State Transition Lifecycle (Curved & Spacious)."""
    fig, ax = plt.subplots(figsize=(11, 6.0), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.0)
    ax.axis('off')

    def draw_state_box(x, y, r, label, sub=""):
        circle = patches.Circle((x, y), r, facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.8)
        ax.add_patch(circle)
        ax.text(x, y + 0.12, label, ha='center', va='center', fontsize=10.5, fontweight='bold')
        if sub:
            ax.text(x, y - 0.20, sub, ha='center', va='center', fontsize=8.0, style='italic')

    # 5 Process States
    draw_state_box(1.2, 3.6, 0.70, "NEW", "Created")
    draw_state_box(4.0, 3.6, 0.85, "READY", "In Memory")
    draw_state_box(8.0, 3.6, 0.85, "RUNNING", "On CPU Core")
    draw_state_box(10.2, 3.6, 0.65, "TERMINATED", "Exit")
    draw_state_box(6.0, 1.1, 0.85, "WAITING", "Blocked (I/O)")

    # 1. New -> Ready
    ax.annotate(
        '', xy=(3.12, 3.6), xytext=(1.92, 3.6),
        arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7)
    )
    ax.text(2.52, 3.90, "Admitted\n(Long-Term Scheduler)", ha='center', va='bottom', fontsize=8.0, fontweight='bold')

    # 2. Ready -> Running (Top Curved Arrow)
    ax.annotate(
        '', xy=(7.25, 4.05), xytext=(4.75, 4.05),
        arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7,
                        connectionstyle="arc3,rad=-0.25")
    )
    ax.text(6.0, 4.85, "Scheduler Dispatch\n(Short-Term CPU Scheduler)", ha='center', va='center', fontsize=8.5, fontweight='bold',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', lw=0.6))

    # 3. Running -> Ready (Bottom Curved Arrow - Preemption)
    ax.annotate(
        '', xy=(4.75, 3.15), xytext=(7.25, 3.15),
        arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7,
                        connectionstyle="arc3,rad=-0.25")
    )
    ax.text(6.0, 2.35, "Timer Interrupt / Quantum Expired\n(Preemption in RR, SRTF, Priority)", ha='center', va='center', fontsize=8.0,
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', lw=0.6))

    # 4. Running -> Terminated
    ax.annotate(
        '', xy=(9.52, 3.6), xytext=(8.88, 3.6),
        arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7)
    )
    ax.text(9.20, 3.90, "Exit\nComplete", ha='center', va='bottom', fontsize=8.0, fontweight='bold')

    # 5. Running -> Waiting (Down-left)
    ax.annotate(
        '', xy=(6.75, 1.55), xytext=(7.50, 2.85),
        arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7)
    )
    ax.text(7.60, 1.95, "I/O or Event Wait\n(System Call)", ha='left', va='center', fontsize=8.0)

    # 6. Waiting -> Ready (Up-left)
    ax.annotate(
        '', xy=(4.50, 2.85), xytext=(5.25, 1.55),
        arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7)
    )
    ax.text(4.40, 1.95, "I/O or Event\nCompletion", ha='right', va='center', fontsize=8.0)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "process_state_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

def draw_socratic_fsm():
    """Generates Figure 4.3: Socratic Pedagogical Finite State Machine (Clean Non-Overlapping Layout)."""
    fig, ax = plt.subplots(figsize=(11.5, 7.0), dpi=300)
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 7.0)
    ax.axis('off')

    def draw_stage(x, y, w, h, s_num, s_title, s_desc):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.6)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.30, s_num, ha='center', va='center', fontsize=10.0, fontweight='bold')
        ax.text(x + w/2, y + h - 0.65, s_title, ha='center', va='center', fontsize=9.0, fontweight='bold')
        ax.text(x + w/2, y + (h - 0.9)/2, s_desc, ha='center', va='center', fontsize=8.0, linespacing=1.3)

    # 4 Stages
    draw_stage(0.5, 3.8, 2.3, 2.2, "STAGE 1", "ANALOGY / HOOK",
               "Presents a relatable\nreal-life scenario\n(e.g., shared console,\nbakery ticket queue)\nto awaken intuition.")

    draw_stage(3.3, 3.8, 2.3, 2.2, "STAGE 2", "INTUITIVE DEDUCTION",
               "Presents guided questions\nprompting the student\nto deduce the core\ncomputational rule\n(e.g., quantum effect).")

    draw_stage(6.1, 3.8, 2.3, 2.2, "STAGE 3", "FORMAL DEFINITION",
               "Synthesizes deduction\ninto formal Operating\nSystems terminology,\nequations, and kernel\nperformance metrics.")

    draw_stage(8.9, 3.8, 2.2, 2.2, "STAGE 4", "VERIFICATION",
               "Administers an\ninteractive practice\nproblem to verify\nsolid understanding\nand close mastery.")

    # Forward arrows between stages (Placed clearly in gaps)
    def fwd_arrow(x1, x2, label):
        ax.annotate('', xy=(x2, 4.9), xytext=(x1, 4.9),
                    arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7))
        ax.text((x1+x2)/2, 5.15, label, ha='center', va='bottom', fontsize=7.5, style='italic')

    fwd_arrow(2.82, 3.28, "Correct\nIntuition")
    fwd_arrow(5.62, 6.08, "Rule\nDeduced")
    fwd_arrow(8.42, 8.88, "Concept\nMastered")

    # Diagnostic Misconception Evaluator below
    box_diag = patches.FancyBboxPatch((2.2, 0.8), 7.2, 1.8, boxstyle='round,pad=0.25', facecolor='#F8F8F8', edgecolor='#000000', linewidth=1.5)
    ax.add_patch(box_diag)
    ax.text(5.8, 2.25, "DIAGNOSTIC MISCONCEPTION EVALUATOR & REMEDIATION LOOP", ha='center', va='center', fontsize=9.5, fontweight='bold')
    diag_text = (
        "• Automatically scans student text for common conceptual pitfalls\n"
        "• Detects Turnaround Time vs. Waiting Time confusion, tie-breaking errors, or FCFS starvation myths\n"
        "• Intercepts misconception with targeted cognitive feedback and gracefully re-prompts the active stage"
    )
    ax.text(2.6, 1.45, diag_text, ha='left', va='center', fontsize=8.0, linespacing=1.35)

    # Downward arrow to Misconception Evaluator
    ax.annotate('', xy=(3.8, 2.65), xytext=(3.8, 3.75),
                arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7))
    ax.text(3.4, 3.20, "Misconception\nIdentified", ha='right', va='center', fontsize=7.5, fontweight='bold')

    # Upward remediation arrow
    ax.annotate('', xy=(7.8, 3.75), xytext=(7.8, 2.65),
                arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7))
    ax.text(8.2, 3.20, "Remediated\nRe-Prompt", ha='left', va='center', fontsize=7.5, fontweight='bold')

    # Direct Answer Override Line across top (High above everything)
    ax.annotate('', xy=(9.8, 6.45), xytext=(1.6, 6.45),
                arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7))
    ax.plot([1.6, 1.6], [6.02, 6.45], color='#000000', lw=1.2)
    ax.plot([9.8, 9.8], [6.45, 6.02], color='#000000', lw=1.2)
    ax.text(5.7, 6.65, "EXPLICIT DIRECT-ANSWER OVERRIDE (e.g., 'Just give me the definition of Round Robin')",
            ha='center', va='bottom', fontsize=8.0, fontweight='bold', style='italic',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', lw=0.6))

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "socratic_fsm_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

def draw_solver_pipeline():
    """Generates Figure 4.1: Deterministic Scheduling Simulation Engine Pipeline (Spacious)."""
    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.2)
    ax.axis('off')

    def draw_step(x, y, w, h, title, sub):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.40, title, ha='center', va='center', fontsize=9.0, fontweight='bold')
        ax.text(x + w/2, y + (h - 0.5)/2, sub, ha='center', va='center', fontsize=8.0, linespacing=1.3)

    draw_step(0.4, 1.1, 1.8, 2.0, "1. INPUT PARSER", "Extracts Process\nSpecs: PID, Arrival,\nBurst, Priority,\nQuantum, Deadlines")
    draw_step(2.6, 1.1, 1.8, 2.0, "2. CLOCK LOOP", "Discrete event cycle\nadvancement:\nt += 1 or slice.\nMaintains timeline.")
    draw_step(4.8, 1.1, 1.8, 2.0, "3. QUEUE MANAGER", "Enqueue arrivals;\nsort by algorithm\npolicy; check for\npreemption triggers.")
    draw_step(7.0, 1.1, 1.8, 2.0, "4. METRIC ENGINE", "Compute exact integer\nmetrics:\nCT, TAT = CT - AT,\nWT = TAT - BT, RT.")
    draw_step(9.1, 1.1, 1.6, 2.0, "5. ASCII GANTT", "Format clean\nmonospace timeline\nbar with boundaries\nand legend.")

    def arr(x1, x2):
        ax.annotate('', xy=(x2, 2.1), xytext=(x1, 2.1),
                    arrowprops=dict(facecolor='#000000', width=1.2, headwidth=6, headlength=7))

    arr(2.22, 2.58)
    arr(4.42, 4.78)
    arr(6.62, 6.98)
    arr(8.82, 9.08)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "solver_pipeline_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

def draw_gantt_comparison():
    """Generates Figure 4.2: Comparative Scheduling Gantt Chart (Clean Dedicated Axis & No Overlaps)."""
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    ax.set_xlim(-1.2, 12.8)
    ax.set_ylim(-0.8, 4.8)
    ax.axis('off')

    ax.text(5.5, 4.5, "BENCHMARK WORKLOAD: P1 (AT=0, BT=5), P2 (AT=1, BT=3), P3 (AT=2, BT=1), P4 (AT=3, BT=2)",
            ha='center', va='center', fontsize=9.5, fontweight='bold')

    def draw_clean_timeline(y, label, blocks, metrics_str):
        # Algorithm Label on Left
        ax.text(-1.0, y + 0.35, label, ha='left', va='center', fontsize=9.5, fontweight='bold')

        # Blocks
        for start, end, pid in blocks:
            w = end - start
            rect = patches.Rectangle((start, y + 0.1), w, 0.55, facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.4)
            ax.add_patch(rect)
            ax.text(start + w/2, y + 0.375, pid, ha='center', va='center', fontsize=9.0, fontweight='bold')

        # Timeline Axis below
        ax.plot([0, 11], [y, y], color='#000000', lw=1.2)

        # Unique boundary ticks only (eliminates duplicate numbers)
        all_pts = sorted(list(set([0] + [b[1] for b in blocks])))
        for pt in all_pts:
            ax.plot([pt, pt], [y - 0.08, y], color='#000000', lw=1.2)
            ax.text(pt, y - 0.22, str(pt), ha='center', va='top', fontsize=8.0)

        # Metrics box on the right
        box_met = patches.FancyBboxPatch(
            (11.3, y - 0.05), 1.4, 0.75,
            boxstyle='square,pad=0.1', facecolor='#F8F8F8', edgecolor='#000000', linewidth=1.0
        )
        ax.add_patch(box_met)
        ax.text(12.0, y + 0.32, metrics_str, ha='center', va='center', fontsize=7.5, linespacing=1.3)

    # 1. FCFS: P1(0-5), P2(5-8), P3(8-9), P4(9-11)
    draw_clean_timeline(3.2, "FCFS", [(0, 5, 'P1'), (5, 8, 'P2'), (8, 9, 'P3'), (9, 11, 'P4')], "Avg WT: 4.00 ms\nAvg TAT: 6.75 ms")

    # 2. SRTF (Preemptive): P1(0-1), P2(1-2), P3(2-3), P2(3-5), P4(5-7), P1(7-11)
    draw_clean_timeline(1.8, "SRTF", [(0, 1, 'P1'), (1, 2, 'P2'), (2, 3, 'P3'), (3, 5, 'P2'), (5, 7, 'P4'), (7, 11, 'P1')], "Avg WT: 2.25 ms\nAvg TAT: 5.00 ms")

    # 3. Round Robin (q=2): P1(0-2), P2(2-4), P3(4-5), P4(5-7), P1(7-9), P2(9-10), P1(10-11)
    draw_clean_timeline(0.4, "RR (q=2)", [(0, 2, 'P1'), (2, 4, 'P2'), (4, 5, 'P3'), (5, 7, 'P4'), (7, 9, 'P1'), (9, 10, 'P2'), (10, 11, 'P1')], "Avg WT: 3.25 ms\nAvg TAT: 6.00 ms")

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "gantt_comparison_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

if __name__ == '__main__':
    draw_system_architecture()
    draw_process_state()
    draw_socratic_fsm()
    draw_solver_pipeline()
    draw_gantt_comparison()
    print("All non-overlapping figures regenerated successfully!")
