from pydantic import BaseModel


class PortAllocationRequest(BaseModel):
    data_drops: int
    ap_drops: int = 0
    ports_per_switch: int = 48
    ap_reserved_ports_per_switch: int = 0
    uplink_ports_per_switch: int = 2


class SwitchAllocationPlanRead(BaseModel):
    switch_index: int
    data_ports: int
    ap_ports: int
    total_ports: int


class PortAllocationResult(BaseModel):
    switches_needed: int
    usable_data_ports_per_switch: int
    data_ports_needed: int
    ap_ports_needed: int
    total_ports_needed: int
    per_switch: list[SwitchAllocationPlanRead]
