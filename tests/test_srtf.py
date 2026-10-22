"""Tests for Shortest Remaining Time First (SRTF) preemptive scheduling."""

import pytest
from app.scheduling.models import Process, SchedulingAlgorithm
from app.scheduling.srtf import schedule_srtf


def test_srtf_classic_reference_case():
    """
    Classic Silberschatz reference case:
    P1: AT=0, BT=8
    P2: AT=1, BT=4
    P3: AT=2, BT=9
    P4: AT=3, BT=5
    
    Gantt execution:
    0-1: P1
    1-5: P2 (preempts P1 at t=1, finishes at t=5)
    5-10: P4 (runs to finish at t=10)
    10-17: P1 (resumes and finishes at t=17)
    17-26: P3 (runs to finish at t=26)
    """
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=8),
        Process(pid="P2", arrival_time=1, burst_time=4),
        Process(pid="P3", arrival_time=2, burst_time=9),
        Process(pid="P4", arrival_time=3, burst_time=5),
    ]

    result = schedule_srtf(procs)

    assert result.algorithm == SchedulingAlgorithm.SRTF

    p1 = next(p for p in result.processes if p.pid == "P1")
    p2 = next(p for p in result.processes if p.pid == "P2")
    p3 = next(p for p in result.processes if p.pid == "P3")
    p4 = next(p for p in result.processes if p.pid == "P4")

    assert p1.completion_time == 17
    assert p1.turnaround_time == 17
    assert p1.waiting_time == 9
    assert p1.response_time == 0

    assert p2.completion_time == 5
    assert p2.turnaround_time == 4
    assert p2.waiting_time == 0
    assert p2.response_time == 0

    assert p4.completion_time == 10
    assert p4.turnaround_time == 7
    assert p4.waiting_time == 2
    assert p4.response_time == 2

    assert p3.completion_time == 26
    assert p3.turnaround_time == 24
    assert p3.waiting_time == 15
    assert p3.response_time == 15

    assert result.avg_turnaround_time == pytest.approx(13.0)
    assert result.avg_waiting_time == pytest.approx(6.5)
    assert result.avg_response_time == pytest.approx(4.25)


def test_srtf_no_preemption_on_equal_remaining_time():
    """Verify that preemption does not happen if remaining times are identical."""
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=5),
        Process(pid="P2", arrival_time=2, burst_time=3),  # at t=2, P1 has rem=3, P2 has rem=3
    ]
    result = schedule_srtf(procs)

    p1 = next(p for p in result.processes if p.pid == "P1")
    p2 = next(p for p in result.processes if p.pid == "P2")

    # P1 should NOT be preempted because rem(P2)==3 is not strictly less than rem(P1)==3
    assert p1.completion_time == 5
    assert p2.completion_time == 8
