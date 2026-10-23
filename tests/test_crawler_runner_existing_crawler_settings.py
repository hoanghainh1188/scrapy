from __future__ import annotations

from scrapy.crawler import AsyncCrawlerRunner, Crawler, CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.spider import DefaultSpider


def _crawler() -> Crawler:
    class CustomSpider(DefaultSpider):
        custom_settings = {"TEST_SPIDER": "spider", "TEST_BOTH": "spider"}

    settings = Settings({"TEST_CRAWLER": "crawler", "TEST_TIE": "crawler"})
    return Crawler(CustomSpider, settings)


def test_runner_settings_used_as_defaults_for_crawler() -> None:
    runner = CrawlerRunner(
        {
            "TEST_RUNNER": "runner",
            "TEST_CRAWLER": "runner",
            "TEST_TIE": "runner",
            "TEST_BOTH": "runner",
        }
    )
    crawler = _crawler()
    assert runner.create_crawler(crawler) is crawler
    assert crawler.settings["TEST_RUNNER"] == "runner"
    # Same or higher priority in the crawler wins.
    assert crawler.settings["TEST_CRAWLER"] == "crawler"
    assert crawler.settings["TEST_TIE"] == "crawler"
    assert crawler.settings["TEST_SPIDER"] == "spider"
    assert crawler.settings["TEST_BOTH"] == "spider"


def test_runner_higher_priority_settings_override_crawler() -> None:
    settings = Settings()
    settings.set("TEST_CRAWLER", "runner", priority="cmdline")
    runner = AsyncCrawlerRunner(settings)
    crawler = _crawler()
    runner.create_crawler(crawler)
    assert crawler.settings["TEST_CRAWLER"] == "runner"
    assert crawler.settings.getpriority("TEST_CRAWLER") == 40
