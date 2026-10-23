from scrapy.utils.url import strip_url


def test_strip_default_port_keeps_password_equal_to_port():
    assert (
        strip_url("http://user:80@example.com:80/p", strip_credentials=False)
        == "http://user:80@example.com/p"
    )


def test_strip_default_port_https_password_equal_to_port():
    assert (
        strip_url("https://user:443@example.com:443/p", strip_credentials=False)
        == "https://user:443@example.com/p"
    )


def test_strip_default_port_ipv6():
    assert strip_url("http://[::1]:80/p") == "http://[::1]/p"
