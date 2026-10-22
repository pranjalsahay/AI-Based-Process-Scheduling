"""Data models for CPU process scheduling."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PriorityConvention(str, Enum):
    """Defines how numerical priority values are interpreted."""
    LOWER_IS_HIGHER = "lower_is_higher"  # e.g., Priority 1 > Priority 2 (UNIX/POSIX-like)
    HIGHER_IS_HIGHER = "higher_is_higher"  # e.g., Priority 10 > Priority 1 (Windows/real-time)


class SchedulingAlgorithm(str, Enum):
    """Supported CPU scheduling algorithms."""
    FCFS = "fcfs"
    SJF_NON_PREEMPTIVE = "sjf_non_preemptive"
    SRTF = "srtf"
    PRIORITY_NON_PREEMPTIVE = "priority_non_preemptive"
    PRIORITY_PREEMPTIVE = "priority_preemptive"
    ROUND_ROBIN = "round_robin"
    HRRN = "hrrn"


class Process(BaseModel):
    """Represents a single process submission."""
    pid: str = Field(..., description="Unique process identifier, e.g. 'P1', 'P2'")
    arrival_time: float = Field(..., ge=0, description="Arrival time in the ready queue (>= 0)")
    burst_time: float = Field(..., gt=0, description="Total CPU burst time (> 0)")
    priority: Optional[int] = Field(default=None, description="Priority integer value if applicable")

    def __repr__(self) -> str:
        return f"Process(pid='{self.pid}', at={self.arrival_time}, bt={self.burst_time}, prio={self.priority})"


class GanttSegment(BaseModel):
    """Represents an execution interval on the CPU."""
    process_id: Optional[str] = Field(None, description="PID of running process or None for CPU idle")
    start_time: float = Field(..., ge=0, description="Start time of segment")
    end_time: float = Field(..., ge=0, description="End time of segment")
    duration: float = Field(..., ge=0, description="Duration = end_time - start_time")
    is_idle: bool = Field(default=False, description="True if CPU was idle during this segment")


class ProcessMetrics(BaseModel):
    """Metrics computed for a single process."""
    pid: str
    arrival_time: float
    burst_time: float
    priority: Optional[int] = None
    completion_time: float
    turnaround_time: float  # CT - AT
    waiting_time: float     # TAT - BT
    response_time: float    # FirstStart - AT


class SchedulingResult(BaseModel):
    """Complete output of a deterministic scheduling execution."""
    algorithm: SchedulingAlgorithm
    time_quantum: Optional[float] = None
    priority_convention: Optional[PriorityConvention] = None
    processes: List[ProcessMetrics]
    gantt_chart: List[GanttSegment]
    ascii_gantt: str
    cpu_utilization: float  # Percentage (0 - 100%)
    throughput: float       # Completed processes per unit time
    avg_turnaround_time: float
    avg_waiting_time: float
    avg_response_time: float
    idle_intervals: List[Dict[str, float]]
    tie_breaking_rule: str
    notes: List[str] = []
