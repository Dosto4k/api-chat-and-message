from rest_framework import serializers

from chat.models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["chat_id"]


class ChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(read_only=True, many=True, source="latest_messages")

    class Meta:
        model = Chat
        fields = ["id", "title", "created_at", "messages"]
