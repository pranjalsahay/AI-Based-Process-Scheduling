"""Highest Response Ratio Next (HRRN) non-preemptive CPU scheduling algorithm."""

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


def schedule_hrrn(processes: List[Process]) -> SchedulingResult:
    """
    Executes non-preemptive Highest Response Ratio Next (HRRN) scheduling.
    
    Response Ratio Formula:
        R = (W + S) / S = 1 + (W / S)
        where:
        W = Waiting Time in Ready Queue (current_time - arrival_time)
        S = Service (Burst) Time
    
    Tie-breaking rule:
    1. Highest response ratio.
    2. Earliest arrival time.
    3. Process ID (lexicographical / natural ordering).
    """
    validate_processes(processes, SchedulingAlgorithm.HRRN)

    completed_pids: Set[str] = set()
    current_time = 0.0
    segments: List[GanttSegment] = []
    total_processes = len(processes)

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

        # Calculate response ratio for each ready process
        def response_ratio(p: Process) -> float:
            waiting_time = current_time - p.arrival_time
            return (waiting_time + p.burst_time) / p.burst_time

        # Select process with highest response ratio, breaking ties by earliest arrival time, then PID
        selected = max(ready, key=lambda p: (response_ratio(p), -p.arrival_time, -ord(p.pid[0]) if p.pid else 0))

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

    compact_segments = compact_gantt_segments(segments)
    metrics_list, avg_tat, avg_wt, avg_rt, cpu_util, throughput, idle_intervals = compute_metrics(
        processes, compact_segments
    )
    ascii_gantt = render_ascii_gantt(compact_segments)

    return SchedulingResult(
        algorithm=SchedulingAlgorithm.HRRN,
        processes=metrics_list,
        gantt_chart=compact_segments,
        ascii_gantt=ascii_gantt,
        cpu_utilization=cpu_util,
        throughput=throughput,
        avg_turnaround_time=avg_tat,
        avg_waiting_time=avg_wt,
        avg_response_time=avg_rt,
        idle_intervals=idle_intervals,
        tie_breaking_rule="Highest response ratio (R = 1 + W/S); ties broken by earliest arrival time, then PID.",
        notes=[
            "Non-preemptive algorithm.",
            "Eliminates starvation by dynamically increasing priority as waiting time accumulates.",
            "Equivalent to SJF when all arrival times are identical (W = 0)."
        ]
    )
