from rest_framework import serializers

from apps.stories.models import Chapter, Story, TaskStatus


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = [
            "id",
            "chapter_number",
            "content",
            "choices",
            "selected_choice",
            "is_generated",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class StorySerializer(serializers.ModelSerializer):
    chapter_count = serializers.IntegerField(read_only=True)
    chapters = ChapterSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "premise",
            "language",
            "max_chapters",
            "status",
            "chapter_count",
            "created_at",
            "updated_at",
            "chapters",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class StoryListSerializer(serializers.ModelSerializer):
    chapter_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "language",
            "status",
            "chapter_count",
            "max_chapters",
            "created_at",
        ]


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = [
            "id",
            "story",
            "chapter_number",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
