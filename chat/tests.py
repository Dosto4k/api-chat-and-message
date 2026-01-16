from datetime import datetime, timedelta

from rest_framework.test import APIClient
from rest_framework.serializers import ValidationError

from django.test import TestCase
from django.db.models import Model

from chat.models import Chat, Message
from chat.validators import validate_limit_query_param


def create_chats(count: int = 1) -> list[Chat]:
    """Создаёт count объектов Chat"""
    curr_chat_number = 1
    objects = []
    for _ in range(count):
        objects.append(Chat(title=f"Чат {curr_chat_number}"))
        curr_chat_number += 1
    return Chat.objects.bulk_create(objects)


def create_messages(chat: Chat, count: int = 1) -> list[Message]:
    """Создаёт count объектов Message для чата chat"""
    curr_message_number = 1
    objects = []
    for _ in range(count):
        objects.append(Message(text=f"Сообщение {curr_message_number}", chat_id=chat))
        curr_message_number += 1
    return Message.objects.bulk_create(objects)


def delete_object(pks: list[int], model: type[Model]) -> None:
    """Удаление объектов из модели model с первичными ключами pks"""
    model.objects.filter(pk__in=pks).delete()


class TestCaseWithApiClient(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        return super().setUp()


class CreateChatTestCase(TestCaseWithApiClient):
    """Проверка endpoint'а POST /chats/"""

    def test_create_chat(self) -> None:
        """Проверка создания чата"""
        response = self.client.post("/chats/", data={"title": "Чат 1"})
        self.assertEqual(response.status_code, 201)
        delete_object([response.json()["id"]], Chat)

    def test_cutting_spaces_in_title(self) -> None:
        """Проверка обрезания пробелов по краям title"""
        request_data = {
            "title": " Чат 1 ",
        }
        response = self.client.post("/chats/", data=request_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["title"], "Чат 1")
        delete_object([data["id"]], Chat)

    def test_request_with_too_long_title(self) -> None:
        """Проверка создания чата с недопустимым по длине title"""
        request_data = {
            "title": "x" * 201,
        }
        response = self.client.post("/chats/", data=request_data)
        self.assertEqual(response.status_code, 400)

    def test_request_with_blank_title(self) -> None:
        """Проверка создания чата с пустым title"""
        request_data = {
            "title": "",
        }
        response = self.client.post("/chats/", data=request_data)
        self.assertEqual(response.status_code, 400)


class SendMessageTestCase(TestCaseWithApiClient):
    """Проверка endpoint'а POST /chats/{id}/messages/"""

    def test_send_message(self) -> None:
        """Проверка отправки сообщения в чат"""
        request_data = {
            "text": "Сообщение 1",
        }
        chat = create_chats()[0]
        response = self.client.post(f"/chats/{chat.pk}/messages/", request_data)
        self.assertEqual(response.status_code, 201)
        delete_object([response.json()["id"]], Message)
        delete_object([chat.pk], Chat)

    def test_send_message_in_non_existent_chat(self) -> None:
        """Проверка отправки сообщения в несуществующий чат"""
        request_data = {
            "text": "Сообщение 1",
        }
        response = self.client.post("/chats/999/messages/", request_data)
        self.assertEqual(response.status_code, 404)

    def test_request_with_too_long_text(self) -> None:
        """Проверка отправки сообщения с недопустимым по длине text"""
        request_data = {
            "text": "x" * 5001,
        }
        chat = create_chats()[0]
        response = self.client.post(f"/chats/{chat.pk}/messages/", request_data)
        self.assertEqual(response.status_code, 400)
        delete_object([chat.pk], Chat)

    def test_request_with_blank_text(self) -> None:
        """Проверка отправки сообщения с пустым text"""
        request_data = {
            "text": "",
        }
        chat = create_chats()[0]
        response = self.client.post(f"/chats/{chat.pk}/messages/", request_data)
        self.assertEqual(response.status_code, 400)
        delete_object([chat.pk], Chat)


class RetrieveChatTestCase(TestCaseWithApiClient):
    """Проверка endpoint'а GET /chats/{id}/"""

    def test_retrieve_chat(self) -> None:
        """Проверка получения чата"""
        chat = create_chats()[0]
        response = self.client.get(f"/chats/{chat.pk}/")
        self.assertEqual(response.status_code, 200)
        delete_object([chat.pk], Chat)

    def test_retrieve_chat_with_latest_messages(self) -> None:
        """
        Проверка получения чата с последними сообщениями
        По умолчанию возвращается 20 последних сообщений
        """
        chat = create_chats()[0]
        messages = create_messages(chat, 21)
        response = self.client.get(f"/chats/{chat.pk}/")
        data = response.json()
        self.assertEqual(21, len(messages))
        self.assertEqual(20, len(data["messages"]))
        delete_object([m.pk for m in messages], Message)
        delete_object([chat.pk], Chat)

    def test_retrieve_chat_with_limit(self) -> None:
        """Проверка получения чата с последними limit сообщениями"""
        chat = create_chats()[0]
        messages = create_messages(chat, 10)
        response = self.client.get(f"/chats/{chat.pk}/?limit=5")
        data = response.json()
        self.assertEqual(10, len(messages))
        self.assertEqual(5, len(data["messages"]))
        delete_object([m.pk for m in messages], Message)
        delete_object([chat.pk], Chat)

    def test_retrieve_chat_with_invalid_limit(self) -> None:
        """Проверка получения чата с невалидным limit"""
        chat = create_chats()[0]
        response = self.client.get(f"/chats/{chat.pk}/?limit=str")
        self.assertEqual(response.status_code, 400)
        delete_object([chat.pk], Chat)

    def test_retrieve_chat_with_limit_out_of_range(self) -> None:
        """
        Проверка получения чата с limit
        выходящим за допустимый диапазон 1...100
        """
        chat = create_chats()[0]
        response = self.client.get(f"/chats/{chat.pk}/?limit=0")
        self.assertEqual(response.status_code, 400)
        response = self.client.get(f"/chats/{chat.pk}/?limit=101")
        self.assertEqual(response.status_code, 400)
        delete_object([chat.pk], Chat)

    def test_retrieve_non_existent_chat(self) -> None:
        """Проверка получения несуществующего чата"""
        response = self.client.get("/chats/999/")
        self.assertEqual(response.status_code, 404)


class DeleteChatTestCase(TestCaseWithApiClient):
    """Проверка endpoint'а DELETE /chats/{id}/"""

    def test_delete_chat(self) -> None:
        """Проверка удаления чата"""
        chat = create_chats()[0]
        response = self.client.delete(f"/chats/{chat.pk}/")
        self.assertEqual(response.status_code, 204)
        all_chats = [chat for chat in Chat.objects.all()]
        self.assertListEqual([], all_chats)

    def test_delete_non_existent_chat(self) -> None:
        """Проверка удаления несуществующего чата"""
        response = self.client.delete("/chats/999/")
        self.assertEqual(response.status_code, 404)

    def test_delete_chat_with_messages(self) -> None:
        """Проверка удаления чата с сообщениями"""
        chat = create_chats()[0]
        create_messages(chat, count=20)
        chat_pk = chat.pk
        response = self.client.delete(f"/chats/{chat_pk}/")
        self.assertEqual(response.status_code, 204)
        all_chats = [chat for chat in Chat.objects.all()]
        chats_messages = [
            message for message in Message.objects.filter(chat_id=chat_pk)
        ]
        self.assertListEqual([], all_chats)
        self.assertListEqual([], chats_messages)


class LimitValidatorTestCase(TestCase):
    """Проверка функции validate_limit_query_param"""

    def setUp(self) -> None:
        self.limit_validator = validate_limit_query_param
        return super().setUp()

    def test_string_num_parameter(self) -> None:
        """Проверка с валидным значением query-параметра limit"""
        value = "10"
        result = self.limit_validator(value)
        self.assertEqual(10, result)

    def test_string_not_num_parameter(self) -> None:
        """Проверка с невалидным значением query-параметра limit"""
        value = "not_num"
        with self.assertRaises(ValidationError):
            self.limit_validator(value)

    def test_num_parameter_out_of_range(self) -> None:
        """Проверка со значением query-параметра limit вышедшем за диапазон 1...100"""
        value = "101"
        with self.assertRaises(ValidationError):
            self.limit_validator(value)
        value = "0"
        with self.assertRaises(ValidationError):
            self.limit_validator(value)


class ChatsQuerySetWithLatestMessagesTestCase(TestCase):
    """Проверка метода Chat.get_chats_with_limited_messages"""

    def test_get_chats_with_six_messages(self) -> None:
        """Проверка получения всех чатов с заданным limit'ом сообщений"""
        chat1, chat2, chat3 = create_chats(3)
        create_messages(chat1, count=10)
        create_messages(chat2, count=5)
        chats = Chat.get_chats_with_limited_messages(limit=6)
        for chat in chats:
            self.assertTrue(len(chat.latest_messages) <= 6)  # type: ignore
        Message.objects.all().delete()
        Chat.objects.all().delete()

    def test_messages_sorting(self) -> None:
        """
        Проверка того, что сообщения отсортированы в
        порядке от самых последних до самых первых
        """
        chat = create_chats()[0]
        first_message = Message.objects.create(text="Сообщение 1", chat_id=chat)
        second_message = Message.objects.create(
            text="Сообщение 2",
            chat_id=chat,
            created_at=datetime.now() + timedelta(days=5),
        )
        third_message = Message.objects.create(text="Сообщение 1", chat_id=chat)
        chat_with_messages = Chat.get_chats_with_limited_messages(limit=6)[0]
        self.assertIs(chat_with_messages.latest_messages[0].pk, third_message.pk)  # type: ignore
        self.assertIs(chat_with_messages.latest_messages[1].pk, second_message.pk)  # type: ignore
        self.assertIs(chat_with_messages.latest_messages[2].pk, first_message.pk)  # type: ignore
        delete_object([chat.pk], Chat)
        delete_object([third_message.pk, second_message.pk, first_message.pk], Message)
