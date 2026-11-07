from django.urls import path

from . import views as v

urlpatterns = [
    path("telemetry/", v.TelemetryCreateView.as_view(), name="telemetry-create"),
    path("telemetry/vehicle/<int:vehicle_id>/", v.UserVehicleTelemetryView.as_view(), name="telemetry-user-history"),
    path(
        "company/vehicles/<int:vehicle_id>/telemetry/",
        v.CompanyVehicleTelemetryView.as_view(),
        name="telemetry-company-history",
    ),
]
