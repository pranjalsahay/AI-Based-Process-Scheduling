with open('app/core/tutoring_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The inserted block started right after "is_fallback=False\n                )\n\n"
block_to_remove = '''            # 7. MLFQ: Priority Boost / Starvation check question
            if (
                ("demoted jobs in q2 do not starve" in pending_q or "mechanism does mlfq use" in pending_q or "demoted to q1" in pending_q)
                and (
                    any(phrase in msg_lower for phrase in ["priority boost", "boost", "aging", "periodic boost", "move all", "reset priority", "promot"])
                    or any(phrase in msg_lower for phrase in ["don't know", "dont know", "not sure", "tell me"])
                )
            ):
                ans_msg = (
                    "Spot on! MLFQ implements a periodic **Priority Boost** (Rule 5): after a fixed time period $S$, all processes in the system are moved to top Queue $Q_0$. "
                    "This guarantees that starving CPU-bound processes get CPU time, and also allows processes whose behavior transformed from batch to interactive to regain top priority!\\n\\n"
                    "Outstanding reasoning! Would you like to explore Linux CFS or Real-Time scheduling next?"
                )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="MLFQ",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore Linux CFS or Real-Time scheduling next?",
                    hint="Type 'CFS' or 'Real-Time'.",
                    misconception=None,
                    concepts_demonstrated=["mlfq_priority_boost", "mlfq_starvation_prevention"],
                    concepts_needing_review=[],
                    source_ids=["05_multilevel_queues_and_advanced_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore Linux CFS or Real-Time scheduling next?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 8. CFS: Virtual runtime growth rate check question
            if (
                ("negative nice value make vruntime grow faster or slower" in pending_q or "vruntime grow faster or slower" in pending_q)
                and (
                    any(phrase in msg_lower for phrase in ["slower", "slow", "less", "more slowly", "decreases rate"])
                    or any(phrase in msg_lower for phrase in ["don't know", "dont know", "not sure", "tell me"])
                )
            ):
                ans_msg = (
                    "Spot on! Because high-priority tasks (negative nice values) have a much higher weight, their `vruntime` increases **slower** per millisecond of real CPU execution: "
                    "$\\Delta vruntime = \\Delta \\text{exec} \\times \\frac{1024}{weight}$. This keeps them at the leftmost branch of the Red-Black Tree longer so they receive more CPU time!\\n\\n"
                    "Would you like to explore Real-Time scheduling (RMS & EDF) or Multiprocessor scheduling next?"
                )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="CFS",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore Real-Time scheduling (RMS & EDF) or Multiprocessor scheduling next?",
                    hint="Type 'Real-Time' or 'Multiprocessor'.",
                    misconception=None,
                    concepts_demonstrated=["cfs_vruntime_nice_weight"],
                    concepts_needing_review=[],
                    source_ids=["02_linux_cfs_completely_fair_scheduler_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore Real-Time scheduling (RMS & EDF) or Multiprocessor scheduling next?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 9. Real-Time RMS: Preemption check question
            if (
                ("what would happen under preemptive rms" in pending_q or "tau_1 releases a new job" in pending_q)
                and (
                    any(phrase in msg_lower for phrase in ["preempt", "preemption", "tau_1 runs", "t1 runs", "interrupt", "switch", "stops tau_2"])
                    or any(phrase in msg_lower for phrase in ["don't know", "dont know", "not sure", "tell me"])
                )
            ):
                ans_msg = (
                    "Spot on! In preemptive Rate Monotonic Scheduling (RMS), because $\\tau_1$ has a shorter period (4 ms) than $\\tau_2$ (6 ms), "
                    "it has higher static priority. At $t=4$ ms, $\\tau_1$'s new job immediately preempts the running $\\tau_2$ to guarantee that $\\tau_1$ meets its deadline!\\n\\n"
                    "Would you like to explore Earliest Deadline First (EDF) or Multiprocessor scheduling next?"
                )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="Real-Time",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore Earliest Deadline First (EDF) or Multiprocessor scheduling next?",
                    hint="Type 'EDF' or 'Multiprocessor'.",
                    misconception=None,
                    concepts_demonstrated=["rms_preemption_mechanics"],
                    concepts_needing_review=[],
                    source_ids=["03_real_time_scheduling_rms_edf_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore Earliest Deadline First (EDF) or Multiprocessor scheduling next?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 10. Multiprocessor: Work stealing / cache affinity trade-off check question
            if (
                ("what trade-off occurs when p4 migrates from core 1 to core 0" in pending_q or "migrates from core 1" in pending_q)
                and (
                    any(phrase in msg_lower for phrase in ["cache", "cache miss", "affinity", "warm cache", "latency", "cold cache", "invalidat", "reload"])
                    or any(phrase in msg_lower for phrase in ["don't know", "dont know", "not sure", "tell me"])
                )
            ):
                ans_msg = (
                    "Spot on! While work stealing keeps Core 0 utilized (eliminating idle core waste), migrating P4 destroys its **cache affinity**. "
                    "Core 0's private L1/L2 caches are cold for P4, causing high memory access latency as P4's cache lines must be reloaded from shared L3 cache or RAM!\\n\\n"
                    "Would you like to explore another topic or try another problem?"
                )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="Multiprocessor",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore another topic or try another problem?",
                    hint="You can name any algorithm like Round Robin, SJF, SRTF, or CFS.",
                    misconception=None,
                    concepts_demonstrated=["work_stealing_cache_affinity_tradeoff"],
                    concepts_needing_review=[],
                    source_ids=["04_multiprocessor_and_thread_scheduling_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore another topic or try another problem?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )

            # 11. Stride Scheduling: Smaller stride check question
            if (
                ("smaller stride cause a process to be selected more frequently or less frequently" in pending_q or "selected more frequently or less frequently" in pending_q)
                and (
                    any(phrase in msg_lower for phrase in ["more", "more frequently", "often", "more often", "higher"])
                    or any(phrase in msg_lower for phrase in ["don't know", "dont know", "not sure", "tell me"])
                )
            ):
                ans_msg = (
                    "Spot on! In Stride Scheduling, the process with the smallest `pass` value is always scheduled next. "
                    "A smaller stride means the pass counter advances in smaller increments, causing the process to stay near the minimum pass value and be selected **more frequently**!\\n\\n"
                    "Would you like to explore another scheduling algorithm or practice another problem?"
                )
                structured_response = TutorStructuredResponse(
                    message=ans_msg,
                    mode=TutoringMode.SOCRATIC,
                    topic="Stride Scheduling",
                    action=TutorAction.ASK_QUESTION,
                    question="Would you like to explore another scheduling algorithm or practice another problem?",
                    hint="You can name any algorithm like Round Robin, SJF, SRTF, or CFS.",
                    misconception=None,
                    concepts_demonstrated=["stride_selection_frequency"],
                    concepts_needing_review=[],
                    source_ids=["05_lottery_and_stride_scheduling_p1_c0"],
                    requires_calculation=False
                )
                learner_state.pending_question = "Would you like to explore another scheduling algorithm or practice another problem?"
                learner_state.last_question_asked = learner_state.pending_question
                LearnerModelManager.update_state_from_turn(learner_state, structured_response, user_message)
                return ChatResponse(
                    session_id=session_id,
                    message=structured_response.message,
                    mode=structured_response.mode,
                    topic=structured_response.topic,
                    action=structured_response.action,
                    question=structured_response.question,
                    hint=structured_response.hint,
                    misconception=None,
                    sources=[],
                    gantt_chart_ascii=None,
                    concepts_demonstrated=structured_response.concepts_demonstrated,
                    concepts_needing_review=[],
                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )'''

# Remove all occurrences of the block
content_clean = content.replace(block_to_remove, "")

# Now find the HRRN check question block and insert it ONCE right after it
hrrn_anchor = '''            # 6. HRRN: Response ratio check question'''
assert hrrn_anchor in content_clean, "HRRN anchor not found"

# Find the end of the HRRN block
hrrn_pos = content_clean.find(hrrn_anchor)
# The return statement for HRRN is:
hrrn_end_marker = '''                    difficulty_level=learner_state.difficulty_level or "beginner",
                    is_fallback=False
                )'''
hrrn_end_pos = content_clean.find(hrrn_end_marker, hrrn_pos)
assert hrrn_end_pos != -1, "HRRN end marker not found"
insert_pos = hrrn_end_pos + len(hrrn_end_marker)

final_content = content_clean[:insert_pos] + "\n\n" + block_to_remove + content_clean[insert_pos:]

with open('app/core/tutoring_engine.py', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Cleaned tutoring_engine.py successfully! Total lines:", len(final_content.splitlines()))
