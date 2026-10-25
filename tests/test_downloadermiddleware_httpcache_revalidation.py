from __future__ import annotations

import email.utils
import shutil
import tempfile
from unittest import mock

from scrapy.downloadermiddlewares.httpcache import HttpCacheMiddleware
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from scrapy.utils.misc import build_from_crawler
from scrapy.utils.test import get_crawler

T0 = 1_700_000_000


def _date(offset: float) -> str:
    return email.utils.formatdate(T0 + offset, usegmt=True)


def test_request_max_age_honored_after_revalidation():
    tmpdir = tempfile.mkdtemp()
    try:
        settings = {
            "HTTPCACHE_ENABLED": True,
            "HTTPCACHE_DIR": tmpdir,
            "HTTPCACHE_POLICY": "scrapy.extensions.httpcache.RFC2616Policy",
            "HTTPCACHE_STORAGE": "scrapy.extensions.httpcache.FilesystemCacheStorage",
        }
        crawler = get_crawler(Spider, settings)
        crawler.spider = crawler._create_spider("example.com")
        crawler.stats.open_spider()
        mw = build_from_crawler(HttpCacheMiddleware, crawler)
        mw.spider_opened(crawler.spider)
        url = "http://www.example.com"

        def request() -> Request:
            return Request(url, headers={"Cache-Control": "max-age=60"})

        try:
            # First-hand response is stored at T0.
            with mock.patch("scrapy.extensions.httpcache.time", return_value=T0):
                req = request()
                assert mw.process_request(req) is None
                resp = Response(
                    url,
                    status=200,
                    headers={
                        "Date": _date(0),
                        "Cache-Control": "max-age=3600",
                        "ETag": "abc",
                    },
                    body=b"body",
                )
                mw.process_response(req, resp)

            # Stale for max-age=60 at T0+120: revalidated with a 304.
            with mock.patch("scrapy.extensions.httpcache.time", return_value=T0 + 120):
                req = request()
                assert mw.process_request(req) is None
                assert "cached_response" in req.meta
                not_modified = Response(url, status=304, headers={"Date": _date(120)})
                result = mw.process_response(req, not_modified)
                assert result.status == 200

            # Validated 10 seconds ago: must be served from the cache.
            with mock.patch("scrapy.extensions.httpcache.time", return_value=T0 + 130):
                req = request()
                result = mw.process_request(req)
                assert result is not None
                assert "cached" in result.flags
        finally:
            mw.spider_closed(crawler.spider)
            crawler.stats.close_spider()
    finally:
        shutil.rmtree(tmpdir)
