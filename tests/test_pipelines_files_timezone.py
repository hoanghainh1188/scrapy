from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from unittest import mock

import pytest

from scrapy.pipelines.files import FTPFilesStore, GCSFilesStore, S3FilesStore

UTC_STAMP = datetime(2019, 12, 1, tzinfo=timezone.utc).timestamp()


@pytest.fixture
def non_utc_timezone():
    if not hasattr(time, "tzset"):
        pytest.skip("time.tzset is not available")
    old = os.environ.get("TZ")
    os.environ["TZ"] = "Etc/GMT-5"  # UTC+5
    time.tzset()
    yield
    if old is None:
        del os.environ["TZ"]
    else:
        os.environ["TZ"] = old
    time.tzset()


def test_s3_last_modified_is_utc(non_utc_timezone):
    boto_key = {
        "ETag": '"abc"',
        "LastModified": datetime(2019, 12, 1, tzinfo=timezone.utc),
    }
    stat = S3FilesStore._onsuccess(boto_key)
    assert stat["last_modified"] == UTC_STAMP


def test_gcs_last_modified_is_utc(non_utc_timezone):
    blob = mock.Mock()
    blob.md5_hash = "q80="
    blob.updated = datetime(2019, 12, 1, tzinfo=timezone.utc)
    stat = GCSFilesStore._onsuccess(blob)
    assert stat["last_modified"] == UTC_STAMP


@pytest.mark.parametrize("reply", ["213 20191201000000", "213 20191201000000.123"])
def test_ftp_last_modified_is_utc(non_utc_timezone, reply):
    store = FTPFilesStore.__new__(FTPFilesStore)
    store.host = "localhost"
    store.port = 21
    store.username = "u"
    store.password = "p"
    store.basedir = ""
    with mock.patch("scrapy.pipelines.files.FTP") as ftp_cls:
        ftp = ftp_cls.return_value.__enter__.return_value
        ftp.voidcmd.return_value = reply
        stat = store._stat_file("f")
    assert stat["last_modified"] == pytest.approx(UTC_STAMP, abs=1)
