"""Admin configuration for the stories app."""

from django.contrib import admin

from .models import Chapter, Story, TaskStatus


class ChapterInline(admin.TabularInline):
    """Inline admin for chapters within a story."""

    model = Chapter
    extra = 0
    readonly_fields = ["id", "created_at"]
    fields = ["chapter_number", "is_generated", "content", "choices", "selected_choice"]
    show_change_link = True

    def get_queryset(self, request):
        """Order chapters by chapter number."""
        return super().get_queryset(request).order_by("chapter_number")


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    """Admin configuration for Story model."""

    list_display = ["title", "user", "status", "language", "chapter_count", "created_at"]
    list_filter = ["status", "language", "created_at"]
    search_fields = ["title", "premise", "user__username"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    inlines = [ChapterInline]

    def chapter_count(self, obj: Story) -> int:
        """Display the number of generated chapters."""
        return obj.chapter_count

    chapter_count.short_description = "Chapters"


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """Admin configuration for Chapter model."""

    list_display = ["story", "chapter_number", "is_generated", "created_at"]
    list_filter = ["is_generated", "created_at"]
    search_fields = ["story__title", "content"]
    readonly_fields = ["id", "created_at"]
    ordering = ["story", "chapter_number"]


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    """Admin configuration for TaskStatus model."""

    list_display = ["id", "story", "chapter_number", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["story__title", "error_message"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
