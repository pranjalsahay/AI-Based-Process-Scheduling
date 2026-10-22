"""Tests for Round Robin CPU scheduling."""

import pytest
from app.scheduling.models import Process, SchedulingAlgorithm
from app.scheduling.round_robin import schedule_round_robin
from app.scheduling.validation import SchedulingValidationError


def test_round_robin_classic_case():
    """
    Silberschatz textbook Round Robin example:
    P1: AT=0, BT=24
    P2: AT=0, BT=3
    P3: AT=0, BT=3
    Quantum = 4
    
    Expected:
    P1: 0-4 (rem 20)
    P2: 4-7 (finishes)
    P3: 7-10 (finishes)
    P1: 10-30 (compacted remaining run)
    
    P1: CT=30, WT=6, RT=0
    P2: CT=7,  WT=4, RT=4
    P3: CT=10, WT=7, RT=7
    Avg WT = 17/3 = 5.6667
    Avg TAT = 47/3 = 15.6667
    """
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=24),
        Process(pid="P2", arrival_time=0, burst_time=3),
        Process(pid="P3", arrival_time=0, burst_time=3),
    ]

    result = schedule_round_robin(procs, time_quantum=4)

    assert result.algorithm == SchedulingAlgorithm.ROUND_ROBIN
    p1 = next(p for p in result.processes if p.pid == "P1")
    p2 = next(p for p in result.processes if p.pid == "P2")
    p3 = next(p for p in result.processes if p.pid == "P3")

    assert p1.completion_time == 30
    assert p1.waiting_time == 6
    assert p1.response_time == 0

    assert p2.completion_time == 7
    assert p2.waiting_time == 4
    assert p2.response_time == 4

    assert p3.completion_time == 10
    assert p3.waiting_time == 7
    assert p3.response_time == 7

    assert result.avg_waiting_time == pytest.approx(17 / 3, rel=1e-4)
    assert result.avg_turnaround_time == pytest.approx(47 / 3, rel=1e-4)


def test_round_robin_quantum_boundary_arrival():
    """
    Test queue ordering when an arrival coincides exactly with a quantum boundary.
    P1: AT=0, BT=4
    P2: AT=2, BT=4
    Quantum = 2
    
    At t=2, P1's quantum expires and P2 arrives.
    Rule: Newly arriving process P2 enters queue BEFORE requeueing P1.
    Queue order: P2, then P1.
    Timeline:
    0-2: P1
    2-4: P2
    4-6: P1 (completes)
    6-8: P2 (completes)
    """
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=4),
        Process(pid="P2", arrival_time=2, burst_time=4),
    ]

    result = schedule_round_robin(procs, time_quantum=2)

    p1 = next(p for p in result.processes if p.pid == "P1")
    p2 = next(p for p in result.processes if p.pid == "P2")

    assert p1.completion_time == 6
    assert p2.completion_time == 8
    assert p2.response_time == 0  # P2 started immediately at t=2


def test_round_robin_invalid_quantum():
    """Test validation errors for invalid quantum."""
    procs = [Process(pid="P1", arrival_time=0, burst_time=4)]
    with pytest.raises(SchedulingValidationError, match="strictly greater than 0"):
        schedule_round_robin(procs, time_quantum=0)
    with pytest.raises(SchedulingValidationError, match="strictly greater than 0"):
        schedule_round_robin(procs, time_quantum=-2)
