from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from scrapy.core.spidermw import SpiderMiddlewareManager
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from scrapy.utils.asyncgen import collect_asyncgen
from scrapy.utils.misc import build_from_crawler
from scrapy.utils.test import get_crawler
from tests.utils.decorators import coroutine_test

if TYPE_CHECKING:
    from collections.abc import Iterable

    from twisted.python.failure import Failure

CALLS: list[str] = []


class _BaseMiddleware:
    def process_spider_output(self, response, result):
        yield from result

    async def process_spider_output_async(self, response, result):
        async for r in result:
            yield r

    def process_spider_exception(self, response, exception):
        CALLS.append(type(self).__name__)


class FirstMiddleware(_BaseMiddleware):
    pass


class MiddleMiddleware(_BaseMiddleware):
    pass


class LastMiddleware(_BaseMiddleware):
    pass


def _callback_yield_then_raise() -> Any:
    yield {"foo": 1}
    raise ValueError("fake exception")


def _callback_raise() -> Any:
    raise ValueError("fake exception")
    yield  # pylint: disable=unreachable


async def _run(callback: Any) -> list[str]:
    CALLS.clear()
    crawler = get_crawler(
        Spider,
        {
            "SPIDER_MIDDLEWARES_BASE": {},
            "SPIDER_MIDDLEWARES": {
                FirstMiddleware: 10,
                MiddleMiddleware: 20,
                LastMiddleware: 30,
            },
        },
    )
    crawler.spider = crawler._create_spider("foo")
    mwman = build_from_crawler(SpiderMiddlewareManager, crawler)
    request = Request("http://example.com/index.html")
    response = Response(request.url, request=request)

    async def scrape_func(
        response: Response | Failure, request: Request
    ) -> Iterable[Any]:
        return callback()

    result = await mwman.scrape_response_async(scrape_func, response, request)
    with pytest.raises(ValueError, match="fake exception"):
        await collect_asyncgen(result)
    return list(CALLS)


@coroutine_test
async def test_exception_handlers_run_once_with_yield():
    calls = await _run(_callback_yield_then_raise)
    assert calls == ["LastMiddleware", "MiddleMiddleware", "FirstMiddleware"]


@coroutine_test
async def test_exception_handlers_run_once_without_yield():
    calls = await _run(_callback_raise)
    assert calls == ["LastMiddleware", "MiddleMiddleware", "FirstMiddleware"]
