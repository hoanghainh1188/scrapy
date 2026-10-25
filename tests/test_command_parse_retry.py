from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.utils.bases.commands import TestProjectBase
from tests.utils.cmdline import proc

if TYPE_CHECKING:
    from pathlib import Path

    from tests.mockserver.http import MockServer


class TestParseCommandRetry(TestProjectBase):
    spider_name = "retry_spider"

    @pytest.fixture(autouse=True)
    def create_files(self, proj_path: Path) -> None:
        proj_mod_path = proj_path / self.project_name
        (proj_mod_path / "spiders" / "retryspider.py").write_text(
            f"""
import scrapy


class RetrySpider(scrapy.Spider):
    name = "{self.spider_name}"

    custom_settings = {{"DOWNLOAD_DELAY": 0}}

    async def start(self):
        return
        yield

    def parse(self, response):
        if response.meta.get("retried"):
            yield {{"done": True}}
            return
        response.meta["retried"] = True
        yield response.request.replace(dont_filter=True)
"""
        )

    def test_retry_without_callback(
        self, proj_path: Path, mockserver: MockServer
    ) -> None:
        _, out, stderr = proc(
            "parse",
            "--spider",
            self.spider_name,
            "-d",
            "2",
            mockserver.url("/html"),
            cwd=proj_path,
        )
        assert "RecursionError" not in stderr
        assert "'done': True" in out
