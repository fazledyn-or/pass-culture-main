import re
import typing


class UrlForPartial(typing.Protocol):
    def __call__(self, page: int) -> str:
        ...


PAGINATION_STEPS = 7
PAGINATION_SIDE_STEPS = PAGINATION_STEPS // 2


def pagination_links(partial_func: UrlForPartial, current_page: int, pages_total: int) -> list[tuple[int, str]]:
    start_page = current_page - PAGINATION_SIDE_STEPS
    end_page = current_page + PAGINATION_SIDE_STEPS

    if start_page < 1:
        distance = 1 - start_page
        start_page = 1
        end_page = min(end_page + distance, pages_total)
    elif end_page > pages_total:
        distance = end_page - pages_total
        end_page = pages_total
        start_page = max(start_page - distance, 1)

    return [(page, partial_func(page=page)) for page in range(start_page, end_page + 1)]


def split_terms(search_query: str) -> list[str]:
    return re.split(r"[,;\s]+", search_query)
