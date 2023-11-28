from rest_framework.pagination import PageNumberPagination


class CustomPageTraitPagination(PageNumberPagination):
    page_size = 2
    page_query_param = "pagina"
    max_page_size = 4
