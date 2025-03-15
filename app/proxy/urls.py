from django.urls import path, re_path
from .views import proxy_view, stream_ts, proxy_key

urlpatterns = [
    path('stream/', stream_ts, name='stream_ts'),
    path('key/', proxy_key, name='proxy_key'),
    re_path(r'^(https?://.+)/$', proxy_view, name='proxy_view'),
]