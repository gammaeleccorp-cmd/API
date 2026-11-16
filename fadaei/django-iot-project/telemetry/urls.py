from django.urls import path

from telemetry.views import TelemetryListView


urlpatterns = [
    path(
        "",
        TelemetryListView.as_view(),
        name="telemetry-list",
    ),
]