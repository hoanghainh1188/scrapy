from scrapy import Spider
from scrapy.crawler import Crawler, CrawlerRunner


class _Spider(Spider):
    name = "dummy"
    custom_settings = {"SPIDER_ONLY": "spider"}


def test_runner_settings_used_as_defaults_for_crawler():
    runner = CrawlerRunner({"FROM_RUNNER": "runner", "SHARED": "runner"})
    crawler = Crawler(_Spider, {"SHARED": "crawler", "FROM_CRAWLER": "crawler"})
    assert runner.create_crawler(crawler) is crawler
    assert crawler.settings["FROM_RUNNER"] == "runner"
    # settings explicitly given to the crawler are not overridden
    assert crawler.settings["SHARED"] == "crawler"
    assert crawler.settings["FROM_CRAWLER"] == "crawler"
    assert crawler.settings["SPIDER_ONLY"] == "spider"


def test_runner_settings_do_not_override_spider_settings():
    runner = CrawlerRunner({"SPIDER_ONLY": "runner"})
    crawler = Crawler(_Spider)
    runner.create_crawler(crawler)
    assert crawler.settings["SPIDER_ONLY"] == "spider"
