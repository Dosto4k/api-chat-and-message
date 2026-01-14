from django.db import models


class Chat(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"


class Message(models.Model):
    chat_id = models.ForeignKey(
        Chat, on_delete=models.CASCADE, verbose_name="Чат", related_name="messages"
    )
    text = models.TextField(max_length=5000, verbose_name="Текст")
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["-created_at"]
