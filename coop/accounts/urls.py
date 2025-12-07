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
]
