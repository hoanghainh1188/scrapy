from __future__ import annotations

from typing import Any

import pytest

from scrapy.core.spidermw import SpiderMiddlewareManager
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from scrapy.utils.asyncgen import collect_asyncgen
from scrapy.utils.misc import build_from_crawler
from scrapy.utils.test import get_crawler
from tests.utils.decorators import coroutine_test

CALLS: list[str] = []


class MW1:
    async def process_spider_output(self, response, result):
        async for r in result:
            yield r

    def process_spider_exception(self, response, exception):
        CALLS.append("MW1")


class MW2:
    async def process_spider_output(self, response, result):
        async for r in result:
            yield r

    def process_spider_exception(self, response, exception):
        CALLS.append("MW2")


class MW3:
    async def process_spider_output(self, response, result):
        async for r in result:
            yield r

    def process_spider_exception(self, response, exception):
        CALLS.append("MW3")


def _callback_yield_then_raise() -> Any:
    yield {"foo": 1}
    raise ValueError("fake exception")


def _callback_raise() -> Any:
    raise ValueError("fake exception")
    yield  # pylint: disable=unreachable


@pytest.mark.parametrize("callback", [_callback_yield_then_raise, _callback_raise])
@coroutine_test
async def test_process_spider_exception_called_once(callback):
    CALLS.clear()
    crawler = get_crawler(
        Spider,
        {
            "SPIDER_MIDDLEWARES_BASE": {},
            "SPIDER_MIDDLEWARES": {MW1: 10, MW2: 20, MW3: 30},
        },
    )
    crawler.spider = crawler._create_spider("foo")
    mwman = build_from_crawler(SpiderMiddlewareManager, crawler)
    request = Request("http://example.com/index.html")
    response = Response(request.url, request=request)

    async def scrape_func(response, request):
        return callback()

    it = await mwman.scrape_response_async(scrape_func, response, request)
    with pytest.raises(ValueError, match="fake exception"):
        await collect_asyncgen(it)
    assert CALLS == ["MW3", "MW2", "MW1"]
