from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    cable_drops,
    patch_panels,
    port_allocation,
    rack_items,
    racks,
    reference_data,
    rooms,
    sites,
    switches,
    vlans,
)

app = FastAPI(title="Network Design Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sites.router)
app.include_router(rooms.router)
app.include_router(racks.router)
app.include_router(rack_items.router)
app.include_router(patch_panels.router)
app.include_router(switches.router)
app.include_router(vlans.router)
app.include_router(cable_drops.router)
app.include_router(port_allocation.router)
app.include_router(reference_data.router)


@app.get("/health")
def health():
    return {"status": "ok"}
