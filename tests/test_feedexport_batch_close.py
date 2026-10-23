from __future__ import annotations

import asyncio
import tempfile

import scrapy
from scrapy.extensions.feedexport import FeedExporter
from scrapy.utils.asyncio import is_asyncio_available
from scrapy.utils.test import get_crawler
from tests.utils.decorators import coroutine_test


class RecordingStorage:
    stored: list[str] = []

    def __init__(self, uri, *, feed_options=None):
        self.uri = uri

    def open(self, spider):
        return tempfile.TemporaryFile()

    def store(self, file):
        RecordingStorage.stored.append(self.uri)
        file.close()


@coroutine_test
async def test_full_batch_is_finalized_before_spider_close():
    RecordingStorage.stored = []
    settings = {
        "FEEDS": {
            "mem:///batch-%(batch_id)d": {
                "format": "jsonlines",
                "batch_item_count": 2,
            },
        },
        "FEED_STORAGES": {"mem": RecordingStorage},
    }
    crawler = get_crawler(settings_dict=settings)
    feed_exporter = FeedExporter.from_crawler(crawler)
    spider = scrapy.Spider("default")
    spider.crawler = crawler

    feed_exporter.open_spider(spider)
    for i in range(2):
        feed_exporter.item_scraped({"n": i}, spider)
    if is_asyncio_available():
        await asyncio.sleep(0.1)

    # The first batch is full, so it must be stored before the spider closes.
    assert RecordingStorage.stored == ["mem:///batch-1"]

    await feed_exporter.close_spider(spider)
    assert RecordingStorage.stored == ["mem:///batch-1"]
