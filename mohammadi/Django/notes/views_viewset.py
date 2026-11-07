"""Style 3: ModelViewSet + Router"""

from rest_framework import viewsets

from accounts.permissions import IsAccount

from .models import Note
from .pagination import NotePagination
from .permissions import IsOwner
from .serializers import NoteSerializer


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [IsAccount, IsOwner]
    pagination_class = NotePagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Note.objects.none()
        # Filtering by owner protects the list endpoint and makes other users' notes 404.
        return Note.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
