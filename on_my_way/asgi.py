import os
from django.core.asgi import get_asgi_application
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'on_my_way.settings')

django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import backend.routing  # Import the routing of your app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'on_my_way.settings')

django.setup()

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            backend.routing.websocket_urlpatterns
        )
    ),
})