from django.urls import path

from . import views as v

urlpatterns = [
    path("devices/", v.DeviceCreateView.as_view(), name="device-create"),
    path("devices/my/", v.MyDevicesView.as_view(), name="device-my"),
    path("devices/<int:device_id>/revoke-token/", v.RevokeDeviceTokenView.as_view(), name="device-revoke-token"),
    path("devices/<str:serial>/heartbeat/", v.HeartbeatView.as_view(), name="device-heartbeat"),
    path("devices/<str:serial>/health/", v.HealthView.as_view(), name="device-health"),
    path("devices/<str:serial>/commands/", v.CommandCreateView.as_view(), name="command-create"),
    path("devices/<str:serial>/commands/pending/", v.PendingCommandsView.as_view(), name="command-pending"),
    path("devices/<str:serial>/commands/<int:command_id>/ack/", v.CommandAckView.as_view(), name="command-ack"),
    path("devices/<str:serial>/commands/<int:command_id>/", v.CommandDetailView.as_view(), name="command-detail"),
    path("company/devices/", v.CompanyDeviceListCreateView.as_view(), name="company-devices"),
]
