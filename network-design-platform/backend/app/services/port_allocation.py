"""Answers the question the old workbook's 'Switch & Port Allocation' sheet
answered with a wall of nested `ROUNDDOWN`/`COUNTIFS`/`MOD` formulas tied to
one specific, undocumented cell layout: given a count of drops, how many
switches do we need, and how do the drops spread across them?

This is a clean-room reimplementation of that *intent*, not a port of the
original formulas -- those formulas referenced hidden helper cells (`$S$2`,
`U2`, ...) in ways that couldn't be safely reverse-engineered from a blank
template with no filled-in example to check against. Trying to fake that
fidelity would be worse than being upfront that this is a fresh
implementation: explicit parameters, one clear algorithm, tested against
its own stated behavior.

Two drop categories, matching the sheet's distinction between ordinary
data drops and AP drops (its comment: "Ports 30-48 are set for Trunk for
APs"): AP drops need ports reserved for them per switch, separate from the
general data-port pool. Ports for switch-to-switch uplinks are reserved
out of every switch's count too, since they're never available for a drop.
"""

from dataclasses import dataclass, field
from math import ceil


@dataclass
class SwitchAllocationInput:
    data_drops: int
    ap_drops: int = 0
    ports_per_switch: int = 48
    ap_reserved_ports_per_switch: int = 0
    uplink_ports_per_switch: int = 2


@dataclass
class SwitchAllocationPlan:
    switch_index: int
    data_ports: int
    ap_ports: int
    total_ports: int


@dataclass
class SwitchAllocationResult:
    switches_needed: int
    usable_data_ports_per_switch: int
    data_ports_needed: int
    ap_ports_needed: int
    total_ports_needed: int
    per_switch: list[SwitchAllocationPlan] = field(default_factory=list)


def _distribute_evenly(total: int, buckets: int) -> list[int]:
    """Splits `total` across `buckets` as evenly as possible -- the first
    `total % buckets` buckets get one extra. With `buckets` chosen as the
    minimum needed for `total` at a given per-bucket capacity, no bucket
    in the result exceeds that capacity (see the docstring on
    calculate_switch_allocation for why)."""
    if buckets == 0:
        return []
    base, remainder = divmod(total, buckets)
    return [base + 1 if i < remainder else base for i in range(buckets)]


def calculate_switch_allocation(inp: SwitchAllocationInput) -> SwitchAllocationResult:
    """Determines switches_needed as whichever pool (data or AP) demands
    more switches, then spreads each pool evenly across that many
    switches. Because switches_needed is at least `ceil(pool / capacity)`
    for both pools, evenly distributing a pool across that many switches
    can never put more than `capacity` of that pool on any one switch --
    the whole point of using the max, rather than summing the two switch
    counts, is that both pools can share the same physical switches.
    """
    if inp.data_drops < 0 or inp.ap_drops < 0:
        raise ValueError("drop counts must be >= 0")
    if inp.ports_per_switch < 1:
        raise ValueError("ports_per_switch must be >= 1")
    if inp.ap_reserved_ports_per_switch < 0 or inp.uplink_ports_per_switch < 0:
        raise ValueError("reserved port counts must be >= 0")

    usable_data_ports = inp.ports_per_switch - inp.ap_reserved_ports_per_switch - inp.uplink_ports_per_switch
    if usable_data_ports < 1:
        raise ValueError(
            f"ap_reserved_ports_per_switch ({inp.ap_reserved_ports_per_switch}) + "
            f"uplink_ports_per_switch ({inp.uplink_ports_per_switch}) leaves no usable data ports "
            f"out of {inp.ports_per_switch} per switch"
        )
    if inp.ap_drops > 0 and inp.ap_reserved_ports_per_switch < 1:
        raise ValueError("ap_reserved_ports_per_switch must be >= 1 when ap_drops > 0")

    switches_for_data = ceil(inp.data_drops / usable_data_ports) if inp.data_drops > 0 else 0
    switches_for_ap = (
        ceil(inp.ap_drops / inp.ap_reserved_ports_per_switch) if inp.ap_drops > 0 else 0
    )
    switches_needed = max(switches_for_data, switches_for_ap, 1 if (inp.data_drops or inp.ap_drops) else 0)

    data_dist = _distribute_evenly(inp.data_drops, switches_needed)
    ap_dist = _distribute_evenly(inp.ap_drops, switches_needed)

    per_switch = [
        SwitchAllocationPlan(
            switch_index=i + 1,
            data_ports=data_dist[i],
            ap_ports=ap_dist[i],
            total_ports=data_dist[i] + ap_dist[i],
        )
        for i in range(switches_needed)
    ]

    return SwitchAllocationResult(
        switches_needed=switches_needed,
        usable_data_ports_per_switch=usable_data_ports,
        data_ports_needed=inp.data_drops,
        ap_ports_needed=inp.ap_drops,
        total_ports_needed=inp.data_drops + inp.ap_drops,
        per_switch=per_switch,
    )
