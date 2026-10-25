from __future__ import annotations

from typing import Any

from scrapy import Request, Spider
from scrapy.utils.test import get_crawler
from tests.utils.decorators import coroutine_test

OUTPUT_SEEN: list[Any] = []


class FailingDownloaderMiddleware:
    def process_request(self, request):
        raise ValueError("downloader middleware failure")


class RecordingSpiderMiddleware:
    async def process_spider_output(self, response, result):
        async for r in result:
            OUTPUT_SEEN.append(r)
            yield r


class ErrbackSpider(Spider):
    name = "errback_spider"
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {FailingDownloaderMiddleware: 10},
        "SPIDER_MIDDLEWARES": {RecordingSpiderMiddleware: 10},
    }

    async def start(self):
        yield Request("data:,", callback=self.parse, errback=self.errback)

    def parse(self, response):
        yield {"from": "parse"}

    def errback(self, failure):
        yield {"from": "errback"}


@coroutine_test
async def test_errback_output_goes_through_process_spider_output() -> None:
    OUTPUT_SEEN.clear()
    crawler = get_crawler(ErrbackSpider)
    await crawler.crawl_async()
    assert OUTPUT_SEEN == [{"from": "errback"}]
    assert crawler.stats.get_value("item_scraped_count") == 1
