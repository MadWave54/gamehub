from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Постраничная пагинация: ?page=N&limit=M (по умолчанию 6 записей)."""

    page_size_query_param = 'limit'
    max_page_size = 100
