from __future__ import annotations

import asyncio
import tempfile

from scrapy import Spider
from scrapy.extensions.feedexport import FeedExporter
from scrapy.utils.test import get_crawler
from tests.utils.decorators import coroutine_test


class RecordingStorage:
    stored: list[bytes] = []

    def __init__(self, uri, *, feed_options=None):
        pass

    def open(self, spider):
        return tempfile.TemporaryFile()

    def store(self, file):
        file.seek(0)
        RecordingStorage.stored.append(file.read())
        file.close()


@coroutine_test
async def test_batch_stored_when_full_not_at_spider_close():
    RecordingStorage.stored = []
    crawler = get_crawler(
        settings_dict={
            "FEEDS": {"mem:///out_%(batch_id)d": {"format": "jsonlines"}},
            "FEED_STORAGES": {"mem": RecordingStorage},
            "FEED_EXPORT_BATCH_ITEM_COUNT": 1,
        }
    )
    exporter = FeedExporter.from_crawler(crawler)
    spider = Spider("default")
    spider.crawler = crawler
    exporter.open_spider(spider)
    exporter.item_scraped({"a": 1}, spider)
    for _ in range(5):
        await asyncio.sleep(0)
    assert RecordingStorage.stored == [b'{"a": 1}\n']
    await exporter.close_spider(spider)
