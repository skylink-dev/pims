from django.urls import path
from . import views

urlpatterns = [
    path('', views.asset_list, name='asset_list'),        # /assets/
    path('add/', views.asset_create, name='asset_create'), # /assets/add/
    path('edit/<int:pk>/', views.asset_update, name='asset_update'),  # /assets/edit/1/
    path('delete/<int:pk>/', views.asset_delete, name='asset_delete'),# /assets/delete/1/
]
