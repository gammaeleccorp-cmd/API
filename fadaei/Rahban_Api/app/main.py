from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine

from .schemas import RootResponse

from .routers import (
    admin,
    auth,
    company,
    devices,
    telemetry,
    vehicles,
)





Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Rahban API",
    description=(
        "Vehicle, Device and Telemetry "
        "Management API"
    ),
    version="1.0.0",
)

# Allows a locally-opened HTML test page (or any dev frontend) to call
# this API from the browser. Fine for local development; for a real
# deployment, replace allow_origins=["*"] with your actual frontend's
# domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(vehicles.router)
app.include_router(telemetry.router)
app.include_router(company.router)
app.include_router(admin.router)


@app.get(
    "/",
    response_model=RootResponse,
)
def root():
    return {
        "message": "Rahban API",
        "version": "1.0.0",
    }
