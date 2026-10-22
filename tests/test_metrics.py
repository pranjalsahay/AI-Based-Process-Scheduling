"""Tests for metric calculations, Gantt chart rendering, and algorithm comparison."""

import pytest
from app.scheduling.models import Process, SchedulingAlgorithm
from app.scheduling import compare_algorithms
from app.scheduling.gantt_renderer import render_ascii_gantt, compact_gantt_segments
from app.scheduling.models import GanttSegment


def test_compact_gantt_segments():
    """Test merging of consecutive segments of the same process."""
    segments = [
        GanttSegment(process_id="P1", start_time=0, end_time=2, duration=2, is_idle=False),
        GanttSegment(process_id="P1", start_time=2, end_time=4, duration=2, is_idle=False),
        GanttSegment(process_id="P2", start_time=4, end_time=6, duration=2, is_idle=False),
    ]
    compacted = compact_gantt_segments(segments)
    assert len(compacted) == 2
    assert compacted[0].process_id == "P1"
    assert compacted[0].start_time == 0
    assert compacted[0].end_time == 4
    assert compacted[0].duration == 4


def test_ascii_gantt_chart_formatting():
    """Test ASCII Gantt chart rendering."""
    segments = [
        GanttSegment(process_id="P1", start_time=0, end_time=4, duration=4, is_idle=False),
        GanttSegment(process_id=None, start_time=4, end_time=6, duration=2, is_idle=True),
        GanttSegment(process_id="P2", start_time=6, end_time=10, duration=4, is_idle=False),
    ]
    ascii_chart = render_ascii_gantt(segments)
    assert "P1" in ascii_chart
    assert "IDLE" in ascii_chart
    assert "P2" in ascii_chart
    assert "0" in ascii_chart
    assert "10" in ascii_chart


def test_compare_algorithms():
    """Test multi-algorithm comparison on the same process workload."""
    procs = [
        Process(pid="P1", arrival_time=0, burst_time=8, priority=3),
        Process(pid="P2", arrival_time=1, burst_time=4, priority=1),
        Process(pid="P3", arrival_time=2, burst_time=9, priority=2),
    ]
    comparison = compare_algorithms(procs, time_quantum=3.0)

    assert "fcfs" in comparison["results"]
    assert "sjf_non_preemptive" in comparison["results"]
    assert "srtf" in comparison["results"]
    assert "round_robin" in comparison["results"]
    assert "priority_non_preemptive" in comparison["results"]
    assert "priority_preemptive" in comparison["results"]

    assert len(comparison["summary"]) >= 4
    assert comparison["best_for_waiting_time"] is not None
