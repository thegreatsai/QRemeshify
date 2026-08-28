from fastapi import APIRouter, HTTPException

from app.schemas.port_allocation import PortAllocationRequest, PortAllocationResult
from app.services.port_allocation import SwitchAllocationInput, calculate_switch_allocation

router = APIRouter(tags=["port-allocation"])


@router.post("/port-allocation/calculate", response_model=PortAllocationResult)
def calculate(payload: PortAllocationRequest):
    """Stateless calculator -- takes explicit drop counts rather than
    deriving them from a site's actual CableDrop rows, since nothing in
    the data model currently distinguishes an 'AP drop' from an ordinary
    one. Useful during design ("how many switches for this room count?")
    before drops are even entered."""
    try:
        result = calculate_switch_allocation(SwitchAllocationInput(**payload.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return PortAllocationResult(
        switches_needed=result.switches_needed,
        usable_data_ports_per_switch=result.usable_data_ports_per_switch,
        data_ports_needed=result.data_ports_needed,
        ap_ports_needed=result.ap_ports_needed,
        total_ports_needed=result.total_ports_needed,
        per_switch=[
            {
                "switch_index": p.switch_index,
                "data_ports": p.data_ports,
                "ap_ports": p.ap_ports,
                "total_ports": p.total_ports,
            }
            for p in result.per_switch
        ],
    )
