from fastapi import FastAPI

from .database import Base, engine

from .routers import (
    auth,
    devices,
    vehicles,
    telemetry,
)


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="Vehicle Tracker API",
    description=(
        "Vehicle, Device and Telemetry "
        "Management API"
    ),
    version="1.0.0",
)


app.include_router(
    auth.router
)

app.include_router(
    devices.router
)

app.include_router(
    vehicles.router
)

app.include_router(
    telemetry.router
)


@app.get("/")
def root():
    return {
        "message": "Vehicle Tracker API",
        "version": "1.0.0",
    }