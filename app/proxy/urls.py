from django.urls import path, re_path
from .views import proxy_view, stream_ts

urlpatterns = [
    path('stream/', stream_ts, name='stream_ts'),
    path('', proxy_view, name='proxy_view'),
]