import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit

from app.core import minio


class MinioEndpointTests(unittest.TestCase):
    def setUp(self):
        self.settings = SimpleNamespace(
            minio_endpoint="minio:9000",
            minio_public_endpoint=None,
            minio_use_ssl=False,
            minio_access_key="test-access-key",
            minio_secret_key="test-secret-key",
        )
        settings_patch = patch.object(minio, "settings", self.settings)
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        for name in ("_client", "_presign_client"):
            cache_patch = patch.object(minio, name, None)
            cache_patch.start()
            self.addCleanup(cache_patch.stop)

    def build_client(self, endpoint):
        client = minio._build_client(endpoint)
        self.addCleanup(client.close)
        return client

    def test_explicit_schemes_override_shared_ssl_setting(self):
        for endpoint, use_ssl in (
            ("https://storage.example.test", False),
            ("http://minio:9000", True),
        ):
            with self.subTest(endpoint=endpoint, use_ssl=use_ssl):
                self.settings.minio_use_ssl = use_ssl
                self.assertEqual(self.build_client(endpoint).meta.endpoint_url, endpoint)

    def test_bare_host_preserves_shared_ssl_setting(self):
        for use_ssl, expected in (
            (False, "http://minio:9000"),
            (True, "https://minio:9000"),
        ):
            with self.subTest(use_ssl=use_ssl):
                self.settings.minio_use_ssl = use_ssl
                self.assertEqual(self.build_client("minio:9000").meta.endpoint_url, expected)

    def test_internal_http_and_public_https_clients_are_independent(self):
        self.settings.minio_public_endpoint = "https://storage.example.test"
        internal = minio.get_minio_client()
        self.addCleanup(internal.close)
        public = minio.get_minio_presign_client()
        self.addCleanup(public.close)

        self.assertEqual(internal.meta.endpoint_url, "http://minio:9000")
        self.assertEqual(public.meta.endpoint_url, "https://storage.example.test")
        signed_url = urlsplit(minio.generate_presigned_url("media", "sample.txt"))
        self.assertEqual(signed_url.scheme, "https")
        self.assertEqual(signed_url.netloc, "storage.example.test")
        self.assertIs(minio.get_minio_client(), internal)
        self.assertIs(minio.get_minio_presign_client(), public)

    def test_presign_client_falls_back_to_internal_endpoint(self):
        self.settings.minio_endpoint = "https://storage.example.test"
        client = minio.get_minio_presign_client()
        self.addCleanup(client.close)
        self.assertEqual(client.meta.endpoint_url, "https://storage.example.test")


if __name__ == "__main__":
    unittest.main()
