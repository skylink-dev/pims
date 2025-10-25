from django.urls import path,include  
from accounts import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.home_view, name='home'),
    path('asset', include('asset.urls')),
     path('add-to-cart/', views.add_to_cart, name='add_to_cart'), 
     path('cart/', views.view_cart, name='view_cart'),  # optional cart page
]
