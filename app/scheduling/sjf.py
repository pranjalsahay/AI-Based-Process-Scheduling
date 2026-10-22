"""Shortest Job First (SJF) non-preemptive CPU scheduling algorithm."""

from typing import List, Set
from app.scheduling.models import (
    Process,
    SchedulingResult,
    SchedulingAlgorithm,
    GanttSegment
)
from app.scheduling.validation import validate_processes
from app.scheduling.metrics import compute_metrics
from app.scheduling.gantt_renderer import render_ascii_gantt, compact_gantt_segments


def schedule_sjf(processes: List[Process]) -> SchedulingResult:
    """
    Executes non-preemptive Shortest Job First (SJF) scheduling.
    
    Tie-breaking rule:
    1. Smallest burst time.
    2. Earliest arrival time.
    3. Process ID (lexicographical / natural ordering).
    """
    validate_processes(processes, SchedulingAlgorithm.SJF_NON_PREEMPTIVE)

    completed_pids: Set[str] = set()
    current_time = 0.0
    segments: List[GanttSegment] = []
    total_processes = len(processes)

    # Make working copy
    process_map = {p.pid: p for p in processes}

    while len(completed_pids) < total_processes:
        # Find all ready processes
        ready = [
            p for p in processes
            if p.pid not in completed_pids and p.arrival_time <= current_time
        ]

        if not ready:
            # CPU is idle until the next arriving process
            pending = [p for p in processes if p.pid not in completed_pids]
            next_proc = min(pending, key=lambda p: (p.arrival_time, p.pid))
            idle_duration = next_proc.arrival_time - current_time
            segments.append(
                GanttSegment(
                    process_id=None,
                    start_time=current_time,
                    end_time=next_proc.arrival_time,
                    duration=idle_duration,
                    is_idle=True
                )
            )
            current_time = next_proc.arrival_time
            continue

        # Select process with shortest burst time, breaking ties by arrival time, then PID
        selected = min(ready, key=lambda p: (p.burst_time, p.arrival_time, p.pid))

        start = current_time
        end = current_time + selected.burst_time
        segments.append(
            GanttSegment(
                process_id=selected.pid,
                start_time=start,
                end_time=end,
                duration=selected.burst_time,
                is_idle=False
            )
        )
        current_time = end
        completed_pids.add(selected.pid)

    compacted_segments = compact_gantt_segments(segments)
    metrics_list, avg_tat, avg_wt, avg_rt, cpu_util, throughput, idle_intervals = compute_metrics(
        processes, compacted_segments
    )

    ascii_gantt = render_ascii_gantt(compacted_segments)

    return SchedulingResult(
        algorithm=SchedulingAlgorithm.SJF_NON_PREEMPTIVE,
        processes=metrics_list,
        gantt_chart=compacted_segments,
        ascii_gantt=ascii_gantt,
        cpu_utilization=cpu_util,
        throughput=throughput,
        avg_turnaround_time=avg_tat,
        avg_waiting_time=avg_wt,
        avg_response_time=avg_rt,
        idle_intervals=idle_intervals,
        tie_breaking_rule="Smallest burst time; ties broken by earliest arrival time, then PID.",
        notes=[
            "Non-preemptive algorithm.",
            "Provably optimal in minimizing average waiting time among non-preemptive algorithms.",
            "Can cause starvation for long processes if short processes continuously arrive."
        ]
    )
