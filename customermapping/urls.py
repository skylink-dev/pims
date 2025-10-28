from django.urls import path
from . import views

urlpatterns = [
    path("", views.customer_asset_mapping, name="customer_asset_mapping"),
    path("get-customer/", views.get_customer_ajax, name="get_customer_ajax"),
    path("assign/", views.assign_customer, name="assign_customer"),
]
