"""First-Come, First-Served (FCFS) CPU scheduling algorithm."""

from typing import List
from app.scheduling.models import (
    Process,
    SchedulingResult,
    SchedulingAlgorithm,
    GanttSegment
)
from app.scheduling.validation import validate_processes
from app.scheduling.metrics import compute_metrics
from app.scheduling.gantt_renderer import render_ascii_gantt, compact_gantt_segments


def schedule_fcfs(processes: List[Process]) -> SchedulingResult:
    """
    Executes First-Come, First-Served scheduling.
    
    Tie-breaking rule:
    When processes have identical arrival times, ties are resolved deterministically
    by process ID (lexicographical / natural ordering).
    """
    validate_processes(processes, SchedulingAlgorithm.FCFS)

    # Sort primarily by arrival_time, secondarily by pid
    sorted_procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))

    current_time = 0.0
    segments: List[GanttSegment] = []

    for p in sorted_procs:
        # Handle CPU idle if process arrives in the future
        if p.arrival_time > current_time:
            idle_duration = p.arrival_time - current_time
            segments.append(
                GanttSegment(
                    process_id=None,
                    start_time=current_time,
                    end_time=p.arrival_time,
                    duration=idle_duration,
                    is_idle=True
                )
            )
            current_time = p.arrival_time

        # Process execution
        start = current_time
        end = current_time + p.burst_time
        segments.append(
            GanttSegment(
                process_id=p.pid,
                start_time=start,
                end_time=end,
                duration=p.burst_time,
                is_idle=False
            )
        )
        current_time = end

    compacted_segments = compact_gantt_segments(segments)
    metrics_list, avg_tat, avg_wt, avg_rt, cpu_util, throughput, idle_intervals = compute_metrics(
        processes, compacted_segments
    )

    ascii_gantt = render_ascii_gantt(compacted_segments)

    return SchedulingResult(
        algorithm=SchedulingAlgorithm.FCFS,
        processes=metrics_list,
        gantt_chart=compacted_segments,
        ascii_gantt=ascii_gantt,
        cpu_utilization=cpu_util,
        throughput=throughput,
        avg_turnaround_time=avg_tat,
        avg_waiting_time=avg_wt,
        avg_response_time=avg_rt,
        idle_intervals=idle_intervals,
        tie_breaking_rule="Earliest arrival time; ties broken by Process ID (lexicographical).",
        notes=[
            "Non-preemptive algorithm.",
            "Susceptible to Convoy Effect when a process with long burst time arrives first."
        ]
    )
