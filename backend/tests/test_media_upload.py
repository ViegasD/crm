import unittest
from io import BytesIO
from unittest.mock import patch

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.api.v1.media import upload_media


class MediaUploadTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_uses_synchronous_storage_helper(self):
        file = UploadFile(filename="smoke.pdf", file=BytesIO(b"%PDF-smoke"),
                          headers=Headers({"content-type": "application/pdf"}))
        with patch("app.api.v1.media.ensure_bucket") as ensure, \
             patch("app.api.v1.media.upload_file") as upload, \
             patch("app.api.v1.media.generate_presigned_url", return_value="https://storage.test/object"):
            result = await upload_media(file, "workspace", object())
        ensure.assert_called_once()
        upload.assert_called_once()
        self.assertEqual(result["url"], "https://storage.test/object")
