"""Regression tests for https://github.com/scrapy/scrapy/issues/4466

HTTP11DownloadHandler used to return responses without a body without
their TLS certificate and IP address.
"""

from __future__ import annotations

import socket
from ipaddress import IPv4Address
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest
from twisted.internet.ssl import Certificate

from scrapy.utils.test import get_crawler
from tests.spiders import SingleRequestSpider
from tests.utils.decorators import coroutine_test

if TYPE_CHECKING:
    from tests.mockserver.http import MockServer


pytestmark = pytest.mark.requires_reactor  # HTTP11DownloadHandler requires a reactor

SETTINGS = {
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler",
        "https": "scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler",
    }
}


@pytest.mark.filterwarnings(
    r"ignore:.*You should use cryptography's X\.509 APIs:DeprecationWarning"
)
@coroutine_test
async def test_empty_body_response_has_certificate(mockserver: MockServer) -> None:
    crawler = get_crawler(SingleRequestSpider, SETTINGS)
    url = mockserver.url("/status?n=200", is_secure=True)
    await crawler.crawl_async(seed=url, mockserver=mockserver)
    assert isinstance(crawler.spider, SingleRequestSpider)
    response = crawler.spider.meta["responses"][0]
    assert response.body == b""
    cert = response.certificate
    assert isinstance(cert, Certificate)
    assert cert.getSubject().commonName == b"localhost"
    assert cert.getIssuer().commonName == b"localhost"


@coroutine_test
async def test_empty_body_response_has_ip_address(mockserver: MockServer) -> None:
    crawler = get_crawler(SingleRequestSpider, SETTINGS)
    url = mockserver.url("/status?n=200")
    expected_netloc, _ = urlparse(url).netloc.split(":")
    await crawler.crawl_async(seed=url, mockserver=mockserver)
    assert isinstance(crawler.spider, SingleRequestSpider)
    response = crawler.spider.meta["responses"][0]
    assert response.body == b""
    assert isinstance(response.ip_address, IPv4Address)
    assert str(response.ip_address) == socket.gethostbyname(expected_netloc)


@coroutine_test
async def test_empty_body_plain_http_has_no_certificate(
    mockserver: MockServer,
) -> None:
    crawler = get_crawler(SingleRequestSpider, SETTINGS)
    url = mockserver.url("/status?n=200", is_secure=False)
    await crawler.crawl_async(seed=url, mockserver=mockserver)
    assert isinstance(crawler.spider, SingleRequestSpider)
    assert crawler.spider.meta["responses"][0].certificate is None
