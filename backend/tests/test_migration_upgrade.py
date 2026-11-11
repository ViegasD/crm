"""PostgreSQL integration checks. Set CRM2_MIGRATION_TEST_URL to a disposable
Postgres admin database URL; each case creates and drops its own database.

Run from backend: python -m unittest tests.test_migration_upgrade -v
Never point this suite at an application database/user: CREATEDB is required.
"""
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


@unittest.skipUnless(os.environ.get("CRM2_MIGRATION_TEST_URL"), "requires disposable PostgreSQL")
class MigrationUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.admin = create_engine(os.environ["CRM2_MIGRATION_TEST_URL"], isolation_level="AUTOCOMMIT")
        self.database = "crm2_migration_test_" + uuid4().hex
        with self.admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{self.database}"'))
        url = make_url(os.environ["CRM2_MIGRATION_TEST_URL"]).set(database=self.database)
        self.engine = create_engine(url)
        async_url = url.set(drivername="postgresql+asyncpg")
        self.env = patch.dict(os.environ, {"DATABASE_URL": async_url.render_as_string(hide_password=False), "DEBUG": "false"})
        self.env.start()
        self.config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        self.config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
        self.addCleanup(self.cleanup_database)

    def cleanup_database(self):
        self.env.stop()
        self.engine.dispose()
        with self.admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE "{self.database}" WITH (FORCE)'))
        self.admin.dispose()

    def assert_current_schema(self):
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT version_num FROM alembic_version")).scalars().all(), ["202611110002"])
            conn.execute(text("SELECT 'sticker'::messagetype, 'dead_letter'::webhookeventstatus"))
        self.assertIn("media_uploads", inspect(self.engine).get_table_names())
        columns = {c["name"] for c in inspect(self.engine).get_columns("webhook_events")}
        self.assertTrue({"raw_payload", "updated_at", "signature_hash", "attempts", "headers"} <= columns)

    def seed_webhook(self, column):
        self.event_id = uuid4()
        columns = {c["name"] for c in inspect(self.engine).get_columns("webhook_events")}
        extra_columns = ""
        extra_values = ""
        if "headers" in columns:
            extra_columns = ", headers, attempts, max_attempts"
            extra_values = ", '{}'::jsonb, 0, 8"
        with self.engine.begin() as conn:
            conn.execute(text(f"INSERT INTO webhook_events (id, provider, {column}, status{extra_columns}) VALUES (:id, 'meta_cloud', '{{\"entry\":[{{\"id\":\"historical\"}}]}}'::jsonb, 'received'{extra_values})"), {"id": self.event_id})

    def assert_webhook_retained(self):
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT raw_payload FROM webhook_events WHERE id = :id"), {"id": self.event_id}).scalar_one(), {"entry": [{"id": "historical"}]})
        # New application writes must work even when a legacy payload column remains.
        from app.models.webhook import WebhookEvent
        new_id = uuid4()
        with self.engine.begin() as conn:
            conn.execute(WebhookEvent.__table__.insert().values(id=new_id, provider="meta_cloud", raw_payload={"new": True}))
            self.assertEqual(conn.execute(text("SELECT raw_payload FROM webhook_events WHERE id = :id"), {"id": new_id}).scalar_one(), {"new": True})

    def test_empty_database_upgrades_to_head(self):
        command.upgrade(self.config, "head")
        self.assert_current_schema()

    def test_existing_merged_database_adds_media_registry(self):
        command.upgrade(self.config, "202611110001")
        # The legacy baseline may create current metadata. Remove only this new
        # empty table to represent the schema deployed before the media change.
        with self.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS media_uploads"))
        command.upgrade(self.config, "head")
        self.assert_current_schema()

    def test_local_history_upgrades_and_preserves_raw_payload(self):
        # The local branch had the explicit initial schema and webhook table.
        command.upgrade(self.config, "7a4d2f9c1b3e")
        command.stamp(self.config, "c1d8e6a4f2b0")
        command.upgrade(self.config, "202605221215")
        self.seed_webhook("raw_payload")
        command.upgrade(self.config, "head")
        self.assert_current_schema()
        self.assert_webhook_retained()

    def test_qa_history_upgrades_and_preserves_payload(self):
        command.upgrade(self.config, "202605250001")
        # Upstream's historical model called this column payload; create_all
        # imports today's models, so restore the actual upstream column shape.
        with self.engine.begin() as conn:
            conn.execute(text("ALTER TABLE webhook_events RENAME COLUMN raw_payload TO payload"))
        self.seed_webhook("payload")
        command.upgrade(self.config, "head")
        self.assert_current_schema()
        self.assert_webhook_retained()
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT payload FROM webhook_events WHERE id = :id"), {"id": self.event_id}).scalar_one(), {"entry": [{"id": "historical"}]})


if __name__ == "__main__":
    unittest.main()
