"""Metrics calculation and verification for CPU scheduling."""

from typing import List, Dict, Tuple, Optional
from app.scheduling.models import Process, ProcessMetrics, GanttSegment


def compute_metrics(
    processes: List[Process],
    gantt_chart: List[GanttSegment]
) -> Tuple[List[ProcessMetrics], float, float, float, float, float, List[Dict[str, float]]]:
    """
    Computes per-process and aggregate scheduling metrics from the Gantt chart.
    
    Returns:
        (
            process_metrics_list,
            avg_turnaround_time,
            avg_waiting_time,
            avg_response_time,
            cpu_utilization_pct,
            throughput,
            idle_intervals
        )
    """
    # Track first start time, last end time, and total run duration per process
    first_start: Dict[str, float] = {}
    completion_times: Dict[str, float] = {}
    total_cpu_delivered: Dict[str, float] = {}
    idle_intervals: List[Dict[str, float]] = []
    total_idle_time = 0.0

    for seg in gantt_chart:
        if seg.is_idle or seg.process_id is None:
            idle_intervals.append({
                "start": seg.start_time,
                "end": seg.end_time,
                "duration": seg.duration
            })
            total_idle_time += seg.duration
            continue

        pid = seg.process_id
        if pid not in first_start:
            first_start[pid] = seg.start_time

        completion_times[pid] = seg.end_time
        total_cpu_delivered[pid] = total_cpu_delivered.get(pid, 0.0) + seg.duration

    # Verification: each process must have received exactly its burst time
    for p in processes:
        delivered = total_cpu_delivered.get(p.pid, 0.0)
        if abs(delivered - p.burst_time) > 1e-6:
            raise RuntimeError(
                f"Scheduling verification failed for process '{p.pid}': "
                f"expected burst {p.burst_time}, but received {delivered} CPU units."
            )

    process_metrics_list: List[ProcessMetrics] = []
    for p in processes:
        ct = completion_times[p.pid]
        tat = ct - p.arrival_time
        wt = tat - p.burst_time
        rt = first_start[p.pid] - p.arrival_time

        # Numerical sanity check
        if wt < -1e-6 or rt < -1e-6:
            raise RuntimeError(
                f"Invalid negative metrics calculated for '{p.pid}': "
                f"WT={wt}, RT={rt}. Process may have executed before arrival."
            )

        process_metrics_list.append(
            ProcessMetrics(
                pid=p.pid,
                arrival_time=p.arrival_time,
                burst_time=p.burst_time,
                priority=p.priority,
                completion_time=round(ct, 4),
                turnaround_time=round(tat, 4),
                waiting_time=round(wt, 4),
                response_time=round(rt, 4)
            )
        )

    # Sort process metrics by PID or original order
    pid_order = {p.pid: i for i, p in enumerate(processes)}
    process_metrics_list.sort(key=lambda m: pid_order[m.pid])

    n = len(process_metrics_list)
    avg_tat = round(sum(m.turnaround_time for m in process_metrics_list) / n, 4) if n > 0 else 0.0
    avg_wt = round(sum(m.waiting_time for m in process_metrics_list) / n, 4) if n > 0 else 0.0
    avg_rt = round(sum(m.response_time for m in process_metrics_list) / n, 4) if n > 0 else 0.0

    total_time = gantt_chart[-1].end_time if gantt_chart else 0.0
    total_busy_time = total_time - total_idle_time
    cpu_utilization = round((total_busy_time / total_time * 100.0), 2) if total_time > 0 else 0.0
    throughput = round(n / total_time, 4) if total_time > 0 else 0.0

    return (
        process_metrics_list,
        avg_tat,
        avg_wt,
        avg_rt,
        cpu_utilization,
        throughput,
        idle_intervals
    )
