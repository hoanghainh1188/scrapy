import pytest

from scrapy.pipelines.files import FilesPipeline, GCSFilesStore, S3FilesStore
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.test import get_crawler

pytest.importorskip("PIL")


@pytest.fixture(autouse=True)
def _restore_policies():
    s3, gcs = S3FilesStore.POLICY, GCSFilesStore.POLICY
    yield
    S3FilesStore.POLICY, GCSFilesStore.POLICY = s3, gcs


def test_images_store_acl_settings_are_used(tmp_path):
    settings = {
        "IMAGES_STORE": str(tmp_path),
        "IMAGES_STORE_S3_ACL": "public-read",
        "IMAGES_STORE_GCS_ACL": "publicRead",
        "FILES_STORE_S3_ACL": "files-acl",
        "FILES_STORE_GCS_ACL": "filesAcl",
    }
    ImagesPipeline.from_crawler(get_crawler(settings_dict=settings))
    assert S3FilesStore.POLICY == "public-read"
    assert GCSFilesStore.POLICY == "publicRead"


def test_images_store_gcs_acl_empty_is_none(tmp_path):
    settings = {"IMAGES_STORE": str(tmp_path), "IMAGES_STORE_GCS_ACL": ""}
    ImagesPipeline.from_crawler(get_crawler(settings_dict=settings))
    assert GCSFilesStore.POLICY is None


def test_files_store_acl_settings_are_used(tmp_path):
    settings = {
        "FILES_STORE": str(tmp_path),
        "FILES_STORE_S3_ACL": "files-acl",
        "FILES_STORE_GCS_ACL": "filesAcl",
        "IMAGES_STORE_S3_ACL": "public-read",
    }
    FilesPipeline.from_crawler(get_crawler(settings_dict=settings))
    assert S3FilesStore.POLICY == "files-acl"
    assert GCSFilesStore.POLICY == "filesAcl"
