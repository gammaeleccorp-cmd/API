from django.urls import path

from . import views as v

urlpatterns = [
    path("vehicles/", v.VehicleCreateView.as_view(), name="vehicle-create"),
    path("vehicles/my/", v.MyVehiclesView.as_view(), name="vehicle-my"),
    path("vehicles/activate/", v.VehicleActivateView.as_view(), name="vehicle-activate"),
    path("vehicles/<int:vehicle_id>/", v.MyVehicleDetailView.as_view(), name="vehicle-detail"),
    path("vehicles/<str:vin>/deactivate/", v.VehicleDeactivateView.as_view(), name="vehicle-deactivate"),
    path("company/vehicles/", v.CompanyVehicleListCreateView.as_view(), name="company-vehicles"),
    path("company/vehicles/activate/", v.CompanyVehicleActivateView.as_view(), name="company-vehicle-activate"),
    path("company/vehicles/<int:vehicle_id>/", v.CompanyVehicleDetailView.as_view(), name="company-vehicle-detail"),
    path(
        "company/vehicles/<str:vin>/deactivate/",
        v.CompanyVehicleDeactivateView.as_view(),
        name="company-vehicle-deactivate",
    ),
]
