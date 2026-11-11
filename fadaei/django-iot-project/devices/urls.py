from django.urls import path
from devices.views import DeviceActivationView

urlpatterns = [
    path(
        "activate/",
        DeviceActivationView.as_view(),
        name="device-activate"
    ),
]