"""
generate_figures.py
Generates clean, high-resolution (300 DPI) Black & White / Monochrome vector-style
flowcharts and diagrams for the SchedulAI Operating Systems Laboratory Mini Project Report.
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
    """Generates Figure 3.1: High-Level End-to-End System Architecture Flowchart."""
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Helper to draw box
    def draw_box(x, y, w, h, text, title=None, style='round,pad=0.2', lw=1.5):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=style,
            facecolor='#FFFFFF',
            edgecolor='#000000',
            linewidth=lw
        )
        ax.add_patch(box)
        if title:
            ax.text(x + w/2, y + h - 0.25, title, ha='center', va='center', fontsize=9.5, fontweight='bold')
            ax.text(x + w/2, y + (h - 0.25)/2, text, ha='center', va='center', fontsize=8.5)
        else:
            ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=9, fontweight='bold' if '\n' not in text else 'normal')

    # Helper to draw arrows
    def draw_arrow(x1, y1, x2, y2, label=None, ha='center', va='bottom'):
        ax.annotate(
            '', xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.0, headwidth=6, headlength=7)
        )
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 0.08, label, ha=ha, va=va, fontsize=8, style='italic')

    # Top: Client
    draw_box(1.5, 7.0, 7.0, 0.7, "STUDENT WEB CLIENT (Modern HTML5 / CSS3 / Vanilla JS Interface)", lw=1.8)

    # API Gateway
    draw_box(2.0, 5.7, 6.0, 0.7, "FASTAPI ASYNCHRONOUS REST GATEWAY (Uvicorn / Starlette)", lw=1.5)
    draw_arrow(4.5, 7.0, 4.5, 6.4, "HTTP POST /chat {session_id, message}")
    draw_arrow(5.5, 6.4, 5.5, 7.0, "JSON Response {reply, state, gantt}")

    # Intent Classifier
    draw_box(2.5, 4.4, 5.0, 0.65, "INTENT & QUERY CLASSIFIER / TOPIC ROUTER", lw=1.5)
    draw_arrow(5.0, 5.7, 5.0, 5.05, "User Prompt")

    # Branch Left: Deterministic Solver
    draw_box(0.5, 2.5, 3.8, 1.3,
             "• Cycle-by-Cycle Execution\n• Exact Integer Arithmetic\n• CT, TAT, WT, RT Formulas\n• Monospace ASCII Gantt",
             title="DETERMINISTIC SOLVER ENGINE", lw=1.5)
    draw_arrow(3.5, 4.4, 2.4, 3.8, "Numerical Problem / Trace")

    # Branch Right: Socratic Dialogue Machine
    draw_box(5.7, 2.5, 3.8, 1.3,
             "• Stage 1: Real-Life Analogy\n• Stage 2: Intuitive Deduction\n• Stage 3: Technical Formalization\n• Stage 4: Verification & Practice",
             title="SOCRATIC PEDAGOGICAL FSM", lw=1.5)
    draw_arrow(6.5, 4.4, 7.6, 3.8, "Concept Query / Guided Inquiry")

    # Middle Right: Vector RAG
    draw_box(5.7, 0.9, 3.8, 1.0,
             "• 170+ Curated OS Chunks\n• Silberschatz & Arpaci-Dusseau\n• Semantic Vector Cosine Match",
             title="CHROMADB VECTOR RAG STORE", lw=1.2)
    draw_arrow(7.6, 2.5, 7.6, 1.9, "Retrieve Grounding")
    draw_arrow(7.3, 1.9, 7.3, 2.5)

    # Prompt Assembler & LLM Gateway
    draw_box(0.5, 0.9, 3.8, 1.0,
             "• Dynamic Prompt Synthesis\n• Strict Role & Stage Guardrails\n• Misconception Interception",
             title="PROMPT ASSEMBLER & LLM ENGINE", lw=1.5)
    draw_arrow(2.4, 2.5, 2.4, 1.9, "Exact Metrics Output")
    draw_arrow(5.7, 1.4, 4.3, 1.4, "Grounding Chunks")

    # Relational Storage Bar
    box_db = patches.FancyBboxPatch(
        (0.5, 0.05), 9.0, 0.55,
        boxstyle='square,pad=0.1',
        facecolor='#F5F5F5',
        edgecolor='#000000',
        linewidth=1.2
    )
    ax.add_patch(box_db)
    ax.text(5.0, 0.32, "SQLITE3 RELATIONAL MEMORY LAYER (Sessions, Chat History, Socratic Stage Logs, Misconception Audits)",
            ha='center', va='center', fontsize=8.5, fontweight='bold')

    draw_arrow(2.4, 0.9, 2.4, 0.6)
    draw_arrow(7.6, 0.9, 7.6, 0.6)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "arch_flowchart_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

def draw_process_state():
    """Generates Figure 3.2: Operating Systems Process State Transition Lifecycle."""
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 4.5)
    ax.axis('off')

    def draw_state(x, y, r, label):
        circle = patches.Circle((x, y), r, facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.8)
        ax.add_patch(circle)
        ax.text(x, y, label, ha='center', va='center', fontsize=9.5, fontweight='bold')

    # States
    draw_state(1.0, 2.5, 0.65, "NEW")
    draw_state(3.2, 2.5, 0.75, "READY")
    draw_state(5.8, 2.5, 0.75, "RUNNING")
    draw_state(8.0, 2.5, 0.65, "TERMINATED")
    draw_state(4.5, 0.8, 0.75, "WAITING\n(BLOCKED)")

    # Arrows
    # New -> Ready
    ax.annotate('', xy=(2.45, 2.5), xytext=(1.65, 2.5),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(2.05, 2.65, "Admitted\n(Long-Term)", ha='center', fontsize=7.5)

    # Ready -> Running (Dispatch)
    ax.annotate('', xy=(5.05, 2.7), xytext=(3.95, 2.7),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(4.5, 2.9, "Scheduler Dispatch\n(Short-Term CPU)", ha='center', fontsize=7.5)

    # Running -> Ready (Interrupt / Preemption)
    ax.annotate('', xy=(3.95, 2.3), xytext=(5.05, 2.3),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(4.5, 1.95, "Interrupt / Quantum Expired\n(Preemption)", ha='center', fontsize=7.5)

    # Running -> Terminated
    ax.annotate('', xy=(7.35, 2.5), xytext=(6.55, 2.5),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(6.95, 2.65, "Exit /\nFinished", ha='center', fontsize=7.5)

    # Running -> Waiting
    ax.annotate('', xy=(5.1, 1.2), xytext=(5.6, 1.8),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(5.9, 1.3, "I/O or Event\nWait", ha='center', fontsize=7.5)

    # Waiting -> Ready
    ax.annotate('', xy=(3.4, 1.8), xytext=(3.9, 1.2),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(3.1, 1.3, "I/O or Event\nCompletion", ha='center', fontsize=7.5)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "process_state_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

def draw_socratic_fsm():
    """Generates Figure 4.1: Socratic Pedagogical Finite State Machine (FSM)."""
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.axis('off')

    def draw_stage(x, y, w, h, s_num, s_title, s_desc):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.25, s_num, ha='center', va='center', fontsize=9.0, fontweight='bold')
        ax.text(x + w/2, y + h - 0.55, s_title, ha='center', va='center', fontsize=8.5, fontweight='bold')
        ax.text(x + w/2, y + (h - 0.7)/2, s_desc, ha='center', va='center', fontsize=7.5)

    # Stage 1 to 4
    draw_stage(0.3, 3.2, 2.0, 1.8, "STAGE 1", "ANALOGY / HOOK", "Presents relatable\nreal-life scenario\n(e.g., canteen queue,\nshared console)")
    draw_stage(2.7, 3.2, 2.0, 1.8, "STAGE 2", "INTUITIVE DEDUCTION", "Guides student to\ndeduce algorithmic\nrule independently\n(e.g. quantum effect)")
    draw_stage(5.1, 3.2, 2.0, 1.8, "STAGE 3", "FORMAL DEFINITION", "Presents formal OS\ndefinition, formulas,\nand kernel-level\ntrade-offs")
    draw_stage(7.5, 3.2, 2.0, 1.8, "STAGE 4", "VERIFICATION", "Administers practice\nquestion or mini quiz\nto verify mastery\nand closure")

    # Forward arrows
    def fwd_arrow(x1, x2, y=4.1):
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))

    fwd_arrow(2.3, 2.7)
    fwd_arrow(4.7, 5.1)
    fwd_arrow(7.1, 7.5)

    # Misconception loop below
    box_diag = patches.FancyBboxPatch((2.7, 1.0), 4.4, 1.2, boxstyle='round,pad=0.2', facecolor='#F5F5F5', edgecolor='#000000', linewidth=1.4)
    ax.add_patch(box_diag)
    ax.text(4.9, 1.85, "DIAGNOSTIC MISCONCEPTION EVALUATOR", ha='center', fontsize=8.5, fontweight='bold')
    ax.text(4.9, 1.35, "Detects classic errors (e.g. TAT vs WT confusion, tie-break misses)\nProvides instant targeted cognitive feedback & re-prompts stage", ha='center', fontsize=7.5)

    # Down arrow from Stage 2 & 3 to Misconception
    ax.annotate('', xy=(3.7, 2.2), xytext=(3.7, 3.2),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(3.3, 2.7, "Incorrect\nResponse", ha='center', fontsize=7.0)

    ax.annotate('', xy=(6.1, 3.2), xytext=(6.1, 2.2),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.text(6.6, 2.7, "Remediated\nRe-prompt", ha='center', fontsize=7.0)

    # Direct Answer Override Line across top
    ax.annotate('', xy=(8.5, 5.0), xytext=(1.3, 5.0),
                arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))
    ax.plot([1.3, 1.3], [5.0, 5.0], color='#000000')
    ax.text(4.9, 5.15, "EXPLICIT DIRECT ANSWER OVERRIDE (e.g. 'Just give me the definition of Round Robin')",
            ha='center', fontsize=7.5, fontweight='bold', style='italic')

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "socratic_fsm_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

def draw_solver_pipeline():
    """Generates Figure 4.2: Deterministic Scheduling Simulation Engine Pipeline."""
    fig, ax = plt.subplots(figsize=(9.5, 4.0), dpi=300)
    ax.set_xlim(0, 9.5)
    ax.set_ylim(0, 4.0)
    ax.axis('off')

    def draw_step(x, y, w, h, title, sub):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.4)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2 + 0.15, title, ha='center', va='center', fontsize=8.5, fontweight='bold')
        ax.text(x + w/2, y + h/2 - 0.25, sub, ha='center', va='center', fontsize=7.5)

    draw_step(0.3, 1.5, 1.6, 1.2, "INPUT PARSER", "PID, Arrival,\nBurst, Priority")
    draw_step(2.2, 1.5, 1.6, 1.2, "CLOCK LOOP", "Discrete cycle\ntime step t += 1")
    draw_step(4.1, 1.5, 1.6, 1.2, "QUEUE DISPATCH", "Ready Queue sort\n& Preemption check")
    draw_step(6.0, 1.5, 1.6, 1.2, "METRIC ENGINE", "Compute CT, TAT,\nWT, RT, Utilization")
    draw_step(7.9, 1.5, 1.4, 1.2, "GANTT ENGINE", "Render ASCII\nTimeline Chart")

    def arr(x1, x2):
        ax.annotate('', xy=(x2, 2.1), xytext=(x1, 2.1),
                    arrowprops=dict(facecolor='#000000', width=1.0, headwidth=5, headlength=6))

    arr(1.9, 2.2)
    arr(3.8, 4.1)
    arr(5.7, 6.0)
    arr(7.6, 7.9)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "solver_pipeline_bw.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_path)

def draw_gantt_comparison():
    """Generates Figure 4.3: Comparative Scheduling Gantt Chart (Pure B&W Line Art)."""
    fig, ax = plt.subplots(figsize=(9.5, 4.5), dpi=300)
    ax.set_xlim(-0.5, 12.5)
    ax.set_ylim(-0.5, 4.0)
    ax.axis('off')

    # Draw timeline headers
    ax.text(0, 3.6, "COMPARATIVE ALGORITHM BENCHMARK (Processes: P1(AT=0, BT=5), P2(AT=1, BT=3), P3(AT=2, BT=1), P4(AT=3, BT=2))",
            fontsize=8.5, fontweight='bold')

    # Helper for Gantt bar
    def draw_gantt_bar(y, label, blocks, text_metrics):
        ax.text(-0.3, y + 0.25, label, ha='right', va='center', fontsize=8.5, fontweight='bold')
        for start, end, pid in blocks:
            w = end - start
            rect = patches.Rectangle((start, y), w, 0.5, facecolor='#FFFFFF', edgecolor='#000000', linewidth=1.2)
            ax.add_patch(rect)
            ax.text(start + w/2, y + 0.25, pid, ha='center', va='center', fontsize=8, fontweight='bold')
            # Tick marks
            ax.plot([start, start], [y - 0.08, y], color='#000000', lw=1)
            ax.plot([end, end], [y - 0.08, y], color='#000000', lw=1)
            ax.text(start, y - 0.2, str(start), ha='center', va='top', fontsize=7)
            ax.text(end, y - 0.2, str(end), ha='center', va='top', fontsize=7)
        ax.text(11.3, y + 0.25, text_metrics, ha='left', va='center', fontsize=7.5, style='italic')

    # 1. FCFS: P1(0-5), P2(5-8), P3(8-9), P4(9-11)
    draw_gantt_bar(2.6, "FCFS", [(0, 5, 'P1'), (5, 8, 'P2'), (8, 9, 'P3'), (9, 11, 'P4')], "Avg WT: 4.50 ms\nAvg TAT: 7.25 ms")

    # 2. SRTF (Preemptive): P1(0-1), P2(1-2), P3(2-3), P2(3-5), P4(5-7), P1(7-11)
    draw_gantt_bar(1.4, "SRTF", [(0, 1, 'P1'), (1, 2, 'P2'), (2, 3, 'P3'), (3, 5, 'P2'), (5, 7, 'P4'), (7, 11, 'P1')], "Avg WT: 2.25 ms\nAvg TAT: 5.00 ms")

    # 3. Round Robin (q=2): P1(0-2), P2(2-4), P3(4-5), P4(5-7), P1(7-9), P2(9-10), P1(10-11)
    draw_gantt_bar(0.2, "RR (q=2)", [(0, 2, 'P1'), (2, 4, 'P2'), (4, 5, 'P3'), (5, 7, 'P4'), (7, 9, 'P1'), (9, 10, 'P2'), (10, 11, 'P1')], "Avg WT: 4.00 ms\nAvg TAT: 6.75 ms")

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
    print("All vector-styled black and white figures generated successfully!")
