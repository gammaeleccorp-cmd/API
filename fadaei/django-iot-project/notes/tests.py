from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status

from notes.models import Note


User = get_user_model()


class NoteAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPass123!"
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="TestPass456!"
        )

    def test_user_can_create_note(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/notes/viewset/",
            {
                "title": "Test Note",
                "content": "Testing note creation",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["title"],
            "Test Note"
        )

        self.assertEqual(
            Note.objects.count(),
            1
        )

    def test_user_cannot_access_other_users_note(self):
        note = Note.objects.create(
            owner=self.other_user,
            title="Private Note",
            content="This belongs to another user",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/notes/viewset/{note.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )