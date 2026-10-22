"""Tests for FCFS CPU scheduling."""

import pytest
from app.scheduling.models import Process, SchedulingAlgorithm
from app.scheduling.fcfs import schedule_fcfs
from app.scheduling.validation import SchedulingValidationError


def test_fcfs_classic_silberschatz():
    """Test Silberschatz textbook classic FCFS example."""
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=24),
        Process(pid="P2", arrival_time=0, burst_time=3),
        Process(pid="P3", arrival_time=0, burst_time=3),
    ]
    result = schedule_fcfs(procs)

    assert result.algorithm == SchedulingAlgorithm.FCFS
    assert len(result.processes) == 3

    # Check metrics
    p1 = next(p for p in result.processes if p.pid == "P1")
    p2 = next(p for p in result.processes if p.pid == "P2")
    p3 = next(p for p in result.processes if p.pid == "P3")

    assert p1.completion_time == 24
    assert p1.turnaround_time == 24
    assert p1.waiting_time == 0
    assert p1.response_time == 0

    assert p2.completion_time == 27
    assert p2.turnaround_time == 27
    assert p2.waiting_time == 24
    assert p2.response_time == 24

    assert p3.completion_time == 30
    assert p3.turnaround_time == 30
    assert p3.waiting_time == 27
    assert p3.response_time == 27

    assert result.avg_waiting_time == pytest.approx(17.0)
    assert result.avg_turnaround_time == pytest.approx(27.0)
    assert result.avg_response_time == pytest.approx(17.0)
    assert result.cpu_utilization == 100.0


def test_fcfs_with_staggered_arrivals_and_idle():
    """Test FCFS with staggered arrival times and CPU idle gaps."""
    procs = [
        Process(pid="P1", arrival_time=2, burst_time=4),
        Process(pid="P2", arrival_time=7, burst_time=3),
    ]
    result = schedule_fcfs(procs)

    assert len(result.idle_intervals) == 2
    assert result.idle_intervals[0]["start"] == 0
    assert result.idle_intervals[0]["end"] == 2
    assert result.idle_intervals[1]["start"] == 6
    assert result.idle_intervals[1]["end"] == 7

    p1 = next(p for p in result.processes if p.pid == "P1")
    p2 = next(p for p in result.processes if p.pid == "P2")

    assert p1.completion_time == 6
    assert p1.waiting_time == 0
    assert p2.completion_time == 10
    assert p2.waiting_time == 0

    # Total time = 10, busy = 7, utilization = 70%
    assert result.cpu_utilization == 70.0


def test_fcfs_validation():
    """Test validation errors for invalid inputs."""
    with pytest.raises(SchedulingValidationError, match="cannot be empty"):
        schedule_fcfs([])

    with pytest.raises(SchedulingValidationError, match="negative arrival time"):
        schedule_fcfs([Process.model_construct(pid="P1", arrival_time=-1, burst_time=5)])

    with pytest.raises(SchedulingValidationError, match="strictly greater than 0"):
        schedule_fcfs([Process.model_construct(pid="P1", arrival_time=0, burst_time=0)])

    with pytest.raises(SchedulingValidationError, match="Duplicate process ID"):
        schedule_fcfs([
            Process(pid="P1", arrival_time=0, burst_time=5),
            Process(pid="P1", arrival_time=1, burst_time=3),
        ])
