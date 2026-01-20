import logging
from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "success": False,
            "error": {
                "code": response.status_code,
                "type": exc.__class__.__name__,
                "message": response.data,
            },
        }

    if response is None or response.status_code >= 500:
        logger.error("Unhandled exception: %s", exc, exc_info=True)

    return response


class ServiceException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Ошибка выполнения операции"
    default_code = "service_error"


class StoryGenerationError(ServiceException):
    default_detail = "Не удалось сгенерировать главу истории"
    default_code = "generation_error"


class BrokerUnavailableError(ServiceException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Сервис временно недоступен. Попробуйте позже."
    default_code = "broker_unavailable"
