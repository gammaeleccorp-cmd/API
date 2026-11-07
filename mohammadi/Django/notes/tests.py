from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.factories import USER_A, USER_B, make_user

from .models import Note


class NoteAPITests(APITestCase):
    def setUp(self):
        self.ali = make_user(USER_A)
        self.reza = make_user(USER_B)
        self.list_url = reverse("note-v3-list")

    def test_create_note_sets_owner_and_lists_only_own_notes(self):
        self.client.force_authenticate(user=self.ali)
        response = self.client.post(self.list_url, {"title": "Ali note", "content": "secret"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.ali.id)

        Note.objects.create(owner=self.reza, title="Reza note")

        response = self.client.get(self.list_url)  # paginated response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Ali note")

    def test_access_control(self):
        note = Note.objects.create(owner=self.ali, title="Private")
        detail_url = reverse("note-v3-detail", args=[note.id])

        # anonymous -> 401
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)

        # another user -> 404 (the object is hidden by get_queryset)
        self.client.force_authenticate(user=self.reza)
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Note.objects.filter(id=note.id).exists())

        # owner -> 200
        self.client.force_authenticate(user=self.ali)
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_200_OK)
