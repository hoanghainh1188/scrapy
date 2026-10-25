import pytest

from scrapy.extensions.telnet import TelnetConsole
from scrapy.utils.test import get_crawler

pytestmark = pytest.mark.requires_reactor  # TelnetConsole requires a reactor


def test_stop_listening_without_start_listening() -> None:
    crawler = get_crawler(settings_dict={"TELNETCONSOLE_ENABLED": True})
    console = TelnetConsole(crawler)
    console.stop_listening()
