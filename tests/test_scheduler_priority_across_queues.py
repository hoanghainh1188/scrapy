from __future__ import annotations

from typing import TYPE_CHECKING

from scrapy.http import Request
from tests.test_scheduler import create_scheduler
from tests.utils.decorators import coroutine_test

if TYPE_CHECKING:
    from pathlib import Path


@coroutine_test
async def test_priority_across_memory_and_disk_queues(tmp_path: Path) -> None:
    async with create_scheduler(
        "scrapy.pqueues.ScrapyPriorityQueue", tmp_path
    ) as scheduler:
        scheduler.enqueue_request(
            Request(
                "http://a.com/mqs-0-unserializable",
                meta={"foo": lambda: "bar"},
                priority=0,
            )
        )
        scheduler.enqueue_request(Request("http://a.com/dqs-100", priority=100))
        scheduler.enqueue_request(Request("http://a.com/dqs-0", priority=0))
        scheduler.enqueue_request(
            Request(
                "http://a.com/mqs-200-unserializable",
                meta={"foo": lambda: "bar"},
                priority=200,
            )
        )
        urls = []
        while (request := scheduler.next_request()) is not None:
            urls.append(request.url)
        assert urls[:2] == [
            "http://a.com/mqs-200-unserializable",
            "http://a.com/dqs-100",
        ]
        assert set(urls[2:]) == {
            "http://a.com/mqs-0-unserializable",
            "http://a.com/dqs-0",
        }
