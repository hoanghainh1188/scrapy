import pytest

from scrapy.core.downloader.contextfactory import _ScrapyClientContextFactory


@pytest.mark.parametrize("verify_certificates", [True, False])
def test_emoji_domain_tls_options(verify_certificates):
    factory = _ScrapyClientContextFactory(verify_certificates=verify_certificates)
    options = factory.creatorForNetloc(b"xn--i-7iq.ws", 443)
    assert options is not None
