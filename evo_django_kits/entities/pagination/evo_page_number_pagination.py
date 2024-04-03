from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class EvoPageNumberPagination(PageNumberPagination):

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
    last_page_strings = ("last",)

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page": self.page.number,
                "page_size": self.page_size,
                "results": data,
            }
        )
