from django.urls import path

from vehicles.views import VehicleListView, VehicleDetailView


urlpatterns = [
    path("", VehicleListView.as_view(), name="vehicle-list"),
    path("<int:pk>/", VehicleDetailView.as_view(), name="vehicle-detail"),
]
