"""Utilities for safe Celery task dispatch."""

import logging
from dataclasses import dataclass
from typing import Any

from celery import Task
from kombu.exceptions import OperationalError

logger = logging.getLogger(__name__)

# Default retry delay suggestion for clients (seconds)
DEFAULT_RETRY_AFTER = 30


@dataclass
class TaskDispatchResult:
    """Result of attempting to dispatch a Celery task."""

    success: bool
    task_id: str | None = None
    error: str | None = None
    retry_after: int = DEFAULT_RETRY_AFTER


def safe_delay(
    task: Task,
    *args: Any,
    **kwargs: Any,
) -> TaskDispatchResult:
    """
    Safely dispatch a Celery task, handling broker unavailability.

    Catches kombu.exceptions.OperationalError which occurs when
    RabbitMQ/Redis broker is unavailable.

    Args:
        task: Celery task to dispatch
        *args: Positional arguments for the task
        **kwargs: Keyword arguments for the task

    Returns:
        TaskDispatchResult with success status and task_id or error message
    """
    try:
        async_result = task.delay(*args, **kwargs)
        logger.debug(f"Task {task.name} dispatched successfully: {async_result.id}")
        return TaskDispatchResult(success=True, task_id=async_result.id)

    except OperationalError as e:
        logger.warning(
            f"Broker unavailable when dispatching {task.name}: {e}",
            exc_info=True,
        )
        return TaskDispatchResult(
            success=False,
            error="broker_unavailable",
            retry_after=DEFAULT_RETRY_AFTER,
        )

    except Exception as e:
        logger.error(
            f"Unexpected error dispatching {task.name}: {e}",
            exc_info=True,
        )
        return TaskDispatchResult(
            success=False,
            error="dispatch_failed",
            retry_after=DEFAULT_RETRY_AFTER,
        )
