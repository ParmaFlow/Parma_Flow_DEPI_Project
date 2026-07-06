# backend/agents/shared/utils.py
"""
Generic helper functions shared across agents.

These utilities are pure functions with no business-specific meaning on
their own (e.g. rounding), so they live outside any single agent.
"""
import math


def round_up_to_nearest(value: float, multiple: int) -> int:
    """
    Round a value up to the nearest multiple.

    Inputs:
        value: the number to round.
        multiple: the multiple to round up to. If <= 0, the value is
            returned unchanged (cast to int).

    Outputs:
        int: value rounded up to the nearest multiple.
    """
    if multiple <= 0:
        return int(value)
    return int(math.ceil(value / multiple) * multiple)