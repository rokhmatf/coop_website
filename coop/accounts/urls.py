from django.urls import path
from .views import CustomLoginView, custom_logout
from . import views

app_name = 'accounts'

urlpatterns = [
    path('',CustomLoginView.as_view(), name='login'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('register-supervisor/', views.register_supervisor, name='register_supervisor'),
    path('reset-password/<uidb64>/<token>/', views.supervisor_password_reset_confirm, name='password_reset_confirm'),
    path('force-change-password/', views.force_password_change, name='force_password_change'),
]
