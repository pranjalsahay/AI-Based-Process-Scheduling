"""Shortest Remaining Time First (SRTF) preemptive CPU scheduling algorithm."""

from typing import List, Dict, Optional, Set
from app.scheduling.models import (
    Process,
    SchedulingResult,
    SchedulingAlgorithm,
    GanttSegment
)
from app.scheduling.validation import validate_processes
from app.scheduling.metrics import compute_metrics
from app.scheduling.gantt_renderer import render_ascii_gantt, compact_gantt_segments


def schedule_srtf(processes: List[Process]) -> SchedulingResult:
    """
    Executes Shortest Remaining Time First (SRTF) preemptive scheduling.
    
    Event-driven simulation guarantees exact floating-point support.
    
    Tie-breaking and preemption rules:
    1. Preemption occurs only if an arriving process has strictly less remaining burst time
       than the currently running process: R(new) < R(current).
    2. If remaining times are equal, the currently running process continues running (avoids context switch).
    3. If multiple ready processes tie for shortest remaining time when the CPU becomes free,
       the tie is broken by earliest arrival time, then PID.
    """
    validate_processes(processes, SchedulingAlgorithm.SRTF)

    remaining_burst: Dict[str, float] = {p.pid: float(p.burst_time) for p in processes}
    arrival_times: Dict[str, float] = {p.pid: float(p.arrival_time) for p in processes}
    completed_pids: Set[str] = set()
    total_processes = len(processes)

    current_time = 0.0
    segments: List[GanttSegment] = []
    current_pid: Optional[str] = None

    # Helper to pick best ready process
    def pick_next_process(curr: Optional[str], time: float) -> Optional[str]:
        ready = [
            p for p in processes
            if p.pid not in completed_pids and arrival_times[p.pid] <= time
        ]
        if not ready:
            return None

        # If current process is still ready and has remaining time
        if curr and curr not in completed_pids and remaining_burst[curr] > 0:
            # Check if any other process has STRICTLY smaller remaining burst
            min_other = min(
                ready,
                key=lambda p: (remaining_burst[p.pid], arrival_times[p.pid], p.pid)
            )
            if remaining_burst[min_other.pid] < remaining_burst[curr] - 1e-9:
                return min_other.pid
            return curr

        # When CPU is idle or current completed, pick process with min remaining burst
        return min(
            ready,
            key=lambda p: (remaining_burst[p.pid], arrival_times[p.pid], p.pid)
        ).pid

    while len(completed_pids) < total_processes:
        current_pid = pick_next_process(current_pid, current_time)

        if current_pid is None:
            # CPU is idle until the next arriving process
            pending_arrivals = [
                arrival_times[p.pid] for p in processes
                if p.pid not in completed_pids and arrival_times[p.pid] > current_time
            ]
            next_arrival = min(pending_arrivals)
            segments.append(
                GanttSegment(
                    process_id=None,
                    start_time=current_time,
                    end_time=next_arrival,
                    duration=next_arrival - current_time,
                    is_idle=True
                )
            )
            current_time = next_arrival
            continue

        # Current process runs until either:
        # 1. It finishes: current_time + remaining_burst[current_pid]
        # 2. A new process arrives that could potentially preempt it
        finish_time = current_time + remaining_burst[current_pid]
        future_arrivals = [
            arrival_times[p.pid] for p in processes
            if p.pid not in completed_pids and arrival_times[p.pid] > current_time
        ]

        next_event_time = finish_time
        if future_arrivals:
            next_arr = min(future_arrivals)
            if next_arr < finish_time:
                next_event_time = next_arr

        duration = next_event_time - current_time
        if duration > 1e-9:
            segments.append(
                GanttSegment(
                    process_id=current_pid,
                    start_time=current_time,
                    end_time=next_event_time,
                    duration=duration,
                    is_idle=False
                )
            )
            remaining_burst[current_pid] -= duration
            current_time = next_event_time

        if remaining_burst[current_pid] <= 1e-9:
            remaining_burst[current_pid] = 0.0
            completed_pids.add(current_pid)
            current_pid = None

    compacted_segments = compact_gantt_segments(segments)
    metrics_list, avg_tat, avg_wt, avg_rt, cpu_util, throughput, idle_intervals = compute_metrics(
        processes, compacted_segments
    )

    ascii_gantt = render_ascii_gantt(compacted_segments)

    return SchedulingResult(
        algorithm=SchedulingAlgorithm.SRTF,
        processes=metrics_list,
        gantt_chart=compacted_segments,
        ascii_gantt=ascii_gantt,
        cpu_utilization=cpu_util,
        throughput=throughput,
        avg_turnaround_time=avg_tat,
        avg_waiting_time=avg_wt,
        avg_response_time=avg_rt,
        idle_intervals=idle_intervals,
        tie_breaking_rule="Smallest remaining time. Preemption requires strictly smaller remaining time. Ties broken by arrival time, then PID.",
        notes=[
            "Preemptive algorithm (preemptive version of SJF).",
            "Optimal in minimizing average waiting time across all scheduling algorithms.",
            "Higher context-switching overhead than non-preemptive SJF.",
            "Can lead to starvation of long jobs under high load."
        ]
    )
