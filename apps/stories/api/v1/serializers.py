from rest_framework import serializers

from apps.stories.models import Chapter, Story


class ChapterSerializer(serializers.ModelSerializer):
    is_final = serializers.BooleanField(read_only=True)
    can_select_choice = serializers.BooleanField(read_only=True)

    class Meta:
        model = Chapter
        fields = [
            "id",
            "chapter_number",
            "content",
            "choices",
            "selected_choice",
            "is_generated",
            "is_final",
            "can_select_choice",
            "created_at",
        ]
        read_only_fields = ["id", "content", "choices", "is_generated", "created_at"]


class StoryListSerializer(serializers.ModelSerializer):
    chapter_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "premise",
            "language",
            "status",
            "max_chapters",
            "chapter_count",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class StoryDetailSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)
    chapter_count = serializers.IntegerField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    can_continue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "premise",
            "language",
            "status",
            "max_chapters",
            "chapter_count",
            "is_complete",
            "can_continue",
            "chapters",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class StoryCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    premise = serializers.CharField()
    language = serializers.ChoiceField(choices=["ru", "en"], default="ru")
    max_chapters = serializers.IntegerField(min_value=1, max_value=50, default=10)


class ChapterChoiceSerializer(serializers.Serializer):
    choice = serializers.CharField(max_length=500)
