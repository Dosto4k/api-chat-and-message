from rest_framework.generics import CreateAPIView, RetrieveDestroyAPIView
from rest_framework.request import Request

from django.db.models.manager import BaseManager
from django.shortcuts import get_object_or_404

from chat.models import Chat
from chat.serializers import ChatSerializer, MessageSerializer
from chat.validators import validate_limit_query_param


class CreateChat(CreateAPIView):
    http_method_names = ["post"]
    serializer_class = ChatSerializer


class DetailChat(RetrieveDestroyAPIView):
    http_method_names = ["get", "delete"]
    serializer_class = ChatSerializer

    def get_queryset(self) -> BaseManager[Chat]:
        if self.request.method == "GET":
            limit = self.get_limit()
            return Chat.get_chats_with_limited_messages(limit)
        return Chat.objects.all()

    def get_limit(self) -> int:
        """Получает query параметр limit и возвращает валидный limit"""
        # Типизированно для устранения ошибки при обращении к query_params
        self.request: Request
        limit = self.request.query_params.get("limit")
        return 20 if limit is None else validate_limit_query_param(limit)


class CreateMessage(CreateAPIView):
    http_method_names = ["post"]
    serializer_class = MessageSerializer

    def perform_create(self, serializer: MessageSerializer) -> None:
        chat = get_object_or_404(Chat, pk=self.kwargs.get("chat_id"))
        serializer.save(chat_id=chat)
