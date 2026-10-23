import sys
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Colors
    NAVY_DARK = RGBColor(15, 23, 42)      # #0F172A
    NAVY_CARD = RGBColor(30, 41, 59)      # #1E293B
    BLUE_ACCENT = RGBColor(37, 99, 235)   # #2563EB
    CYAN_ACCENT = RGBColor(2, 132, 199)   # #0284C7
    BG_LIGHT = RGBColor(248, 250, 252)    # #F8FAFC
    CARD_BG = RGBColor(255, 255, 255)     # #FFFFFF
    TEXT_DARK = RGBColor(30, 41, 59)      # #1E293B
    TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B
    BORDER_LIGHT = RGBColor(226, 232, 240)# #E2E8F0
    CARD_TINT = RGBColor(241, 245, 249)   # #F1F5F9
    ACCENT_GREEN = RGBColor(16, 185, 129) # #10B981

    def add_header(slide, title_text, category_text="SCHEDULAI : AN INTELLIGENT SOCRATIC OS TUTOR"):
        # Header category
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = BLUE_ACCENT

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.65))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY_DARK

    def set_slide_background(slide, color=BG_LIGHT):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = color

    # =========================================================================
    # SLIDE 1: Title Slide (Topic, Team Members, Registration No., Faculty)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1, NAVY_DARK)

    # Accent decorative banner top
    banner = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.15))
    banner.fill.solid()
    banner.fill.fore_color.rgb = BLUE_ACCENT
    banner.line.color.rgb = BLUE_ACCENT

    # Project Tag
    tag_box = slide1.shapes.add_textbox(Inches(1.0), Inches(1.1), Inches(11.3), Inches(0.5))
    tf_tag = tag_box.text_frame
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = "OPERATING SYSTEMS CAPSTONE PROJECT"
    p_tag.font.size = Pt(12)
    p_tag.font.bold = True
    p_tag.font.color.rgb = CYAN_ACCENT

    # Main Title
    title_box = slide1.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.3), Inches(1.8))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p1 = tf_title.paragraphs[0]
    p1.text = "SchedulAI"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)

    p2 = tf_title.add_paragraph()
    p2.text = "An Intelligent Socratic AI Tutor for Operating Systems CPU Process Scheduling"
    p2.font.size = Pt(20)
    p2.font.color.rgb = RGBColor(203, 213, 225)
    p2.space_before = Pt(8)

    # Team Members Card
    team_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(3.7), Inches(5.4), Inches(2.8))
    team_card.fill.solid()
    team_card.fill.fore_color.rgb = NAVY_CARD
    team_card.line.color.rgb = RGBColor(51, 65, 85)

    tf_team = team_card.text_frame
    tf_team.margin_left = Inches(0.4)
    tf_team.margin_top = Inches(0.3)
    tf_team.margin_right = Inches(0.4)

    p_t_head = tf_team.paragraphs[0]
    p_t_head.text = "PROJECT TEAM MEMBERS"
    p_t_head.font.size = Pt(13)
    p_t_head.font.bold = True
    p_t_head.font.color.rgb = CYAN_ACCENT
    p_t_head.space_after = Pt(12)

    bullets_team = [
        ("Pranjal Sahay", "24BKT0082"),
        ("Shubham Hazra", "24BKT0111")
    ]
    for name, regno in bullets_team:
        p_mem = tf_team.add_paragraph()
        p_mem.text = f"•  {name}"
        p_mem.font.size = Pt(15)
        p_mem.font.bold = True
        p_mem.font.color.rgb = RGBColor(255, 255, 255)
        
        p_reg = tf_team.add_paragraph()
        p_reg.text = f"    Registration No: {regno}"
        p_reg.font.size = Pt(13)
        p_reg.font.color.rgb = RGBColor(148, 163, 184)
        p_reg.space_after = Pt(10)

    # Faculty Guide Card
    fac_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(3.7), Inches(5.5), Inches(2.8))
    fac_card.fill.solid()
    fac_card.fill.fore_color.rgb = NAVY_CARD
    fac_card.line.color.rgb = RGBColor(51, 65, 85)

    tf_fac = fac_card.text_frame
    tf_fac.margin_left = Inches(0.4)
    tf_fac.margin_top = Inches(0.3)
    tf_fac.margin_right = Inches(0.4)

    p_f_head = tf_fac.paragraphs[0]
    p_f_head.text = "FACULTY GUIDE"
    p_f_head.font.size = Pt(13)
    p_f_head.font.bold = True
    p_f_head.font.color.rgb = CYAN_ACCENT
    p_f_head.space_after = Pt(12)

    p_fac_name = tf_fac.add_paragraph()
    p_fac_name.text = "•  Mr. Jagalingam P"
    p_fac_name.font.size = Pt(17)
    p_fac_name.font.bold = True
    p_fac_name.font.color.rgb = RGBColor(255, 255, 255)

    p_fac_dept = tf_fac.add_paragraph()
    p_fac_dept.text = "    Faculty Guide & Course Coordinator"
    p_fac_dept.font.size = Pt(13)
    p_fac_dept.font.color.rgb = RGBColor(148, 163, 184)
    p_fac_dept.space_before = Pt(4)

    p_fac_sub = tf_fac.add_paragraph()
    p_fac_sub.text = "    School of Computer Science and Engineering"
    p_fac_sub.font.size = Pt(13)
    p_fac_sub.font.color.rgb = RGBColor(148, 163, 184)

    # =========================================================================
    # SLIDE 2: Introduction to Topic & Objectives (Strictly Bullets)
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, "Introduction to the Topic & Project Objectives")

    # Column 1: Introduction Card
    card_intro = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_intro.fill.solid()
    card_intro.fill.fore_color.rgb = CARD_BG
    card_intro.line.color.rgb = BORDER_LIGHT

    tf_intro = card_intro.text_frame
    tf_intro.margin_left = Inches(0.4)
    tf_intro.margin_top = Inches(0.35)
    tf_intro.margin_right = Inches(0.4)

    p_i_title = tf_intro.paragraphs[0]
    p_i_title.text = "INTRODUCTION & BACKGROUND"
    p_i_title.font.size = Pt(14)
    p_i_title.font.bold = True
    p_i_title.font.color.rgb = BLUE_ACCENT
    p_i_title.space_after = Pt(10)

    intro_bullets = [
        "Core OS Role: CPU process scheduling is the primary kernel subsystem governing CPU allocation, queue management, and overall system throughput.",
        "Learning Bottlenecks: Students struggle with non-preemptive vs preemptive mechanics, queue transitions, and complex trade-offs (e.g., Convoy Effect, Starvation).",
        "LLM Chatbot Pitfalls: Standard conversational models passively dump long textbook passages rather than cultivating conceptual understanding.",
        "Lack of Pedagogical Structure: Generic AI assistants fail to assess student intuition, diagnose misconceptions, or provide structured practice.",
        "The Solution (SchedulAI): An interactive tutor built on Socratic inquiry, deterministic Gantt verification, and verified OS knowledge grounding."
    ]

    for b in intro_bullets:
        p = tf_intro.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # Column 2: Objectives Card
    card_obj = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_obj.fill.solid()
    card_obj.fill.fore_color.rgb = CARD_BG
    card_obj.line.color.rgb = BORDER_LIGHT

    tf_obj = card_obj.text_frame
    tf_obj.margin_left = Inches(0.4)
    tf_obj.margin_top = Inches(0.35)
    tf_obj.margin_right = Inches(0.4)

    p_o_title = tf_obj.paragraphs[0]
    p_o_title.text = "PRIMARY PROJECT OBJECTIVES"
    p_o_title.font.size = Pt(14)
    p_o_title.font.bold = True
    p_o_title.font.color.rgb = BLUE_ACCENT
    p_o_title.space_after = Pt(10)

    obj_bullets = [
        "Enforce Socratic Question-Driven Teaching: Teach through real-world analogies, targeted inquiry, and guided reasoning across 20 OS concepts.",
        "Zero-Hallucination Deterministic Problem Solving: Compute verified Gantt charts and timeline metrics (TAT, WT, RT) via pure-Python algorithms.",
        "Multi-Turn Conversation & State Memory: Track student understanding stages, past errors, and misconceptions dynamically in SQLite.",
        "Authoritative Knowledge Grounding (RAG): Index 170 curated semantic chunks in ChromaDB vector store with citation attribution.",
        "Embedded Evaluation & Warm Personas: Deliver warm, adaptive acknowledgments on every turn while evaluating check questions rigorously.",
        "UI Preservation & Robustness: Retain existing clean frontend interface while passing 100% of API and system test suites."
    ]

    for b in obj_bullets:
        p = tf_obj.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 3: System Architecture Diagram & Component Explanation
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, "System Architecture & Component Explanation")

    # LEFT: Architecture Visual Diagram
    diag_container = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(6.0), Inches(5.5))
    diag_container.fill.solid()
    diag_container.fill.fore_color.rgb = CARD_BG
    diag_container.line.color.rgb = BORDER_LIGHT

    # Diagram Header inside box
    d_label = slide3.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(5.6), Inches(0.35))
    d_label.text_frame.paragraphs[0].text = "SYSTEM ARCHITECTURE PIPELINE"
    d_label.text_frame.paragraphs[0].font.size = Pt(11)
    d_label.text_frame.paragraphs[0].font.bold = True
    d_label.text_frame.paragraphs[0].font.color.rgb = BLUE_ACCENT

    # Block 1: User / Frontend
    b1 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(2.05), Inches(5.2), Inches(0.65))
    b1.fill.solid()
    b1.fill.fore_color.rgb = NAVY_CARD
    b1.line.color.rgb = BLUE_ACCENT
    b1.text_frame.paragraphs[0].text = "1. Frontend Chat Client (HTML5 / CSS3 / Vanilla JS)"
    b1.text_frame.paragraphs[0].font.size = Pt(10)
    b1.text_frame.paragraphs[0].font.bold = True
    b1.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

    # Block 2: API Gateway
    b2 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(2.9), Inches(5.2), Inches(0.65))
    b2.fill.solid()
    b2.fill.fore_color.rgb = CARD_TINT
    b2.line.color.rgb = BORDER_LIGHT
    b2.text_frame.paragraphs[0].text = "2. API Gateway & Intent Router (FastAPI / Asynchronous Router)"
    b2.text_frame.paragraphs[0].font.size = Pt(10)
    b2.text_frame.paragraphs[0].font.bold = True
    b2.text_frame.paragraphs[0].font.color.rgb = NAVY_DARK

    # Block 3: Socratic Engine & Pedagogical Controller
    b3 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(3.75), Inches(5.2), Inches(0.75))
    b3.fill.solid()
    b3.fill.fore_color.rgb = CARD_TINT
    b3.line.color.rgb = BLUE_ACCENT
    tf_b3 = b3.text_frame
    p_b3_1 = tf_b3.paragraphs[0]
    p_b3_1.text = "3. Socratic Curriculum Engine & Pedagogical Controller"
    p_b3_1.font.size = Pt(10)
    p_b3_1.font.bold = True
    p_b3_1.font.color.rgb = BLUE_ACCENT
    p_b3_2 = tf_b3.add_paragraph()
    p_b3_2.text = "• Stage 1-4 State Machine • Intent Classifier • 33 Evaluators"
    p_b3_2.font.size = Pt(8.5)
    p_b3_2.font.color.rgb = TEXT_MUTED

    # Twin Engines: Block 4A & 4B
    b4a = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.7), Inches(2.5), Inches(0.95))
    b4a.fill.solid()
    b4a.fill.fore_color.rgb = CARD_BG
    b4a.line.color.rgb = ACCENT_GREEN
    tf_b4a = b4a.text_frame
    p_b4a_1 = tf_b4a.paragraphs[0]
    p_b4a_1.text = "Deterministic Engine"
    p_b4a_1.font.size = Pt(9.5)
    p_b4a_1.font.bold = True
    p_b4a_1.font.color.rgb = NAVY_DARK
    p_b4a_2 = tf_b4a.add_paragraph()
    p_b4a_2.text = "• 11 Algorithm Solvers\n• Verified Gantt & Metrics"
    p_b4a_2.font.size = Pt(8)
    p_b4a_2.font.color.rgb = TEXT_MUTED

    b4b = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.9), Inches(4.7), Inches(2.5), Inches(0.95))
    b4b.fill.solid()
    b4b.fill.fore_color.rgb = CARD_BG
    b4b.line.color.rgb = CYAN_ACCENT
    tf_b4b = b4b.text_frame
    p_b4b_1 = tf_b4b.paragraphs[0]
    p_b4b_1.text = "ChromaDB Vector RAG"
    p_b4b_1.font.size = Pt(9.5)
    p_b4b_1.font.bold = True
    p_b4b_1.font.color.rgb = NAVY_DARK
    p_b4b_2 = tf_b4b.add_paragraph()
    p_b4b_2.text = "• 170 Curated Chunks\n• Semantic Vector Search"
    p_b4b_2.font.size = Pt(8)
    p_b4b_2.font.color.rgb = TEXT_MUTED

    # Block 5: Persistence & LLM
    b5 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(5.85), Inches(5.2), Inches(0.7))
    b5.fill.solid()
    b5.fill.fore_color.rgb = NAVY_DARK
    b5.line.color.rgb = BORDER_LIGHT
    tf_b5 = b5.text_frame
    p_b5_1 = tf_b5.paragraphs[0]
    p_b5_1.text = "5. Learner State DB (SQLite)  &  Inference (Ollama Qwen / System Prompt)"
    p_b5_1.font.size = Pt(9.5)
    p_b5_1.font.bold = True
    p_b5_1.font.color.rgb = RGBColor(255, 255, 255)

    # RIGHT: Architecture Explanation in Bullets
    card_arch_text = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.1), Inches(1.5), Inches(5.4), Inches(5.5))
    card_arch_text.fill.solid()
    card_arch_text.fill.fore_color.rgb = CARD_BG
    card_arch_text.line.color.rgb = BORDER_LIGHT

    tf_at = card_arch_text.text_frame
    tf_at.margin_left = Inches(0.35)
    tf_at.margin_top = Inches(0.3)
    tf_at.margin_right = Inches(0.35)

    p_at_h = tf_at.paragraphs[0]
    p_at_h.text = "ARCHITECTURAL SUBSYSTEMS"
    p_at_h.font.size = Pt(13)
    p_at_h.font.bold = True
    p_at_h.font.color.rgb = BLUE_ACCENT
    p_at_h.space_after = Pt(10)

    arch_bullets = [
        "Presentation Layer: Responsive, non-intrusive chat UI managing session identifiers, message timestamps, and markdown rendering.",
        "API Gateway & Routing Layer: Asynchronous FastAPI endpoints managing lifespan database startup, input sanitization, and request routing.",
        "Socratic Dialogue Subsystem: Finite-state machine tracking the 4-stage pedagogical progression, assessing baseline knowledge, and mitigating misconceptions.",
        "Deterministic Calculation Engine: Dedicated scheduling algorithms executing mathematical process simulations with zero-hallucination accuracy.",
        "ChromaDB Vector Retrieval: Vector database storing 170 semantic chunks for grounded context injection and citation provenance.",
        "State & Conversation Store: SQLite relational persistence managing multi-turn dialog history, topic progress, and learner mastery metrics.",
        "Ollama LLM Integration: Local model client operating under strict system prompts with JSON schema validation and graceful fallback."
    ]

    for b in arch_bullets:
        p = tf_at.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 4: Methodology — Pedagogical Design & Socratic Framework
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, "Methodology: Socratic Tutoring & Pedagogical Design")

    # Column 1: Socratic Progression Model
    card_m1 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_m1.fill.solid()
    card_m1.fill.fore_color.rgb = CARD_BG
    card_m1.line.color.rgb = BORDER_LIGHT

    tf_m1 = card_m1.text_frame
    tf_m1.margin_left = Inches(0.4)
    tf_m1.margin_top = Inches(0.35)
    tf_m1.margin_right = Inches(0.4)

    p_m1_h = tf_m1.paragraphs[0]
    p_m1_h.text = "4-STAGE SOCRATIC PROGRESSION"
    p_m1_h.font.size = Pt(14)
    p_m1_h.font.bold = True
    p_m1_h.font.color.rgb = BLUE_ACCENT
    p_m1_h.space_after = Pt(10)

    socratic_bullets = [
        "Stage 1 (Real-Life Intuitive Analogy): Grounds complex concepts in relatable daily scenarios (e.g., supermarket checkout for MLFQ, ER triage for Priority, canteen queue for FCFS).",
        "Stage 2 (Mechanism & Terminology): Transitions from intuition to low-level kernel mechanisms (hardware timer interrupts, PCB context switches, Red-Black Trees).",
        "Stage 3 (Trade-Offs & Phenomenon Synthesis): Explores system trade-offs, edge-cases, and systemic behaviors (Convoy Effect, starvation vs aging, cache affinity loss).",
        "Stage 4 (Guided Practice Transition): Offers verified numerical problem solving to reinforce theoretical concepts with concrete metrics.",
        "Default Teaching Mode: Conceptual inquiries strictly trigger interactive questioning rather than passive textbook paragraphs."
    ]

    for b in socratic_bullets:
        p = tf_m1.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # Column 2: Learner Modeling & Feedback Engine
    card_m2 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_m2.fill.solid()
    card_m2.fill.fore_color.rgb = CARD_BG
    card_m2.line.color.rgb = BORDER_LIGHT

    tf_m2 = card_m2.text_frame
    tf_m2.margin_left = Inches(0.4)
    tf_m2.margin_top = Inches(0.35)
    tf_m2.margin_right = Inches(0.4)

    p_m2_h = tf_m2.paragraphs[0]
    p_m2_h.text = "LEARNER MODELING & ADAPTIVE FEEDBACK"
    p_m2_h.font.size = Pt(14)
    p_m2_h.font.bold = True
    p_m2_h.font.color.rgb = BLUE_ACCENT
    p_m2_h.space_after = Pt(10)

    learner_bullets = [
        "Dynamic State Management: Persistently tracks concepts understood, partially understood, and needing review in the SQLite database.",
        "Adaptive Misconception Identification: Diagnoses common student errors (e.g., confusing turnaround time with waiting time or assuming preemption terminates jobs).",
        "33 Specialized Answer Evaluators: Robust regex and keyword evaluators recognizing nuanced student phrasing without falling back to generic chat.",
        "Warm, Encouraging Persona: Warmly acknowledges every student answer ('Spot on!', 'Exactly right!', 'Good attempt, but here is the nuance:').",
        "Zero-Knowledge & Direct-Answer Handling: Gracefully supports students with zero baseline knowledge or students explicitly requesting direct formulas."
    ]

    for b in learner_bullets:
        p = tf_m2.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 5: Methodology — Deterministic Engine & RAG Grounding
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, "Methodology: Deterministic Solver & RAG Grounding")

    # Column 1: Deterministic Scheduling Engine
    card_d1 = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_d1.fill.solid()
    card_d1.fill.fore_color.rgb = CARD_BG
    card_d1.line.color.rgb = BORDER_LIGHT

    tf_d1 = card_d1.text_frame
    tf_d1.margin_left = Inches(0.4)
    tf_d1.margin_top = Inches(0.35)
    tf_d1.margin_right = Inches(0.4)

    p_d1_h = tf_d1.paragraphs[0]
    p_d1_h.text = "DETERMINISTIC SCHEDULING SOLVER"
    p_d1_h.font.size = Pt(14)
    p_d1_h.font.bold = True
    p_d1_h.font.color.rgb = BLUE_ACCENT
    p_d1_h.space_after = Pt(10)

    solver_bullets = [
        "11 Algorithmic Solvers Implemented: FCFS, SJF, SRTF, Round Robin, Priority, HRRN, MLQ, MLFQ, Linux CFS, Real-Time RMS/EDF, Stride Scheduling.",
        "Zero Generative Math: Metrics, completion times, and queue state transitions are strictly calculated in Python, eliminating LLM arithmetic hallucination.",
        "Verified ASCII Gantt Charts: Automatically constructs clean text-based timelines with precise millisecond interval boundaries.",
        "Standard Metric Computations: Generates exact Completion Time (CT), Turnaround Time (TAT = CT - AT), Waiting Time (WT = TAT - BT), and Response Time (RT).",
        "Embedded Tutor Check Inquiries: Concludes each worked example with a targeted question testing comprehension of key timeline transitions."
    ]

    for b in solver_bullets:
        p = tf_d1.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # Column 2: Vector RAG Knowledge Base
    card_d2 = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_d2.fill.solid()
    card_d2.fill.fore_color.rgb = CARD_BG
    card_d2.line.color.rgb = BORDER_LIGHT

    tf_d2 = card_d2.text_frame
    tf_d2.margin_left = Inches(0.4)
    tf_d2.margin_top = Inches(0.35)
    tf_d2.margin_right = Inches(0.4)

    p_d2_h = tf_d2.paragraphs[0]
    p_d2_h.text = "170-CHUNK CHROMADB RAG SYSTEM"
    p_d2_h.font.size = Pt(14)
    p_d2_h.font.bold = True
    p_d2_h.font.color.rgb = BLUE_ACCENT
    p_d2_h.space_after = Pt(10)

    rag_bullets = [
        "170 High-Density Semantic Chunks: Ingested across 21 structured textbook documents covering algorithms, fundamentals, and worked problem sets.",
        "Advanced Theory Inclusion: Covers Queuing Theory (Little's Law, M/M/1), Kernel Preemption (preempt_count), Hardware Timers (APIC, PIT), and Priority Inversion.",
        "Local Vector Storage: Managed locally using ChromaDB with persistent disk serialization and dense semantic vector search.",
        "Hybrid Citation Provenance: Automatically attaches source chunk identifiers to tutor turns for academic verification.",
        "Dynamic System Prompt Injection: Injects top-k retrieved knowledge passages into the conversational prompt to ensure factual authority."
    ]

    for b in rag_bullets:
        p = tf_d2.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 6: Results & Experimental Evaluation (Strictly Bullets)
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, "Results & Experimental System Evaluation")

    # Column 1: Test Suite & Operational Robustness
    card_r1 = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_r1.fill.solid()
    card_r1.fill.fore_color.rgb = CARD_BG
    card_r1.line.color.rgb = BORDER_LIGHT

    tf_r1 = card_r1.text_frame
    tf_r1.margin_left = Inches(0.4)
    tf_r1.margin_top = Inches(0.35)
    tf_r1.margin_right = Inches(0.4)

    p_r1_h = tf_r1.paragraphs[0]
    p_r1_h.text = "VERIFIED TEST SUITE & SYSTEM STABILITY"
    p_r1_h.font.size = Pt(14)
    p_r1_h.font.bold = True
    p_r1_h.font.color.rgb = BLUE_ACCENT
    p_r1_h.space_after = Pt(10)

    test_bullets = [
        "100% Automated Test Pass Rate: All 72 unit and integration tests passing cleanly across API, database, RAG, and scheduling engines.",
        "Zero Regression Execution: Passed end-to-end API regression tests across conversational turn requirements, memory retention, and fallback routing.",
        "Fast Execution Latency: Complete 72-test suite executes in ~11.55 seconds with fast deterministic math and vector search.",
        "Robust Check Question Handlers: 11 out of 11 algorithm check question dialogues verified with warm acknowledgments and forward questions.",
        "Deterministic Solve Accuracy: 100% accuracy on canonical benchmark problems for FCFS, SJF, SRTF, RR, Priority, HRRN, MLFQ, CFS, RMS, MQMS, and Stride."
    ]

    for b in test_bullets:
        p = tf_r1.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # Column 2: Conversational & Pedagogical Results
    card_r2 = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_r2.fill.solid()
    card_r2.fill.fore_color.rgb = CARD_BG
    card_r2.line.color.rgb = BORDER_LIGHT

    tf_r2 = card_r2.text_frame
    tf_r2.margin_left = Inches(0.4)
    tf_r2.margin_top = Inches(0.35)
    tf_r2.margin_right = Inches(0.4)

    p_r2_h = tf_r2.paragraphs[0]
    p_r2_h.text = "PEDAGOGICAL & CONVERSATIONAL METRICS"
    p_r2_h.font.size = Pt(14)
    p_r2_h.font.bold = True
    p_r2_h.font.color.rgb = BLUE_ACCENT
    p_r2_h.space_after = Pt(10)

    ped_bullets = [
        "Zero Unprompted Syllabus Dumping: Greetings ('Hello') respond in 1 concise turn ('Hey! What are we learning today?') without lecture text.",
        "Active Socratic Inquiries: 100% of concept requests trigger intuitive real-life analogies rather than static encyclopedia dumps.",
        "Reliable Misconception Correction: Identified misconceptions trigger empathetic, targeted corrections before advancing.",
        "Seamless Context Carryover: Retains past topics, student answers, and difficulty levels across prolonged multi-turn sessions.",
        "Zero Frontend Regression: Existing user interface preserved completely with zero changes to layout, stylesheets, or scripts."
    ]

    for b in ped_bullets:
        p = tf_r2.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 7: Conclusion & Future Scope (Strictly Bullets)
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7)
    add_header(slide7, "Conclusion & Future Enhancements")

    # Column 1: Conclusion Card
    card_c1 = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_c1.fill.solid()
    card_c1.fill.fore_color.rgb = CARD_BG
    card_c1.line.color.rgb = BORDER_LIGHT

    tf_c1 = card_c1.text_frame
    tf_c1.margin_left = Inches(0.4)
    tf_c1.margin_top = Inches(0.35)
    tf_c1.margin_right = Inches(0.4)

    p_c1_h = tf_c1.paragraphs[0]
    p_c1_h.text = "PROJECT SUMMARY & CONTRIBUTIONS"
    p_c1_h.font.size = Pt(14)
    p_c1_h.font.bold = True
    p_c1_h.font.color.rgb = BLUE_ACCENT
    p_c1_h.space_after = Pt(10)

    concl_bullets = [
        "Successfully Built SchedulAI: Transformed generic LLM interactions into an intelligent, adaptive Operating Systems tutor.",
        "Socratic Teaching Paradigm: Replaced passive text dumps with a structured 4-stage inquiry model (Analogy -> Mechanism -> Trade-offs -> Practice).",
        "Deterministic Mathematical Grounding: Eliminated generative calculation errors by coupling NLP dialogue with a verified pure-Python solver.",
        "Universal Algorithm Coverage: Fully tuned across 20 OS curriculum topics, covering both classic uniprocessor and modern multi-core schedulers.",
        "Educational Value: Empowers engineering students to build deep conceptual intuition and master exam-level scheduling problems."
    ]

    for b in concl_bullets:
        p = tf_c1.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # Column 2: Future Scope Card
    card_c2 = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    card_c2.fill.solid()
    card_c2.fill.fore_color.rgb = CARD_BG
    card_c2.line.color.rgb = BORDER_LIGHT

    tf_c2 = card_c2.text_frame
    tf_c2.margin_left = Inches(0.4)
    tf_c2.margin_top = Inches(0.35)
    tf_c2.margin_right = Inches(0.4)

    p_c2_h = tf_c2.paragraphs[0]
    p_c2_h.text = "FUTURE RESEARCH & ENHANCEMENTS"
    p_c2_h.font.size = Pt(14)
    p_c2_h.font.bold = True
    p_c2_h.font.color.rgb = BLUE_ACCENT
    p_c2_h.space_after = Pt(10)

    future_bullets = [
        "Interactive Visual Timeline Simulator: Animated SVG / Canvas UI showing real-time process state migrations across multicore queues.",
        "Automated Exercise & Quiz Generator: Dynamic procedural workload generation with real-time student submission grading.",
        "Multimodal Voice Tutoring: Bidirectional voice interaction using speech-to-speech models for natural audio pair-learning.",
        "Kernel Code Cross-Referencing: Linking scheduling concepts directly to upstream Linux kernel source lines (e.g., `kernel/sched/fair.c`).",
        "LMS Integration: Interoperability with Moodle and Canvas platforms for automated grading and learning analytics dashboards."
    ]

    for b in future_bullets:
        p = tf_c2.add_paragraph()
        p.text = f"•  {b}"
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(10)

    # Save presentation
    output_path = "SchedulAI_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_deck()
