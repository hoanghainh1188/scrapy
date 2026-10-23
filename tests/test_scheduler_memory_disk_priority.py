"""Request priority must be honoured across the memory and disk queues of the
default scheduler (https://github.com/scrapy/scrapy/issues/3666)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scrapy.http import Request
from tests.test_scheduler import create_scheduler
from tests.utils.decorators import coroutine_test

if TYPE_CHECKING:
    from pathlib import Path


_PQ = "scrapy.pqueues.ScrapyPriorityQueue"


def _unserializable(url: str, priority: int) -> Request:
    return Request(url, meta={"foo": lambda: "bar"}, priority=priority)


@coroutine_test
async def test_disk_request_with_higher_priority_comes_first(tmp_path: Path) -> None:
    async with create_scheduler(_PQ, tmp_path) as scheduler:
        scheduler.enqueue_request(_unserializable("http://a.com/mqs-0", 0))
        scheduler.enqueue_request(Request("http://a.com/dqs-100", priority=100))
        assert scheduler.stats is not None
        assert scheduler.stats.get_value("scheduler/enqueued/memory") == 1
        assert scheduler.stats.get_value("scheduler/enqueued/disk") == 1

        first = scheduler.next_request()
        second = scheduler.next_request()
        assert first is not None
        assert second is not None
        assert first.url == "http://a.com/dqs-100"
        assert second.url == "http://a.com/mqs-0"
        assert scheduler.next_request() is None


@coroutine_test
async def test_memory_request_with_higher_priority_comes_first(
    tmp_path: Path,
) -> None:
    async with create_scheduler(_PQ, tmp_path) as scheduler:
        scheduler.enqueue_request(Request("http://a.com/dqs-0", priority=0))
        scheduler.enqueue_request(_unserializable("http://a.com/mqs-100", 100))

        urls = []
        while (request := scheduler.next_request()) is not None:
            urls.append(request.url)
        assert urls == ["http://a.com/mqs-100", "http://a.com/dqs-0"]


@coroutine_test
async def test_mixed_priorities_dequeued_in_order(tmp_path: Path) -> None:
    async with create_scheduler(_PQ, tmp_path) as scheduler:
        scheduler.enqueue_request(_unserializable("http://a.com/m-1", 1))
        scheduler.enqueue_request(Request("http://a.com/d-3", priority=3))
        scheduler.enqueue_request(_unserializable("http://a.com/m-2", 2))
        scheduler.enqueue_request(Request("http://a.com/d-0", priority=0))
        # Same priority: memory takes precedence over disk.
        scheduler.enqueue_request(Request("http://a.com/d-2", priority=2))

        urls = []
        while (request := scheduler.next_request()) is not None:
            urls.append(request.url)
        assert urls == [
            "http://a.com/d-3",
            "http://a.com/m-2",
            "http://a.com/d-2",
            "http://a.com/m-1",
            "http://a.com/d-0",
        ]
