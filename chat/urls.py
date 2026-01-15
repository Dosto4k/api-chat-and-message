from django.urls import path

from chat import views


app_name = "chat"
urlpatterns = [
    path("", views.CreateChat.as_view(), name="chat-list"),
    path("<int:pk>/", views.DetailChat.as_view(), name="chat-detail"),
    path("<int:chat_id>/messages/", views.CreateMessage.as_view(), name="message-list"),
]
