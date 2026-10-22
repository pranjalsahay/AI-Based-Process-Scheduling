"""Gantt chart rendering for ASCII and text representations."""

from typing import List
from app.scheduling.models import GanttSegment


def compact_gantt_segments(segments: List[GanttSegment]) -> List[GanttSegment]:
    """Merges adjacent segments running the same process or contiguous idle periods."""
    if not segments:
        return []

    compacted: List[GanttSegment] = []
    current = segments[0].model_copy()

    for nxt in segments[1:]:
        if (nxt.process_id == current.process_id) and (nxt.is_idle == current.is_idle):
            current.end_time = nxt.end_time
            current.duration = current.end_time - current.start_time
        else:
            compacted.append(current)
            current = nxt.model_copy()

    compacted.append(current)
    return compacted


def render_ascii_gantt(segments: List[GanttSegment], min_cell_width: int = 7) -> str:
    """
    Renders an ASCII/text Gantt chart with timestamps aligned beneath boundaries.
    
    Example:
    +-------+-------+-------+
    |  P1   |  P2   |  P3   |
    +-------+-------+-------+
    0       4       7       10
    """
    if not segments:
        return "[Empty Gantt Chart]"

    compacted = compact_gantt_segments(segments)

    # Calculate proportional or standardized cell widths
    cell_widths = []
    labels = []
    for seg in compacted:
        label = "IDLE" if (seg.is_idle or not seg.process_id) else seg.process_id
        labels.append(label)
        # Allocate width based on duration with a minimum
        width = max(min_cell_width, len(label) + 2)
        cell_widths.append(width)

    # Top border: +-------+-------+
    top_border = "+" + "+".join("-" * w for w in cell_widths) + "+"

    # Middle line: |  P1   |  P2   |
    middle_cells = []
    for label, w in zip(labels, cell_widths):
        middle_cells.append(label.center(w))
    middle_line = "|" + "|".join(middle_cells) + "|"

    # Bottom border: +-------+-------+
    bottom_border = top_border

    # Timeline line with timestamps: 0       4       7       10
    # Boundary positions in the border string:
    timestamps = [compacted[0].start_time] + [seg.end_time for seg in compacted]
    
    # Format timestamps cleanly (no unnecessary decimals for integers)
    ts_strs = [f"{ts:g}" for ts in timestamps]

    # Timeline line with timestamps: allow extra buffer width for last timestamp
    max_len = len(top_border) + max(len(ts) for ts in ts_strs) + 2
    timeline_chars = list(" " * max_len)
    current_pos = 0

    for i, ts_str in enumerate(ts_strs):
        for j, ch in enumerate(ts_str):
            target_idx = current_pos + j
            if target_idx < len(timeline_chars):
                timeline_chars[target_idx] = ch
        if i < len(cell_widths):
            current_pos += cell_widths[i] + 1  # 1 for '+' border

    timeline_line = "".join(timeline_chars).rstrip()

    return f"{top_border}\n{middle_line}\n{bottom_border}\n{timeline_line}"
