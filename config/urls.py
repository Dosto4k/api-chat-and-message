from debug_toolbar.toolbar import debug_toolbar_urls

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path("chats/", include("chat.urls", namespace="chat")),
] + debug_toolbar_urls()
