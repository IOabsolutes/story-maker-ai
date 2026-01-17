"""Factory Boy factories for stories app models."""

import uuid

import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from apps.stories.models import (
    Chapter,
    LanguageChoice,
    Story,
    StoryStatus,
    TaskStatus,
    TaskStatusChoice,
)


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    @factory.post_generation
    def password(self, create: bool, extracted: str | None, **kwargs: object) -> None:
        """Set password after user creation."""
        password = extracted or "testpass123"
        self.set_password(password)
        if create:
            self.save()


class StoryFactory(DjangoModelFactory):
    """Factory for creating Story instances."""

    class Meta:
        model = Story

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Test Story {n}")
    premise = factory.Faker("paragraph", nb_sentences=3)
    language = LanguageChoice.RUSSIAN
    max_chapters = 10
    status = StoryStatus.IN_PROGRESS


class ChapterFactory(DjangoModelFactory):
    """Factory for creating Chapter instances."""

    class Meta:
        model = Chapter

    id = factory.LazyFunction(uuid.uuid4)
    story = factory.SubFactory(StoryFactory)
    chapter_number = factory.Sequence(lambda n: n + 1)
    content = factory.Faker("paragraph", nb_sentences=5)
    choices = factory.LazyAttribute(
        lambda _: ["Continue exploring", "Return home", "Ask for help"]
    )
    selected_choice = None
    is_generated = True


class TaskStatusFactory(DjangoModelFactory):
    """Factory for creating TaskStatus instances."""

    class Meta:
        model = TaskStatus

    id = factory.LazyFunction(uuid.uuid4)
    story = factory.SubFactory(StoryFactory)
    chapter_number = 1
    status = TaskStatusChoice.PENDING
    error_message = ""
