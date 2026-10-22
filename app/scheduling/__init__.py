"""CPU Scheduling Engine package entry point."""

from typing import List, Optional, Dict, Any
from app.scheduling.models import (
    Process,
    SchedulingResult,
    SchedulingAlgorithm,
    PriorityConvention,
    GanttSegment,
    ProcessMetrics
)
from app.scheduling.validation import SchedulingValidationError, validate_processes
from app.scheduling.fcfs import schedule_fcfs
from app.scheduling.sjf import schedule_sjf
from app.scheduling.srtf import schedule_srtf
from app.scheduling.priority import schedule_priority_non_preemptive, schedule_priority_preemptive
from app.scheduling.round_robin import schedule_round_robin
from app.scheduling.hrrn import schedule_hrrn
from app.scheduling.gantt_renderer import render_ascii_gantt, compact_gantt_segments


def run_scheduler(
    algorithm: SchedulingAlgorithm,
    processes: List[Process],
    time_quantum: Optional[float] = None,
    priority_convention: PriorityConvention = PriorityConvention.LOWER_IS_HIGHER
) -> SchedulingResult:
    """
    Main dispatch function to run any CPU scheduling algorithm deterministically.
    """
    if algorithm == SchedulingAlgorithm.FCFS:
        return schedule_fcfs(processes)
    elif algorithm == SchedulingAlgorithm.SJF_NON_PREEMPTIVE:
        return schedule_sjf(processes)
    elif algorithm == SchedulingAlgorithm.SRTF:
        return schedule_srtf(processes)
    elif algorithm == SchedulingAlgorithm.PRIORITY_NON_PREEMPTIVE:
        return schedule_priority_non_preemptive(processes, convention=priority_convention)
    elif algorithm == SchedulingAlgorithm.PRIORITY_PREEMPTIVE:
        return schedule_priority_preemptive(processes, convention=priority_convention)
    elif algorithm == SchedulingAlgorithm.ROUND_ROBIN:
        if time_quantum is None:
            raise SchedulingValidationError("time_quantum is required for Round Robin scheduling.")
        return schedule_round_robin(processes, time_quantum=time_quantum)
    elif algorithm == SchedulingAlgorithm.HRRN:
        return schedule_hrrn(processes)
    else:
        raise SchedulingValidationError(f"Unsupported algorithm: {algorithm}")


def compare_algorithms(
    processes: List[Process],
    algorithms: Optional[List[SchedulingAlgorithm]] = None,
    time_quantum: float = 2.0,
    priority_convention: PriorityConvention = PriorityConvention.LOWER_IS_HIGHER
) -> Dict[str, Any]:
    """
    Runs multiple scheduling algorithms on the exact same process set and returns
    comparative metrics, rankings, and Gantt charts.
    """
    if algorithms is None:
        # Check if priority is present in all processes
        has_priority = all(p.priority is not None for p in processes)
        algorithms = [
            SchedulingAlgorithm.FCFS,
            SchedulingAlgorithm.SJF_NON_PREEMPTIVE,
            SchedulingAlgorithm.SRTF,
            SchedulingAlgorithm.ROUND_ROBIN
        ]
        if has_priority:
            algorithms.extend([
                SchedulingAlgorithm.PRIORITY_NON_PREEMPTIVE,
                SchedulingAlgorithm.PRIORITY_PREEMPTIVE
            ])

    results: Dict[str, SchedulingResult] = {}
    summary_table: List[Dict[str, Any]] = []

    for algo in algorithms:
        try:
            res = run_scheduler(
                algorithm=algo,
                processes=processes,
                time_quantum=time_quantum,
                priority_convention=priority_convention
            )
            results[algo.value] = res
            summary_table.append({
                "algorithm": algo.value,
                "avg_turnaround_time": res.avg_turnaround_time,
                "avg_waiting_time": res.avg_waiting_time,
                "avg_response_time": res.avg_response_time,
                "cpu_utilization": res.cpu_utilization,
                "throughput": res.throughput
            })
        except Exception as e:
            results[algo.value] = {"error": str(e)}

    # Identify winners for each metric among successful runs
    valid_summaries = [s for s in summary_table if "avg_waiting_time" in s]
    best_wt = min(valid_summaries, key=lambda s: s["avg_waiting_time"])["algorithm"] if valid_summaries else None
    best_tat = min(valid_summaries, key=lambda s: s["avg_turnaround_time"])["algorithm"] if valid_summaries else None
    best_rt = min(valid_summaries, key=lambda s: s["avg_response_time"])["algorithm"] if valid_summaries else None

    return {
        "results": {k: (v.model_dump() if isinstance(v, SchedulingResult) else v) for k, v in results.items()},
        "summary": summary_table,
        "best_for_waiting_time": best_wt,
        "best_for_turnaround_time": best_tat,
        "best_for_response_time": best_rt
    }


__all__ = [
    "Process",
    "GanttSegment",
    "ProcessMetrics",
    "SchedulingResult",
    "SchedulingAlgorithm",
    "PriorityConvention",
    "SchedulingValidationError",
    "validate_processes",
    "run_scheduler",
    "compare_algorithms",
    "schedule_fcfs",
    "schedule_sjf",
    "schedule_srtf",
    "schedule_priority_non_preemptive",
    "schedule_priority_preemptive",
    "schedule_round_robin",
    "render_ascii_gantt",
    "compact_gantt_segments"
]
