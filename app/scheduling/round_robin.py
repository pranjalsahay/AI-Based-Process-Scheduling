"""Round Robin (RR) CPU scheduling algorithm."""

from collections import deque
from typing import List, Dict, Set
from app.scheduling.models import (
    Process,
    SchedulingResult,
    SchedulingAlgorithm,
    GanttSegment
)
from app.scheduling.validation import validate_processes
from app.scheduling.metrics import compute_metrics
from app.scheduling.gantt_renderer import render_ascii_gantt, compact_gantt_segments


def schedule_round_robin(processes: List[Process], time_quantum: float) -> SchedulingResult:
    """
    Executes Round Robin (RR) scheduling with a configurable time quantum.
    
    Queue & Quantum Boundary Rules (Standard Operating Systems Specification):
    1. At t=0, all processes arriving at t=0 enter the ready queue (ties broken by PID).
    2. A process runs for min(remaining_burst, time_quantum).
    3. During/at the quantum boundary t_new = t + delta:
       - Any process arriving in (t, t_new] is appended to the ready queue.
       - If arrival coincides EXACTLY with the quantum boundary (arrival == t_new),
         the newly arriving process enters the ready queue BEFORE the preempted process is requeued.
       - If the running process still has remaining burst time, it is then requeued at the tail.
    4. If the ready queue is empty and processes remain pending in the future:
       - CPU is idle until the next arrival time.
    """
    validate_processes(processes, SchedulingAlgorithm.ROUND_ROBIN, time_quantum=time_quantum)

    remaining_burst: Dict[str, float] = {p.pid: float(p.burst_time) for p in processes}
    arrival_times: Dict[str, float] = {p.pid: float(p.arrival_time) for p in processes}
    completed_pids: Set[str] = set()
    total_processes = len(processes)

    # Sort processes by arrival time, then PID for initial queueing
    sorted_by_arrival = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    
    current_time = 0.0
    segments: List[GanttSegment] = []
    ready_queue: deque = deque()
    enqueued_pids: Set[str] = set()

    # Enqueue initial arrivals at time 0
    for p in sorted_by_arrival:
        if p.arrival_time <= current_time:
            ready_queue.append(p.pid)
            enqueued_pids.add(p.pid)

    while len(completed_pids) < total_processes:
        if not ready_queue:
            # CPU is idle: find next earliest arriving pending process
            pending = [p for p in sorted_by_arrival if p.pid not in completed_pids and p.pid not in enqueued_pids]
            if not pending:
                break
            next_arrival = min(p.arrival_time for p in pending)
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
            # Enqueue all newly arrived processes at this new current_time
            new_arrivals = [
                p for p in pending
                if p.arrival_time <= current_time and p.pid not in enqueued_pids
            ]
            new_arrivals.sort(key=lambda p: (p.arrival_time, p.pid))
            for p in new_arrivals:
                ready_queue.append(p.pid)
                enqueued_pids.add(p.pid)
            continue

        curr_pid = ready_queue.popleft()
        run_duration = min(remaining_burst[curr_pid], time_quantum)
        start_time = current_time
        end_time = current_time + run_duration

        segments.append(
            GanttSegment(
                process_id=curr_pid,
                start_time=start_time,
                end_time=end_time,
                duration=run_duration,
                is_idle=False
            )
        )

        remaining_burst[curr_pid] -= run_duration
        current_time = end_time

        # Check for newly arrived processes during (start_time, end_time]
        # Important: Newly arrived processes join the queue BEFORE the preempted process!
        new_arrivals = [
            p for p in sorted_by_arrival
            if p.pid not in completed_pids
            and p.pid not in enqueued_pids
            and start_time < p.arrival_time <= current_time
        ]
        new_arrivals.sort(key=lambda p: (p.arrival_time, p.pid))
        for p in new_arrivals:
            ready_queue.append(p.pid)
            enqueued_pids.add(p.pid)

        # Now handle the currently running process
        if remaining_burst[curr_pid] <= 1e-9:
            remaining_burst[curr_pid] = 0.0
            completed_pids.add(curr_pid)
        else:
            # Requeue at the back of the ready queue
            ready_queue.append(curr_pid)

    compacted_segments = compact_gantt_segments(segments)
    metrics_list, avg_tat, avg_wt, avg_rt, cpu_util, throughput, idle_intervals = compute_metrics(
        processes, compacted_segments
    )

    ascii_gantt = render_ascii_gantt(compacted_segments)

    return SchedulingResult(
        algorithm=SchedulingAlgorithm.ROUND_ROBIN,
        time_quantum=time_quantum,
        processes=metrics_list,
        gantt_chart=compacted_segments,
        ascii_gantt=ascii_gantt,
        cpu_utilization=cpu_util,
        throughput=throughput,
        avg_turnaround_time=avg_tat,
        avg_waiting_time=avg_wt,
        avg_response_time=avg_rt,
        idle_intervals=idle_intervals,
        tie_breaking_rule="FIFO ready queue. On quantum expiration, simultaneous arrivals enter queue before the preempted process.",
        notes=[
            f"Preemptive Round Robin with time quantum = {time_quantum}.",
            "Designed for time-sharing systems to provide rapid response times.",
            "If time quantum is very large, Round Robin approaches FCFS.",
            "If time quantum is very small, context switching overhead degrades system performance."
        ]
    )
