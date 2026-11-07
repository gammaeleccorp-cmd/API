"""Style 2: Generic views."""

from rest_framework import generics

from accounts.permissions import IsAccount

from .models import Note
from .permissions import IsOwner
from .serializers import NoteSerializer
from .pagination import NotePagination


class NoteListCreateView(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAccount]
    pagination_class = NotePagination

    def get_queryset(self):
        # drf-spectacular builds the schema without a real user
        if getattr(self, "swagger_fake_view", False):
            return Note.objects.none()
        return Note.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class NoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAccount, IsOwner]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Note.objects.none()
        return Note.objects.filter(owner=self.request.user)
