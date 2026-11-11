import unittest
from io import BytesIO
from unittest.mock import patch
from types import SimpleNamespace
from uuid import uuid4

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.api.v1.media import upload_media


class MediaUploadTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_uses_synchronous_storage_helper(self):
        file = UploadFile(filename="smoke.pdf", file=BytesIO(b"%PDF-smoke"),
                          headers=Headers({"content-type": "application/pdf"}))
        with patch("app.api.v1.media.ensure_bucket") as ensure, \
             patch("app.api.v1.media.upload_file") as upload, \
             patch("app.api.v1.media.download_url", return_value="/api/v1/media/download?token=fixture"):
            from unittest.mock import AsyncMock, Mock
            db = SimpleNamespace(add=Mock(), flush=AsyncMock())
            result = await upload_media(file, uuid4(), SimpleNamespace(id=uuid4()), db)
        ensure.assert_called_once()
        upload.assert_called_once()
        self.assertEqual(result["url"], "/api/v1/media/download?token=fixture")
        db.add.assert_called_once()
