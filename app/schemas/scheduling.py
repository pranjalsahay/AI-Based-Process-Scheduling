"""Pydantic schemas for the scheduling API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.scheduling.models import SchedulingAlgorithm, PriorityConvention


class ProcessInput(BaseModel):
    pid: str = Field(..., description="Process Identifier (e.g. 'P1')")
    arrival_time: float = Field(..., ge=0, description="Arrival Time (>= 0)")
    burst_time: float = Field(..., gt=0, description="Burst Time (> 0)")
    priority: Optional[int] = Field(None, description="Priority integer (required for Priority scheduling)")


class SchedulingCalculateRequest(BaseModel):
    algorithm: SchedulingAlgorithm
    processes: List[ProcessInput]
    time_quantum: Optional[float] = Field(2.0, gt=0, description="Quantum for Round Robin")
    priority_convention: Optional[PriorityConvention] = Field(
        PriorityConvention.LOWER_IS_HIGHER,
        description="Whether smaller or larger numbers mean higher priority"
    )


class ComparisonRequest(BaseModel):
    processes: List[ProcessInput]
    algorithms: Optional[List[SchedulingAlgorithm]] = None
    time_quantum: float = 2.0
    priority_convention: PriorityConvention = PriorityConvention.LOWER_IS_HIGHER


class PracticeSubmitRequest(BaseModel):
    session_id: str
    problem_id: str
    algorithm: SchedulingAlgorithm
    student_ct: Dict[str, float] = Field(..., description="Student calculated completion times per PID")
    student_tat: Dict[str, float] = Field(..., description="Student calculated turnaround times per PID")
    student_wt: Dict[str, float] = Field(..., description="Student calculated waiting times per PID")
    student_avg_tat: Optional[float] = None
    student_avg_wt: Optional[float] = None
