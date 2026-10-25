import pytest

from scrapy.core.downloader.contextfactory import _ScrapyClientContextFactory


@pytest.mark.parametrize("verify_certificates", [False, True])
def test_creator_for_emoji_domain(verify_certificates):
    factory = _ScrapyClientContextFactory(verify_certificates=verify_certificates)
    creator = factory.creatorForNetloc(b"xn--i-7iq.ws", 443)
    assert creator is not None
