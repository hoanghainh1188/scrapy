from __future__ import annotations

from ipaddress import IPv4Address
from typing import TYPE_CHECKING

import pytest

from scrapy.utils.test import get_crawler
from tests.spiders import SingleRequestSpider
from tests.utils.decorators import coroutine_test

if TYPE_CHECKING:
    from tests.mockserver.http import MockServer


@pytest.mark.filterwarnings(
    r"ignore:.*You should use cryptography's X\.509 APIs:DeprecationWarning"
)
@coroutine_test
async def test_certificate_and_ip_address_with_empty_body(
    mockserver: MockServer,
) -> None:
    crawler = get_crawler(SingleRequestSpider)
    url = mockserver.url("/status?n=200", is_secure=True)
    await crawler.crawl_async(seed=url, mockserver=mockserver)
    assert isinstance(crawler.spider, SingleRequestSpider)
    response = crawler.spider.meta["responses"][0]
    assert response.body == b""
    assert response.certificate is not None
    assert isinstance(response.ip_address, IPv4Address)
