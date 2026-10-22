"""Input validation for scheduling algorithms."""

from typing import List, Optional
from app.scheduling.models import Process, SchedulingAlgorithm, PriorityConvention


class SchedulingValidationError(ValueError):
    """Raised when process list or scheduling parameters fail validation."""
    pass


def validate_processes(
    processes: List[Process],
    algorithm: SchedulingAlgorithm,
    time_quantum: Optional[float] = None,
    priority_convention: Optional[PriorityConvention] = None
) -> None:
    """
    Validates process list and algorithm-specific parameters.
    
    Raises SchedulingValidationError on any violation.
    """
    if not processes:
        raise SchedulingValidationError("The process list cannot be empty. At least one process is required.")

    seen_pids = set()
    for p in processes:
        if not p.pid or not p.pid.strip():
            raise SchedulingValidationError("Process ID cannot be empty or blank.")
        
        normalized_pid = p.pid.strip()
        if normalized_pid in seen_pids:
            raise SchedulingValidationError(f"Duplicate process ID '{normalized_pid}' found. All PIDs must be unique.")
        seen_pids.add(normalized_pid)

        if p.arrival_time < 0:
            raise SchedulingValidationError(
                f"Process '{p.pid}' has negative arrival time ({p.arrival_time}). Arrival times must be >= 0."
            )

        if p.burst_time <= 0:
            raise SchedulingValidationError(
                f"Process '{p.pid}' has burst time {p.burst_time}. Burst times must be strictly greater than 0."
            )

        # Check algorithm-specific requirements
        if algorithm in (SchedulingAlgorithm.PRIORITY_NON_PREEMPTIVE, SchedulingAlgorithm.PRIORITY_PREEMPTIVE):
            if p.priority is None:
                raise SchedulingValidationError(
                    f"Process '{p.pid}' is missing a priority value, which is required for {algorithm.value}."
                )

    if algorithm == SchedulingAlgorithm.ROUND_ROBIN:
        if time_quantum is None:
            raise SchedulingValidationError("A positive time quantum must be specified for Round Robin scheduling.")
        if time_quantum <= 0:
            raise SchedulingValidationError(
                f"Time quantum must be strictly greater than 0. Got: {time_quantum}"
            )
