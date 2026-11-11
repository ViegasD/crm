"""Media ownership and revocable download regressions on disposable Postgres."""
import os
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

import test_authorization as auth
from app.models.conversation import Message
from app.models.media import MediaUpload
from app.models.workspace import UserWorkspaceMembership
from app.services.media_access import download_url
from app.models.contact import ContactPhone
from app.models.conversation import CannedResponse
from app.models.macros import Macro, MacroAction


@unittest.skipUnless(os.environ.get("CRM2_MIGRATION_TEST_URL"), "requires disposable PostgreSQL")
class MediaAuthorizationTests(unittest.TestCase):
    setUpClass = classmethod(auth.AuthorizationTests.setUpClass.__func__)
    tearDownClass = classmethod(auth.AuthorizationTests.tearDownClass.__func__)
    headers = auth.AuthorizationTests.headers

    def setUp(self):
        auth.AuthorizationTests.setUp(self)
        self.client._transport.raise_server_exceptions = True
        patcher = patch("app.services.security_audit_service.AsyncSessionLocal", self.sessions)
        patcher.start()
        self.addCleanup(patcher.stop)

    def upload(self, user=None, filename="fixture.pdf"):
        with patch("app.api.v1.media.ensure_bucket"), patch("app.api.v1.media.upload_file"):
            return self.client.post("/api/v1/media/upload", params={"workspace_id": str(self.ws)},
                headers=self.headers(user or self.admin_id), files={"file": (filename, b"%PDF-fixture", "application/pdf")})

    def test_outsider_upload_is_denied_before_storage(self):
        with patch("app.api.v1.media.upload_file") as storage:
            r = self.client.post("/api/v1/media/upload", params={"workspace_id": str(self.ws)},
                headers=self.headers(self.outsider_id), files={"file": ("fixture.pdf", b"%PDF-fixture", "application/pdf")})
            self.assertEqual(r.status_code, 403, r.text)
            storage.assert_not_called()

    def test_draft_upload_is_owned_and_cannot_be_claimed_by_another_member(self):
        r = self.upload(); self.assertEqual(r.status_code, 200, r.text)
        key = r.json()["key"]
        for user, expected in [(self.admin_id, 200), (self.agent_id, 404), (self.outsider_id, 404)]:
            response = self.client.get("/api/v1/media/presign", params={"key": key}, headers=self.headers(user))
            self.assertEqual(response.status_code, expected, response.text)
        r = self.client.post(self.prefix+f"/conversations/{self.public}/messages", headers=self.headers(self.agent_id),
            json={"is_note": True, "attachments": [{"key": key}]})
        self.assertEqual(r.status_code, 404, r.text)

    def test_attach_canonicalizes_metadata_and_rejects_other_conversation(self):
        key = self.upload().json()["key"]
        with patch("app.services.presence_idle.mark_agent_active"):
            r = self.client.post(self.prefix+f"/conversations/{self.conv}/messages", headers=self.headers(self.admin_id),
                json={"is_note": True, "attachments": [{"key": key, "bucket": "foreign", "url": "https://evil.test/", "name": "forged", "sizeBytes": 1}]})
        self.assertEqual(r.status_code, 201, r.text)
        attachment = r.json()["attachments"][0]
        self.assertEqual(attachment["name"], "fixture.pdf")
        self.assertEqual(attachment["sizeBytes"], len(b"%PDF-fixture"))
        self.assertNotIn("evil.test", str(attachment))
        r = self.client.post(self.prefix+f"/conversations/{self.public}/messages", headers=self.headers(self.admin_id),
            json={"is_note": True, "attachments": [{"key": key}]})
        self.assertEqual(r.status_code, 404, r.text)

    def test_download_capability_rechecks_membership_and_conversation_access(self):
        key = self.upload().json()["key"]
        r = self.client.post(self.prefix+f"/conversations/{self.conv}/messages", headers=self.headers(self.admin_id),
            json={"is_note": True, "attachments": [{"key": key}]})
        self.assertEqual(r.status_code, 201, r.text)
        url = r.json()["attachments"][0]["url"]
        self.assertTrue(url.startswith("/api/v1/media/download?"), url)
        with patch("app.api.v1.media.read_file", return_value=b"%PDF-fixture"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.content, b"%PDF-fixture")
            with Session(self.engine) as db:
                db.get(auth.Conversation, self.conv).assignee_id = self.agent_id; db.commit()
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_legacy_attachment_is_readable_only_through_visible_message(self):
        key = f"{self.ws}/{uuid4()}/legacy.pdf"
        with Session(self.engine) as db:
            db.add(Message(workspace_id=self.ws, conversation_id=self.conv, sender_type="agent", sender_id=self.admin_id,
                origin="crm_agent", type="file", attachments=[{"key": key, "bucket": "crm-media", "url": "https://old.test/signed", "name": "legacy.pdf"}]))
            db.commit()
        for user, expected in [(self.admin_id, 200), (self.agent_id, 404)]:
            r = self.client.get("/api/v1/media/presign", params={"key": key}, headers=self.headers(user))
            self.assertEqual(r.status_code, expected, r.text)
            if expected == 200:
                self.assertTrue(r.json()["url"].startswith("/api/v1/media/download?"))
        r = self.client.get(self.prefix+f"/conversations/{self.conv}/messages", headers=self.headers(self.admin_id))
        self.assertNotIn("old.test", r.text)

    def test_external_url_or_unknown_key_cannot_be_sent(self):
        for attachment in [{"url": "http://internal.test/private"}, {"key": f"{self.ws}/{uuid4()}/unknown.pdf"}, {"key": "../secret"}]:
            with self.subTest(attachment=attachment):
                r = self.client.post(self.prefix+f"/conversations/{self.public}/messages", headers=self.headers(self.admin_id),
                    json={"is_note": True, "attachments": [attachment]})
                self.assertIn(r.status_code, [400, 404], r.text)

    def test_upload_rejects_path_filename_and_limits_read(self):
        for name in ["../escape.pdf", "folder\\escape.pdf"]:
            r = self.upload(filename=name)
            self.assertEqual(r.status_code, 400, r.text)

    def test_draft_expiration_blocks_presign_download_and_linking(self):
        result = self.upload().json()
        with Session(self.engine) as db:
            upload = db.query(MediaUpload).filter_by(key=result["key"]).one()
            upload.expires_at = datetime.now(timezone.utc)-timedelta(seconds=1); db.commit()
        h = self.headers(self.admin_id)
        self.assertEqual(self.client.get("/api/v1/media/presign", params={"key": result["key"]}, headers=h).status_code, 404)
        self.assertEqual(self.client.get(result["url"]).status_code, 404)
        r = self.client.post(self.prefix+f"/conversations/{self.conv}/messages", headers=h,
            json={"is_note": True, "attachments": [{"key": result["key"]}]})
        self.assertEqual(r.status_code, 404, r.text)

    def test_download_rejects_removed_member_tampered_or_wrong_type_token(self):
        result = self.upload().json()
        with Session(self.engine) as db:
            db.query(UserWorkspaceMembership).filter_by(workspace_id=self.ws, user_id=self.admin_id).delete(); db.commit()
        with patch("app.api.v1.media.read_file") as storage:
            self.assertIn(self.client.get(result["url"]).status_code, [403, 404])
            self.assertEqual(self.client.get(result["url"]+"tampered").status_code, 401)
            from app.core.security import create_access_token
            r = self.client.get("/api/v1/media/download", params={"token": create_access_token(str(self.admin_id))})
            self.assertEqual(r.status_code, 401)
            storage.assert_not_called()

    def test_linked_download_survives_draft_expiration_for_authorized_member(self):
        result = self.upload().json()
        r = self.client.post(self.prefix+f"/conversations/{self.public}/messages", headers=self.headers(self.admin_id),
            json={"is_note": True, "attachments": [{"key": result["key"]}]})
        self.assertEqual(r.status_code, 201, r.text)
        with Session(self.engine) as db:
            db.query(MediaUpload).filter_by(key=result["key"]).one().expires_at = datetime.now(timezone.utc)-timedelta(days=1); db.commit()
        r = self.client.get("/api/v1/media/presign", params={"key": result["key"]}, headers=self.headers(self.agent_id))
        self.assertEqual(r.status_code, 200, r.text)
        with patch("app.api.v1.media.read_file", return_value=b"fixture"):
            r = self.client.get(r.json()["url"])
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.headers["cache-control"], "private, no-store")

    def test_failed_attachment_batch_does_not_consume_a_draft(self):
        result = self.upload().json()
        r = self.client.post(self.prefix+f"/conversations/{self.conv}/messages", headers=self.headers(self.admin_id),
            json={"is_note": True, "attachments": [{"key": result["key"]}, {"key": f"{self.ws}/{uuid4()}/missing.pdf"}]})
        self.assertEqual(r.status_code, 404, r.text)
        with Session(self.engine) as db:
            self.assertIsNone(db.query(MediaUpload).filter_by(key=result["key"]).one().conversation_id)

    def test_download_legacy_file_never_uses_stored_url_or_foreign_bucket(self):
        message_id = uuid4()
        key = f"{self.ws}/{uuid4()}/legacy.pdf"
        with Session(self.engine) as db:
            db.add(Message(id=message_id, workspace_id=self.ws, conversation_id=self.public, sender_type="agent", sender_id=self.admin_id,
                origin="crm_agent", type="file", attachments=[{"key": key, "bucket": "crm-media", "url": "https://stale.test/file"}]))
            db.commit()
        url = download_url(self.agent_id, message_id=message_id, index=0)
        with patch("app.api.v1.media.read_file", return_value=b"legacy") as storage:
            self.assertEqual(self.client.get(url).content, b"legacy")
            storage.assert_called_once_with("crm-media", key, 25*1024*1024)
            with Session(self.engine) as db:
                db.get(Message, message_id).attachments = [{"key": key, "bucket": "foreign"}]; db.commit()
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_provider_receives_only_server_derived_storage_url(self):
        key = self.upload().json()["key"]
        with Session(self.engine) as db:
            db.add(ContactPhone(workspace_id=self.ws, contact_id=self.contact, phone="5511999999900")); db.commit()
        adapter = SimpleNamespace(send_media=AsyncMock(return_value=SimpleNamespace(external_message_id="fixture-id", wamid=None)))
        with patch("app.services.message_service.get_whatsapp_adapter", new_callable=AsyncMock, return_value=adapter), \
             patch("app.core.minio.generate_presigned_url", return_value="https://storage.test/provider-fetch") as signed, \
             patch("app.services.presence_idle.mark_agent_active", new_callable=AsyncMock):
            r = self.client.post(self.prefix+f"/conversations/{self.public}/messages", headers=self.headers(self.admin_id),
                json={"type": "file", "attachments": [{"key": key, "url": "https://attacker.test/", "mimeType": "fake/type"}]})
        self.assertEqual(r.status_code, 201, r.text)
        signed.assert_called_once_with("crm-media", key, expires=300)
        self.assertEqual(adapter.send_media.await_args.args[1], "https://storage.test/provider-fetch")
        self.assertNotIn("attacker.test", r.text)
        with Session(self.engine) as db:
            stored = db.get(Message, UUID(r.json()["id"]))
            self.assertNotIn("url", stored.attachments[0])

    def test_upload_size_and_mime_are_validated_before_storage(self):
        for mime, content, expected in [("text/html", b"<html>", 415), ("application/pdf", b"%PDF-oversize", 413)]:
            with self.subTest(mime=mime), patch("app.api.v1.media.MAX_UPLOAD_BYTES", 5), patch("app.api.v1.media.upload_file") as upload:
                r = self.client.post("/api/v1/media/upload", params={"workspace_id": str(self.ws)}, headers=self.headers(self.admin_id),
                    files={"file": ("fixture.pdf", content, mime)})
                self.assertEqual(r.status_code, expected, r.text)
                upload.assert_not_called()

    def test_message_serialization_drops_unstored_external_urls(self):
        with Session(self.engine) as db:
            db.add(Message(workspace_id=self.ws, conversation_id=self.public, sender_type="agent", sender_id=self.admin_id,
                origin="crm_agent", type="file", attachments=[{"url": "https://private-provider.test/file", "providerUrl": "https://private-provider.test/secret", "sourceUrl": "https://private-provider.test/source", "provider_payload": {"url": "https://private-provider.test/payload", "mediaKey": "provider-key"}, "base64": "provider-bytes"}]))
            db.commit()
        r = self.client.get(self.prefix+f"/conversations/{self.public}/messages", headers=self.headers(self.agent_id))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotIn("private-provider.test", r.text)
        self.assertNotIn("provider-key", r.text)
        self.assertNotIn("provider-bytes", r.text)

    def test_saved_shared_canned_media_remains_reusable_and_outlives_draft(self):
        key = self.upload().json()["key"]
        canned_id = uuid4()
        with Session(self.engine) as db:
            db.add(CannedResponse(id=canned_id, workspace_id=self.ws, title="Shared", shortcut=str(canned_id), content="", attachments=[{"key": key}]))
            db.query(MediaUpload).filter_by(key=key).one().expires_at = datetime.now(timezone.utc)-timedelta(days=1)
            db.commit()
        for conv in [self.public, self.conv]:
            # Different users may use the same workspace template in different
            # conversations, while ordinary private-file reuse stays forbidden.
            user = self.agent_id if conv == self.public else self.admin_id
            r = self.client.post(self.prefix+f"/conversations/{conv}/messages", headers=self.headers(user),
                json={"is_note": True, "attachments": [{"key": key}]})
            self.assertEqual(r.status_code, 201, r.text)
        r = self.client.get("/api/v1/media/presign", params={"key": key}, headers=self.headers(self.agent_id))
        self.assertEqual(r.status_code, 200, r.text)

    def test_failed_macro_action_does_not_consume_draft(self):
        key = self.upload().json()["key"]
        macro_id = uuid4()
        with Session(self.engine) as db:
            db.add(Macro(id=macro_id, workspace_id=self.ws, name="Partial failure")); db.flush()
            db.add(MacroAction(macro_id=macro_id, position=0, action_type="add_note",
                params={"content": "fixture", "attachments": [{"key": key}, {"key": f"{self.ws}/{uuid4()}/absent.pdf"}]}))
            db.commit()
        # add_note currently has no attachments, so use send_message and make
        # failure happen during binding, before any provider operation.
        with Session(self.engine) as db:
            action = db.query(MacroAction).filter_by(macro_id=macro_id).one()
            action.action_type = "send_message"; db.commit()
        r = self.client.post(self.prefix+f"/macros/{macro_id}/run", headers=self.headers(self.admin_id), json={"conversation_id": str(self.conv)})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["errors"])
        with Session(self.engine) as db:
            self.assertIsNone(db.query(MediaUpload).filter_by(key=key).one().conversation_id)

    def test_template_save_validates_source_and_does_not_publish_someone_elses_draft(self):
        key = self.upload().json()["key"]
        for kind, payload in [
            ("canned-responses", {"title": "Invalid shared", "shortcut": str(uuid4()), "content": "", "attachments": [{"key": key}]}),
            ("macros", {"name": "Invalid shared", "actions": [{"action_type": "send_message", "params": {"attachments": [{"key": key}]}}]}),
        ]:
            r = self.client.post(self.prefix+"/"+kind, headers=self.headers(self.agent_id), json=payload)
            self.assertEqual(r.status_code, 404, r.text)
        r = self.client.post(self.prefix+"/canned-responses", headers=self.headers(self.admin_id),
            json={"title": "Owned shared", "shortcut": str(uuid4()), "content": "", "attachments": [{"key": key, "url": "https://forged.test"}]})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertNotIn("forged.test", r.text)
        self.assertEqual(self.client.get("/api/v1/media/presign", params={"key": key}, headers=self.headers(self.agent_id)).status_code, 200)

    def test_legacy_template_media_without_registry_is_authorized_by_scope(self):
        key = f"{self.ws}/{uuid4()}/saved.pdf"
        canned_id = uuid4()
        with Session(self.engine) as db:
            db.add(CannedResponse(id=canned_id, workspace_id=self.ws, user_id=self.admin_id, visibility="user",
                title="Personal", shortcut=str(canned_id), content="", attachments=[{"key": key, "url": "https://old-signed.test/secret"}]))
            db.commit()
        self.assertEqual(self.client.get("/api/v1/media/presign", params={"key": key}, headers=self.headers(self.agent_id)).status_code, 404)
        r = self.client.get("/api/v1/media/presign", params={"key": key}, headers=self.headers(self.admin_id))
        self.assertEqual(r.status_code, 200, r.text)
        url = r.json()["url"]
        with patch("app.api.v1.media.read_file", return_value=b"legacy-saved"):
            self.assertEqual(self.client.get(url).content, b"legacy-saved")
            with Session(self.engine) as db:
                db.get(CannedResponse, canned_id).active = False; db.commit()
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_shared_saved_macro_media_can_be_used_in_two_conversations(self):
        key = self.upload().json()["key"]
        r = self.client.post(self.prefix+"/macros", headers=self.headers(self.admin_id), json={"name": "Reusable",
            "actions": [{"action_type": "send_message", "params": {"attachments": [{"key": key}]}}]})
        self.assertEqual(r.status_code, 201, r.text)
        for conv, user in [(self.public, self.agent_id), (self.conv, self.admin_id)]:
            r = self.client.post(self.prefix+f"/conversations/{conv}/messages", headers=self.headers(user), json={"is_note": True, "attachments": [{"key": key}]})
            self.assertEqual(r.status_code, 201, r.text)

    def test_timeline_attachments_use_scoped_urls_and_hide_provider_payload(self):
        with Session(self.engine) as db:
            db.add(Message(workspace_id=self.ws, conversation_id=self.public, sender_type="agent", sender_id=self.admin_id,
                origin="crm_agent", type="file", attachments=[{"key": f"{self.ws}/{uuid4()}/legacy.pdf", "bucket": "crm-media",
                    "sourceUrl": "https://provider-secret.test", "provider_payload": {"mediaKey": "provider-key"}}])); db.commit()
        r = self.client.get(self.prefix+f"/contacts/{self.contact}/timeline", headers=self.headers(self.agent_id))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotIn("provider-secret.test", r.text)
        self.assertNotIn("provider-key", r.text)
        attachment = r.json()["conversations"][0]["items"][0]["attachments"][0]
        self.assertTrue(attachment["url"].startswith("/api/v1/media/download?"))

    def test_member_cannot_publish_inaccessible_sector_templates_by_scope_only_patch(self):
        from app.models.workspace import SectorMember
        key = self.upload().json()["key"]
        canned_id, macro_id = uuid4(), uuid4()
        with Session(self.engine) as db:
            db.add(SectorMember(workspace_id=self.ws, sector_id=self.sector, user_id=self.admin_id))
            db.add(CannedResponse(id=canned_id, workspace_id=self.ws, sector_id=self.sector, visibility="sector",
                title="Restricted", shortcut=str(canned_id), content="private", attachments=[{"key": key}]))
            db.add(Macro(id=macro_id, workspace_id=self.ws, sector_id=self.sector, visibility="sector", name="Restricted")); db.flush()
            db.add(MacroAction(macro_id=macro_id, position=0, action_type="send_message", params={"attachments": [{"key": key}]})); db.commit()
        for kind, identity in [("canned-responses", canned_id), ("macros", macro_id)]:
            for fields in [{"visibility": "workspace"}, {"sector_id": str(self.foreign_sector)}]:
                with self.subTest(kind=kind, fields=fields):
                    r = self.client.patch(self.prefix+f"/{kind}/{identity}", json=fields, headers=self.headers(self.agent_id))
                    self.assertEqual(r.status_code, 404, r.text)
        r = self.client.get("/api/v1/media/presign", params={"key": key}, headers=self.headers(self.agent_id))
        self.assertEqual(r.status_code, 404, r.text)

    def test_inactive_template_cannot_grant_an_expired_draft_by_reactivation(self):
        key = self.upload().json()["key"]
        canned_id = uuid4()
        with Session(self.engine) as db:
            db.add(CannedResponse(id=canned_id, workspace_id=self.ws, title="Inactive", shortcut=str(canned_id), content="",
                active=False, attachments=[{"key": key}]))
            db.query(MediaUpload).filter_by(key=key).one().expires_at = datetime.now(timezone.utc)-timedelta(days=1); db.commit()
        r = self.client.patch(self.prefix+f"/canned-responses/{canned_id}", headers=self.headers(self.agent_id), json={"active": True})
        self.assertEqual(r.status_code, 404, r.text)

    @unittest.skipUnless(os.environ.get("CRM2_MEDIA_TEST_STORAGE"), "requires isolated MinIO")
    def test_real_storage_upload_link_and_revocable_download(self):
        from app.core.minio import delete_object
        r = self.client.post("/api/v1/media/upload", params={"workspace_id": str(self.ws)}, headers=self.headers(self.admin_id),
            files={"file": ("real.pdf", b"%PDF-real-storage", "application/pdf")})
        self.assertEqual(r.status_code, 200, r.text)
        result = r.json()
        self.addCleanup(delete_object, "crm-media", result["key"])
        self.assertEqual(self.client.get(result["url"]).content, b"%PDF-real-storage")
        r = self.client.post(self.prefix+f"/conversations/{self.conv}/messages", headers=self.headers(self.admin_id),
            json={"is_note": True, "attachments": [{"key": result["key"]}]})
        self.assertEqual(r.status_code, 201, r.text)
        url = r.json()["attachments"][0]["url"]
        self.assertEqual(self.client.get(url).content, b"%PDF-real-storage")
        with Session(self.engine) as db:
            db.get(auth.Conversation, self.conv).assignee_id = self.agent_id; db.commit()
        self.assertEqual(self.client.get(url).status_code, 404)
