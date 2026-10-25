from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapy import Spider
from scrapy.utils.asyncio import sleep
from scrapy.utils.test import get_crawler
from tests.utils.decorators import coroutine_test

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

processed: list[Any] = []


class SlowPipeline:
    async def process_item(self, item: Any) -> Any:
        await sleep(0.5)
        processed.append(item)
        return item


class StartItemsSpider(Spider):
    name = "test"

    async def start(self) -> AsyncIterator[Any]:
        yield {"a": 1}
        yield {"a": 2}


@coroutine_test
async def test_spider_waits_for_pipelines_of_start_items() -> None:
    processed.clear()
    crawler = get_crawler(
        StartItemsSpider,
        {"ITEM_PIPELINES": {SlowPipeline: 1}},
    )
    await crawler.crawl_async()
    assert processed == [{"a": 1}, {"a": 2}]
