from rest_framework import serializers

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "owner", "title", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

class PaginatedNoteSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = NoteSerializer(many=True)