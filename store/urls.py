from django.urls import path
from . import views

urlpatterns = [
    path('store_orders/', views.store_orders, name='store_orders'),
    path('orders/update_serials/<int:item_id>/', views.update_serials, name='update_serials'),
    path('orders/mark_completed/<int:order_id>/', views.mark_order_completed, name='mark_order_completed'),
    path('orders/<int:order_id>/add-shipment/', views.add_shipment, name='add_shipment'),
    path('store_order_detail/<int:order_id>/', views.store_order_detail, name='store_order_detail'),
    path("orders/<int:order_id>/edit-shipment/", views.edit_shipment, name="edit_shipment"),
   
]
