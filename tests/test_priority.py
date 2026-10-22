"""Tests for non-preemptive and preemptive Priority scheduling."""

import pytest
from app.scheduling.models import Process, SchedulingAlgorithm, PriorityConvention
from app.scheduling.priority import schedule_priority_non_preemptive, schedule_priority_preemptive
from app.scheduling.validation import SchedulingValidationError


def test_priority_non_preemptive_lower_is_higher():
    """
    Test non-preemptive priority scheduling (lower integer = higher priority).
    P1: AT=0, BT=10, Prio=3
    P2: AT=0, BT=1,  Prio=1
    P3: AT=0, BT=2,  Prio=4
    P4: AT=0, BT=1,  Prio=5
    P5: AT=0, BT=5,  Prio=2
    
    Order: P2 (Prio 1), P5 (Prio 2), P1 (Prio 3), P3 (Prio 4), P4 (Prio 5)
    Execution:
    P2: 0-1 (CT=1)
    P5: 1-6 (CT=6)
    P1: 6-16 (CT=16)
    P3: 16-18 (CT=18)
    P4: 18-19 (CT=19)
    """
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=10, priority=3),
        Process(pid="P2", arrival_time=0, burst_time=1, priority=1),
        Process(pid="P3", arrival_time=0, burst_time=2, priority=4),
        Process(pid="P4", arrival_time=0, burst_time=1, priority=5),
        Process(pid="P5", arrival_time=0, burst_time=5, priority=2),
    ]

    result = schedule_priority_non_preemptive(procs, convention=PriorityConvention.LOWER_IS_HIGHER)

    assert result.algorithm == SchedulingAlgorithm.PRIORITY_NON_PREEMPTIVE
    p2 = next(p for p in result.processes if p.pid == "P2")
    p5 = next(p for p in result.processes if p.pid == "P5")
    p1 = next(p for p in result.processes if p.pid == "P1")
    p3 = next(p for p in result.processes if p.pid == "P3")
    p4 = next(p for p in result.processes if p.pid == "P4")

    assert p2.completion_time == 1
    assert p5.completion_time == 6
    assert p1.completion_time == 16
    assert p3.completion_time == 18
    assert p4.completion_time == 19

    assert result.avg_waiting_time == pytest.approx((0 + 1 + 6 + 16 + 18) / 5)


def test_priority_preemptive_with_interruption():
    """
    Test preemptive priority scheduling:
    P1: AT=0, BT=10, Prio=3
    P2: AT=2, BT=4,  Prio=1 (higher priority, preempts P1 at t=2)
    P3: AT=4, BT=2,  Prio=2 (lower than P2, so P2 continues until t=6)
    """
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=10, priority=3),
        Process(pid="P2", arrival_time=2, burst_time=4, priority=1),
        Process(pid="P3", arrival_time=4, burst_time=2, priority=2),
    ]

    result = schedule_priority_preemptive(procs, convention=PriorityConvention.LOWER_IS_HIGHER)

    p1 = next(p for p in result.processes if p.pid == "P1")
    p2 = next(p for p in result.processes if p.pid == "P2")
    p3 = next(p for p in result.processes if p.pid == "P3")

    # P1 runs 0-2 (2 units done, 8 remaining)
    # P2 runs 2-6 (CT=6, WT=0, RT=0)
    # At t=6, P3 (Prio 2) is higher priority than P1 (Prio 3)
    # P3 runs 6-8 (CT=8, WT=2, RT=2)
    # P1 resumes at 8 and finishes at 16 (CT=16, TAT=16, WT=6, RT=0)
    assert p2.completion_time == 6
    assert p2.waiting_time == 0
    assert p2.response_time == 0

    assert p3.completion_time == 8
    assert p3.waiting_time == 2
    assert p3.response_time == 2

    assert p1.completion_time == 16
    assert p1.waiting_time == 6
    assert p1.response_time == 0


def test_priority_validation_missing_priority():
    """Verify that omitting priority raises validation error."""
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=4),  # No priority
    ]
    with pytest.raises(SchedulingValidationError, match="missing a priority value"):
        schedule_priority_non_preemptive(procs)
