# app/api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_endpoint, name='api_endpoint'),
]
