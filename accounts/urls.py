from django.urls import path,include  
from accounts import views
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views

from accounts.views import CustomPasswordChangeView

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.home_view, name='home'),
    path('asset', include('asset.urls')),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('delete-from-cart/', views.delete_from_cart, name='delete_from_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('success/', views.success_page, name='success_page'),

    path('profile/', views.profile_view, name='profile'),
path('unauthorized/', views.unauthorized_page, name='unauthorized_page'),

    # Password change views
    path('password/change/', CustomPasswordChangeView.as_view(), name='password_change'),
path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),
]
