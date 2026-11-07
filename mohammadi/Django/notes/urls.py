from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views_apiview, views_generic, views_viewset

router = SimpleRouter()
router.register("notes", views_viewset.NoteViewSet, basename="note-v3")

urlpatterns = [
    # v1: APIView
    path("v1/notes/", views_apiview.NoteListCreateAPIView.as_view(), name="note-v1-list"),
    path("v1/notes/<int:pk>/", views_apiview.NoteDetailAPIView.as_view(), name="note-v1-detail"),
    # v2: generic views
    path("v2/notes/", views_generic.NoteListCreateView.as_view(), name="note-v2-list"),
    path("v2/notes/<int:pk>/", views_generic.NoteDetailView.as_view(), name="note-v2-detail"),
    # v3: ViewSet + router -> /api/v3/notes/ and /api/v3/notes/<pk>/
    path("v3/", include(router.urls)),
]
