from django.urls import path, include
from rest_framework.routers import DefaultRouter

from notes.views import (
    NoteListCreateView,
    NoteDetailView,
    NoteListCreateGenericView,
    NoteDetailGenericView,
    NoteViewSet,
)


router = DefaultRouter()
router.register(
    "viewset",
    NoteViewSet,
    basename="note"
)


urlpatterns = [
    # APIView
    path(
        "",
        NoteListCreateView.as_view(),
        name="note-list-create",
    ),
    path(
        "<int:pk>/",
        NoteDetailView.as_view(),
        name="note-detail",
    ),

    # Generic Views
    path(
        "generic/",
        NoteListCreateGenericView.as_view(),
        name="note-generic-list-create",
    ),
    path(
        "generic/<int:pk>/",
        NoteDetailGenericView.as_view(),
        name="note-generic-detail",
    ),

    # ModelViewSet + Router
    path(
        "",
        include(router.urls),
    ),
]