from scrapy.utils.url import strip_url


def test_strip_default_port_keeps_password_equal_to_port():
    assert (
        strip_url("http://user:80@example.com:80/p", strip_credentials=False)
        == "http://user:80@example.com/p"
    )


def test_strip_default_port_without_credentials():
    assert strip_url("http://example.com:80/p") == "http://example.com/p"
