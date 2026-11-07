"""Style 1: APIView."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAccount

from .models import Note
from .permissions import IsOwner
from .pagination import NotePagination
from .serializers import NoteSerializer, PaginatedNoteSerializer



class NoteListCreateAPIView(APIView):
    permission_classes = [IsAccount]

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, description="Page number"),
            OpenApiParameter("page_size", int, description="Items per page (max 50)"),
        ],
        responses=PaginatedNoteSerializer,
    )
    def get(self, request):
        notes = Note.objects.filter(owner=request.user)
        paginator = NotePagination()
        page = paginator.paginate_queryset(notes, request, view=self)
        serializer = NoteSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(request=NoteSerializer, responses={201: NoteSerializer})
    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NoteDetailAPIView(APIView):
    permission_classes = [IsAccount, IsOwner]

    def get_object(self, pk):
        note = get_object_or_404(Note, pk=pk)
        # APIView does not call this automatically (generic views do).
        self.check_object_permissions(self.request, note)
        return note

    @extend_schema(responses=NoteSerializer)
    def get(self, request, pk):
        return Response(NoteSerializer(self.get_object(pk)).data)

    @extend_schema(request=NoteSerializer, responses=NoteSerializer)
    def put(self, request, pk):
        serializer = NoteSerializer(self.get_object(pk), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(request=NoteSerializer, responses=NoteSerializer)
    def patch(self, request, pk):
        serializer = NoteSerializer(self.get_object(pk), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
