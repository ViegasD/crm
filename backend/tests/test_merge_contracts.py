"""Regression checks for the local/QA integration; no external services needed."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models.webhook import WebhookEvent
from app.services import webhook_event_service


class MigrationGraphTests(unittest.TestCase):
    def test_combined_history_has_one_upgrade_target(self):
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        self.assertEqual(len(ScriptDirectory.from_config(config).get_heads()), 1)

    def test_initial_dispatch_and_retry_share_the_persisted_payload(self):
        event = WebhookEvent(provider="meta_cloud", raw_payload={"entry": [{"id": "sample"}]})
        self.assertEqual(event.payload, event.raw_payload)
        event.payload = {"entry": []}
        self.assertEqual(event.raw_payload, {"entry": []})


class WebhookPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_ingress_retains_retry_metadata_without_secret_headers(self):
        saved = []

        class Session:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            def add(self, event):
                saved.append(event)

            async def commit(self):
                pass

        with patch.object(webhook_event_service, "AsyncSessionLocal", Session):
            await webhook_event_service.record_webhook_event(
                provider="meta_cloud", payload={"entry": []}, signature="sha256=test",
                headers={"content-type": "application/json", "authorization": "secret", "apikey": "secret"},
            )
        event = saved[0]
        self.assertEqual(event.signature_hash, hashlib.sha256(b"sha256=test").hexdigest())
        self.assertEqual(event.headers, {"content-type": "application/json"})
        self.assertEqual(event.payload, {"entry": []})


if __name__ == "__main__":
    unittest.main()
