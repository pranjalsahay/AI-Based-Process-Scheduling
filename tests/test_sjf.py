"""Tests for non-preemptive Shortest Job First (SJF)."""

import pytest
from app.scheduling.models import Process, SchedulingAlgorithm
from app.scheduling.sjf import schedule_sjf


def test_sjf_non_preemptive_reference_case():
    """
    Standard textbook reference case with tie-breaking:
    P1: AT=0, BT=7
    P2: AT=2, BT=4
    P3: AT=4, BT=1
    P4: AT=5, BT=4
    
    Expected order: P1 (0-7), P3 (7-8), P2 (8-12), P4 (12-16)
    P2 and P4 tie on BT=4 at t=8; P2 wins because AT=2 < AT=5.
    """
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=7),
        Process(pid="P2", arrival_time=2, burst_time=4),
        Process(pid="P3", arrival_time=4, burst_time=1),
        Process(pid="P4", arrival_time=5, burst_time=4),
    ]

    result = schedule_sjf(procs)

    assert result.algorithm == SchedulingAlgorithm.SJF_NON_PREEMPTIVE
    p1 = next(p for p in result.processes if p.pid == "P1")
    p2 = next(p for p in result.processes if p.pid == "P2")
    p3 = next(p for p in result.processes if p.pid == "P3")
    p4 = next(p for p in result.processes if p.pid == "P4")

    assert p1.completion_time == 7
    assert p1.waiting_time == 0

    assert p3.completion_time == 8
    assert p3.waiting_time == 3

    assert p2.completion_time == 12
    assert p2.waiting_time == 6

    assert p4.completion_time == 16
    assert p4.waiting_time == 7

    assert result.avg_waiting_time == pytest.approx(4.0)
    assert result.avg_turnaround_time == pytest.approx(8.0)


def test_sjf_with_idle():
    """Test SJF when no process is ready initially."""
    procs = [
        Process(pid="P1", arrival_time=3, burst_time=5),
        Process(pid="P2", arrival_time=3, burst_time=2),
    ]
    result = schedule_sjf(procs)

    assert len(result.idle_intervals) == 1
    assert result.idle_intervals[0]["start"] == 0
    assert result.idle_intervals[0]["end"] == 3

    # P2 has smaller burst time (2 < 5), so P2 runs first: 3 to 5
    p2 = next(p for p in result.processes if p.pid == "P2")
    p1 = next(p for p in result.processes if p.pid == "P1")

    assert p2.completion_time == 5
    assert p2.waiting_time == 0

    assert p1.completion_time == 10
    assert p1.waiting_time == 2
