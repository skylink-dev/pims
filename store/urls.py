from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.order_list, name='order_list'),
    path('orders/update_serials/<int:item_id>/', views.update_serials, name='update_serials'),
    path('orders/mark_completed/<int:order_id>/', views.mark_order_completed, name='mark_order_completed'),

# path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
   
]
