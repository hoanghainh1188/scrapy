from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from scrapy.pipelines.files import FilesPipeline, GCSFilesStore, S3FilesStore
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.test import get_crawler

if TYPE_CHECKING:
    from pathlib import Path

pytest.importorskip("PIL")


@pytest.fixture
def _restore_policies():
    s3_policy = S3FilesStore.POLICY
    gcs_policy = GCSFilesStore.POLICY
    yield
    S3FilesStore.POLICY = s3_policy
    GCSFilesStore.POLICY = gcs_policy


@pytest.mark.usefixtures("_restore_policies")
def test_images_store_acl_settings_are_used(tmp_path: Path) -> None:
    crawler = get_crawler(
        settings_dict={
            "IMAGES_STORE": str(tmp_path),
            "IMAGES_STORE_S3_ACL": "public-read",
            "IMAGES_STORE_GCS_ACL": "publicRead",
        }
    )
    ImagesPipeline.from_crawler(crawler)
    assert S3FilesStore.POLICY == "public-read"
    assert GCSFilesStore.POLICY == "publicRead"


@pytest.mark.usefixtures("_restore_policies")
def test_images_store_acl_defaults_ignore_files_acl(tmp_path: Path) -> None:
    crawler = get_crawler(
        settings_dict={
            "IMAGES_STORE": str(tmp_path),
            "FILES_STORE_S3_ACL": "public-read",
            "FILES_STORE_GCS_ACL": "publicRead",
        }
    )
    ImagesPipeline.from_crawler(crawler)
    assert S3FilesStore.POLICY == "private"
    assert GCSFilesStore.POLICY is None


@pytest.mark.usefixtures("_restore_policies")
def test_files_store_acl_settings_are_used(tmp_path: Path) -> None:
    crawler = get_crawler(
        settings_dict={
            "FILES_STORE": str(tmp_path),
            "FILES_STORE_S3_ACL": "public-read",
            "FILES_STORE_GCS_ACL": "publicRead",
            "IMAGES_STORE_S3_ACL": "other",
            "IMAGES_STORE_GCS_ACL": "other",
        }
    )
    FilesPipeline.from_crawler(crawler)
    assert S3FilesStore.POLICY == "public-read"
    assert GCSFilesStore.POLICY == "publicRead"
