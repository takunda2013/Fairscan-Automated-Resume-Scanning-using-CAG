# scan/routing.py
from django.urls import path, re_path
from scan.consumer import ChatConsumer, DashboardConsumer, FileTableConsumer

# Define a list of URL patterns for WebSocket connections
websocket_urlpatterns = [
    path("ws/scan/", ChatConsumer.as_asgi()),
    path("ws/scan/dashboard/", DashboardConsumer.as_asgi()),
    re_path(r'ws/files/$', FileTableConsumer.as_asgi()),

]
