"""Custom pagination classes."""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Standard pagination for API responses.

    Attributes:
        page_size: Default number of items per page (20)
        page_size_query_param: Query param to override page size ("page_size")
        max_page_size: Maximum allowed page size (100)
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
