from django.urls import path
from . import views

urlpatterns = [
    path('summary/<int:order_id>/pdf/', views.order_summary_pdf, name='order_summary_pdf'),
      path('orders/', views.orders_list, name='orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
]
