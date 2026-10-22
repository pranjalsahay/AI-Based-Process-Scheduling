"""Priority CPU scheduling algorithms (both non-preemptive and preemptive)."""

from typing import List, Dict, Optional, Set
from app.scheduling.models import (
    Process,
    SchedulingResult,
    SchedulingAlgorithm,
    PriorityConvention,
    GanttSegment
)
from app.scheduling.validation import validate_processes
from app.scheduling.metrics import compute_metrics
from app.scheduling.gantt_renderer import render_ascii_gantt, compact_gantt_segments


def _is_higher_priority(p1_val: int, p2_val: int, convention: PriorityConvention) -> bool:
    """Returns True if p1_val is strictly higher priority than p2_val."""
    if convention == PriorityConvention.LOWER_IS_HIGHER:
        return p1_val < p2_val
    else:
        return p1_val > p2_val


def _priority_sort_key(p: Process, convention: PriorityConvention) -> int:
    """Returns a numeric key where smaller values mean higher priority."""
    val = p.priority if p.priority is not None else 0
    if convention == PriorityConvention.LOWER_IS_HIGHER:
        return val
    else:
        return -val


def schedule_priority_non_preemptive(
    processes: List[Process],
    convention: PriorityConvention = PriorityConvention.LOWER_IS_HIGHER
) -> SchedulingResult:
    """
    Executes Non-preemptive Priority Scheduling.
    
    Tie-breaking:
    1. Highest priority (according to convention).
    2. Earliest arrival time.
    3. Process ID (lexicographical).
    """
    validate_processes(processes, SchedulingAlgorithm.PRIORITY_NON_PREEMPTIVE, priority_convention=convention)

    completed_pids: Set[str] = set()
    current_time = 0.0
    segments: List[GanttSegment] = []
    total_processes = len(processes)

    while len(completed_pids) < total_processes:
        ready = [
            p for p in processes
            if p.pid not in completed_pids and p.arrival_time <= current_time
        ]

        if not ready:
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

        # Select highest priority process
        selected = min(
            ready,
            key=lambda p: (_priority_sort_key(p, convention), p.arrival_time, p.pid)
        )

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

    convention_desc = (
        "Lower number indicates higher priority (e.g. 1 is higher than 5)"
        if convention == PriorityConvention.LOWER_IS_HIGHER
        else "Higher number indicates higher priority (e.g. 10 is higher than 1)"
    )

    return SchedulingResult(
        algorithm=SchedulingAlgorithm.PRIORITY_NON_PREEMPTIVE,
        priority_convention=convention,
        processes=metrics_list,
        gantt_chart=compacted_segments,
        ascii_gantt=ascii_gantt,
        cpu_utilization=cpu_util,
        throughput=throughput,
        avg_turnaround_time=avg_tat,
        avg_waiting_time=avg_wt,
        avg_response_time=avg_rt,
        idle_intervals=idle_intervals,
        tie_breaking_rule=f"Priority ({convention_desc}); ties broken by arrival time, then PID.",
        notes=[
            "Non-preemptive priority scheduling.",
            f"Priority convention: {convention_desc}.",
            "Susceptible to starvation for low-priority processes (solved by Aging in production systems)."
        ]
    )


def schedule_priority_preemptive(
    processes: List[Process],
    convention: PriorityConvention = PriorityConvention.LOWER_IS_HIGHER
) -> SchedulingResult:
    """
    Executes Preemptive Priority Scheduling.
    
    Tie-breaking and preemption rules:
    1. Preemption occurs if an arriving process has strictly higher priority than the currently running process.
    2. If priorities are equal, the currently running process continues running.
    3. When CPU is free, highest priority is selected. Ties broken by earliest arrival time, then PID.
    """
    validate_processes(processes, SchedulingAlgorithm.PRIORITY_PREEMPTIVE, priority_convention=convention)

    remaining_burst: Dict[str, float] = {p.pid: float(p.burst_time) for p in processes}
    arrival_times: Dict[str, float] = {p.pid: float(p.arrival_time) for p in processes}
    priorities: Dict[str, int] = {p.pid: p.priority if p.priority is not None else 0 for p in processes}
    completed_pids: Set[str] = set()
    total_processes = len(processes)

    current_time = 0.0
    segments: List[GanttSegment] = []
    current_pid: Optional[str] = None

    def pick_next_process(curr: Optional[str], time: float) -> Optional[str]:
        ready = [
            p for p in processes
            if p.pid not in completed_pids and arrival_times[p.pid] <= time
        ]
        if not ready:
            return None

        # Check if current running process should keep running
        if curr and curr not in completed_pids and remaining_burst[curr] > 0:
            highest_other = min(
                ready,
                key=lambda p: (_priority_sort_key(p, convention), arrival_times[p.pid], p.pid)
            )
            # Preemption only if strictly higher priority
            if _is_higher_priority(priorities[highest_other.pid], priorities[curr], convention):
                return highest_other.pid
            return curr

        return min(
            ready,
            key=lambda p: (_priority_sort_key(p, convention), arrival_times[p.pid], p.pid)
        ).pid

    while len(completed_pids) < total_processes:
        current_pid = pick_next_process(current_pid, current_time)

        if current_pid is None:
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

    convention_desc = (
        "Lower number indicates higher priority (e.g. 1 is higher than 5)"
        if convention == PriorityConvention.LOWER_IS_HIGHER
        else "Higher number indicates higher priority (e.g. 10 is higher than 1)"
    )

    return SchedulingResult(
        algorithm=SchedulingAlgorithm.PRIORITY_PREEMPTIVE,
        priority_convention=convention,
        processes=metrics_list,
        gantt_chart=compacted_segments,
        ascii_gantt=ascii_gantt,
        cpu_utilization=cpu_util,
        throughput=throughput,
        avg_turnaround_time=avg_tat,
        avg_waiting_time=avg_wt,
        avg_response_time=avg_rt,
        idle_intervals=idle_intervals,
        tie_breaking_rule=f"Priority ({convention_desc}). Preemption requires strictly higher priority. Ties broken by arrival time, then PID.",
        notes=[
            "Preemptive priority scheduling.",
            f"Priority convention: {convention_desc}.",
            "High priority tasks interrupt running lower-priority tasks.",
            "Can cause starvation for low-priority processes."
        ]
    )
