"""The spider must wait for the item pipelines to finish processing items
produced from Spider.start() before closing."""

from __future__ import annotations

from typing import Any

from twisted.internet.defer import Deferred

from scrapy import Spider, signals
from scrapy.utils.asyncio import call_later
from scrapy.utils.defer import maybe_deferred_to_future
from scrapy.utils.test import get_crawler

from .utils.decorators import coroutine_test

SLEEP_SECONDS = 0.5


async def _delay(seconds: float) -> None:
    d: Deferred[None] = Deferred()
    call_later(seconds, d.callback, None)
    await maybe_deferred_to_future(d)


class SlowPipeline:
    events: list[str]

    def open_spider(self) -> None:
        SlowPipeline.events = []

    async def process_item(self, item: Any) -> Any:
        await _delay(SLEEP_SECONDS)
        SlowPipeline.events.append(f"processed {item['id']}")
        return item

    def close_spider(self) -> None:
        SlowPipeline.events.append("close_spider")


class StartItemsSpider(Spider):
    name = "test"

    async def start(self):
        yield {"id": "a"}
        yield {"id": "b"}


@coroutine_test
async def test_spider_waits_for_start_item_pipelines() -> None:
    scraped: list[Any] = []

    def track_item(item, response, spider):
        scraped.append(item)

    crawler = get_crawler(
        StartItemsSpider,
        {"ITEM_PIPELINES": {SlowPipeline: 100}},
    )
    crawler.signals.connect(track_item, signals.item_scraped)
    await crawler.crawl_async()

    assert crawler.stats.get_value("finish_reason") == "finished"
    assert sorted(item["id"] for item in scraped) == ["a", "b"]
    assert crawler.stats.get_value("item_scraped_count") == 2
    assert SlowPipeline.events[-1] == "close_spider"
    assert sorted(SlowPipeline.events[:-1]) == ["processed a", "processed b"]
