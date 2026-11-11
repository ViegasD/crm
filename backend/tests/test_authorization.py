"""API behavior checks against a uniquely named disposable PostgreSQL database.

Set CRM2_MIGRATION_TEST_URL to an isolated PostgreSQL admin endpoint. These tests
never use the shared development app DB; the temporary DB is dropped afterward.
"""
import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from starlette.websockets import WebSocketDisconnect

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.workspace import User, Workspace, UserWorkspaceMembership, Sector, SectorMember
from app.models.channel import ChannelAccount
from app.models.contact import Contact
from app.models.conversation import Conversation, ConversationParticipant, ConversationLabel, Label, CannedResponse
from app.models.flow import Flow
from app.models.catalog import MentionInbox
from app.models.stage9_extras import CsatSurvey, NotificationDelivery
from app.models.sla import ConversationAssignment
from app.models.webhook import WebhookEvent


@unittest.skipUnless(os.environ.get("CRM2_MIGRATION_TEST_URL"), "requires disposable PostgreSQL")
class AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = make_url(os.environ["CRM2_MIGRATION_TEST_URL"])
        cls.admin = create_engine(url, isolation_level="AUTOCOMMIT")
        cls.database = "crm2_audit_" + uuid4().hex
        with cls.admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{cls.database}"'))
        cls.engine = create_engine(url.set(database=cls.database))
        Base.metadata.create_all(cls.engine)
        cls.async_engine = create_async_engine(url.set(database=cls.database, drivername="postgresql+asyncpg"), poolclass=NullPool)
        cls.sessions = async_sessionmaker(cls.async_engine, expire_on_commit=False)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        with cls.admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{cls.database}" WITH (FORCE)'))
        cls.admin.dispose()

    def setUp(self):
        self.admin_id, self.agent_id, self.outsider_id = (uuid4() for _ in range(3))
        self.ws, self.other = uuid4(), uuid4()
        self.sector, self.foreign_sector, self.channel, self.contact, self.conv, self.flow = (uuid4() for _ in range(6))
        with Session(self.engine) as db:
            for user_id in [self.admin_id, self.agent_id, self.outsider_id]:
                db.add(User(id=user_id, name="Audit fixture", email=str(user_id)+"@audit.test", password_hash="unused"))
            db.add_all([Workspace(id=self.ws, name="Audit A", slug=str(self.ws)), Workspace(id=self.other, name="Audit B", slug=str(self.other))])
            db.flush()
            db.add_all([UserWorkspaceMembership(user_id=self.admin_id, workspace_id=self.ws, role="admin"),
                        UserWorkspaceMembership(user_id=self.agent_id, workspace_id=self.ws, role="agent"),
                        UserWorkspaceMembership(user_id=self.outsider_id, workspace_id=self.other, role="admin")])
            db.add_all([Sector(id=self.sector, workspace_id=self.ws, name="A"), Sector(id=self.foreign_sector, workspace_id=self.other, name="B")])
            db.add(Contact(id=self.contact, workspace_id=self.ws, name="Audit Contact"))
            db.add(ChannelAccount(id=self.channel, workspace_id=self.ws, channel_type="whatsapp", provider="evolution_baileys", display_name="Unpaired audit fixture"))
            db.flush()
            db.add(SectorMember(workspace_id=self.other, sector_id=self.foreign_sector, user_id=self.outsider_id))
            db.add(Conversation(id=self.conv, workspace_id=self.ws, channel_account_id=self.channel, contact_id=self.contact))
            db.add(Flow(id=self.flow, workspace_id=self.ws, name="Audit flow", trigger_type="message_received", nodes_data={"version":1,"nodes":[],"edges":[]}))
            db.commit()
        sessions = self.sessions
        async def fixture_db():
            async with sessions() as db:
                try:
                    yield db
                    await db.commit()
                except Exception:
                    await db.rollback()
                    raise
        app.dependency_overrides[get_db] = fixture_db
        self.client = TestClient(app, raise_server_exceptions=False)
        self.addCleanup(app.dependency_overrides.clear)
        self.addCleanup(self.client.close)
        self.prefix = f"/api/v1/workspaces/{self.ws}"
        self.public, self.label = uuid4(), uuid4()
        with Session(self.engine) as db:
            conv = db.get(Conversation, self.conv)
            conv.is_private = True
            conv.assignee_id = self.admin_id
            db.add(Conversation(id=self.public, workspace_id=self.ws, channel_account_id=self.channel, contact_id=self.contact))
            db.add(Label(id=self.label, workspace_id=self.ws, name=str(self.label), color="#123456"))
            db.commit()
        for module in ["app.websocket.handlers", "app.websocket.manager"]:
            patcher = patch(module+".AsyncSessionLocal",self.sessions,create=True)
            patcher.start(); self.addCleanup(patcher.stop)
        patcher=patch("app.websocket.handlers.mark_agent_active",new_callable=AsyncMock)
        patcher.start(); self.addCleanup(patcher.stop)

    def headers(self, user_id):
        return {"Authorization": "Bearer " + create_access_token(str(user_id))}

    def test_private_routes_share_the_list_visibility_rule(self):
        path = f"/conversations/{self.conv}"
        until = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        routes = [
            ("GET", path, None), ("PATCH", path, {"priority": "high"}),
            ("GET", path+"/events", None), ("GET", path+"/messages", None),
            ("POST", path+"/messages", {"content": "unauthorized", "is_note": True}),
            ("POST", path+"/messages/read", None),
            ("POST", path+"/transfer", {"assignee_id": str(self.agent_id)}),
            ("GET", path+"/participants", None),
            ("POST", path+"/participants", {"user_id": str(self.agent_id)}),
            ("DELETE", path+f"/participants/{self.admin_id}", None),
            ("GET", path+"/snooze", None), ("DELETE", path+"/snooze", None),
            ("POST", path+"/snooze", {"until": until}),
            ("GET", path+"/lock", None), ("POST", path+"/lock", {}),
            ("DELETE", path+"/lock", None),
            ("POST", f"/labels/{self.label}/assign", {"conversation_id": str(self.conv)}),
            ("DELETE", f"/labels/{self.label}/assign/{self.conv}", None),
            ("POST", "/sla/assign-next", {"conversation_id": str(self.conv)}),
        ]
        for method, suffix, body in routes:
            with self.subTest(method=method, suffix=suffix):
                response = self.client.request(method, self.prefix+suffix, json=body, headers=self.headers(self.agent_id))
                self.assertEqual(response.status_code, 404, response.text)

    def test_private_list_detail_and_timeline_agree(self):
        for user, expected in [(self.admin_id, {self.conv, self.public}), (self.agent_id, {self.public})]:
            with self.subTest(user=user):
                response = self.client.get(self.prefix+"/conversations", headers=self.headers(user))
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual({x["id"] for x in response.json()["items"]}, {str(x) for x in expected})
                self.assertEqual(response.json()["total"], len(expected))
                response = self.client.get(self.prefix+f"/contacts/{self.contact}/timeline", headers=self.headers(user))
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual({x["id"] for x in response.json()["conversations"]}, {str(x) for x in expected})

    def test_participant_grant_and_revoke_take_effect(self):
        with Session(self.engine) as db:
            p = ConversationParticipant(workspace_id=self.ws, conversation_id=self.conv, user_id=self.agent_id)
            db.add(p); db.commit(); participant_id = p.id
        h = self.headers(self.agent_id)
        self.assertEqual(self.client.get(self.prefix+f"/conversations/{self.conv}", headers=h).status_code, 200)
        with Session(self.engine) as db:
            db.delete(db.get(ConversationParticipant, participant_id)); db.commit()
        self.assertEqual(self.client.get(self.prefix+f"/conversations/{self.conv}", headers=h).status_code, 404)

    def test_admin_does_not_gain_implicit_private_access(self):
        with Session(self.engine) as db:
            db.get(Conversation, self.conv).assignee_id = self.agent_id; db.commit()
        self.assertEqual(self.client.get(self.prefix+f"/conversations/{self.conv}", headers=self.headers(self.admin_id)).status_code, 404)

    def test_bulk_rejects_mixed_visible_and_private_records_without_changes(self):
        actions = [
            ("label", {"label_id": str(self.label)}),
            ("transfer", {"assignee_id": str(self.agent_id)}),
            ("status", {"status": "pending"}),
            ("assign", {"assignee_id": str(self.agent_id)}),
            ("add-participant", {"user_id": str(self.agent_id)}),
        ]
        for action, fields in actions:
            with self.subTest(action=action):
                response = self.client.post(self.prefix+"/conversations/bulk/"+action,
                    json={"conversation_ids": [str(self.public), str(self.conv)], **fields}, headers=self.headers(self.agent_id))
                self.assertEqual(response.status_code, 404, response.text)
        with Session(self.engine) as db:
            self.assertIsNone(db.get(Conversation, self.public).assignee_id)
            self.assertEqual(db.get(Conversation, self.public).status.value, "open")
            self.assertEqual(db.query(ConversationLabel).filter_by(conversation_id=self.public).count(), 0)
            self.assertEqual(db.query(ConversationParticipant).filter_by(conversation_id=self.public).count(), 0)

    def test_agent_cannot_change_members_channels_or_sectors(self):
        cases = [
            ("DELETE", f"/members/{self.admin_id}", None),
            ("POST", "/channels", {"channel_type": "whatsapp", "provider": "evolution_baileys", "display_name": "denied"}),
            ("PATCH", f"/channels/{self.channel}", {"display_name": "denied"}),
            ("DELETE", f"/channels/{self.channel}", None),
            ("PUT", f"/channels/{self.channel}/credentials", {"credential_type": "evolution", "payload": {}}),
            ("POST", "/sectors", {"name": "denied"}),
            ("DELETE", f"/sectors/{self.sector}", None),
            ("POST", f"/sectors/{self.sector}/members", {"user_id": str(self.agent_id)}),
        ]
        for method, suffix, body in cases:
            with self.subTest(method=method, suffix=suffix):
                response = self.client.request(method, self.prefix+suffix, json=body, headers=self.headers(self.agent_id))
                self.assertEqual(response.status_code, 403, response.text)

    def test_last_admin_cannot_be_removed(self):
        r = self.client.delete(self.prefix+f"/members/{self.admin_id}", headers=self.headers(self.admin_id))
        self.assertEqual(r.status_code, 409, r.text)

    def test_sector_members_cannot_cross_workspaces(self):
        h = self.headers(self.admin_id)
        self.assertEqual(self.client.post(self.prefix+f"/sectors/{self.foreign_sector}/members", json={"user_id": str(self.admin_id)}, headers=h).status_code, 404)
        self.assertEqual(self.client.delete(self.prefix+f"/sectors/{self.foreign_sector}/members/{self.outsider_id}", headers=h).status_code, 404)
        self.assertEqual(self.client.post(self.prefix+f"/sectors/{self.sector}/members", json={"user_id": str(self.outsider_id)}, headers=h).status_code, 404)

    def test_participant_cannot_be_added_from_another_workspace(self):
        r = self.client.post(self.prefix+f"/conversations/{self.conv}/participants", json={"user_id": str(self.outsider_id)}, headers=self.headers(self.admin_id))
        self.assertEqual(r.status_code, 404, r.text)

    def test_outsider_is_denied_flows_and_conversations(self):
        for suffix in ["/flows", f"/flows/{self.flow}", "/conversations", f"/conversations/{self.conv}"]:
            with self.subTest(suffix=suffix):
                self.assertEqual(self.client.get(self.prefix+suffix, headers=self.headers(self.outsider_id)).status_code, 403)

    def test_deleted_membership_blocks_existing_token(self):
        with Session(self.engine) as db:
            db.query(UserWorkspaceMembership).filter_by(workspace_id=self.ws, user_id=self.agent_id).delete(); db.commit()
        self.assertEqual(self.client.get(self.prefix+f"/conversations/{self.public}", headers=self.headers(self.agent_id)).status_code, 403)

    def test_websocket_denies_outsider_and_deleted_user(self):
        for user in [self.outsider_id, uuid4()]:
            with self.subTest(user=user), self.assertRaises(WebSocketDisconnect):
                with self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(user))):
                    pass

    def test_websocket_filters_private_events_and_targets_individual_users(self):
        from app.websocket.manager import manager
        with self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(self.admin_id))) as owner, \
             self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(self.agent_id))) as agent:
            for socket in [owner, agent]:
                socket.send_text("ping"); self.assertEqual(socket.receive_text(), "pong")
            event = {"type": "message.new", "conversation_id": str(self.conv)}
            owner.portal.call(manager.broadcast, str(self.ws), event)
            self.assertEqual(json.loads(owner.receive_text()), event)
            agent.send_text("ping"); self.assertEqual(agent.receive_text(), "pong")
            owner.portal.call(manager.send_to, str(self.ws), str(self.admin_id), {"type": "targeted"})
            self.assertEqual(json.loads(owner.receive_text()), {"type": "targeted"})
            agent.send_text("ping"); self.assertEqual(agent.receive_text(), "pong")
            event = {"type": "conversation.updated", "conversation_id": str(self.public)}
            owner.portal.call(manager.broadcast, str(self.ws), event)
            self.assertEqual(json.loads(owner.receive_text()), event)
            self.assertEqual(json.loads(agent.receive_text()), event)

    def test_open_websocket_loses_access_after_membership_revocation(self):
        with self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(self.agent_id))) as ws:
            ws.send_text("ping"); self.assertEqual(ws.receive_text(), "pong")
            with Session(self.engine) as db:
                db.query(UserWorkspaceMembership).filter_by(workspace_id=self.ws, user_id=self.agent_id).delete(); db.commit()
            ws.send_text("ping")
            with self.assertRaises(WebSocketDisconnect):
                ws.receive_text()

    def test_admin_can_manage_channels_and_sector_members(self):
        h = self.headers(self.admin_id)
        r = self.client.patch(self.prefix+f"/channels/{self.channel}", json={"display_name": "authorized"}, headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["display_name"], "authorized")
        for _ in range(2):
            self.assertEqual(self.client.post(self.prefix+f"/sectors/{self.sector}/members", json={"user_id": str(self.agent_id)}, headers=h).status_code, 204)
        self.assertEqual(self.client.delete(self.prefix+f"/sectors/{self.sector}/members/{self.agent_id}", headers=h).status_code, 204)

    def test_channel_sector_reference_must_belong_to_workspace(self):
        h = self.headers(self.admin_id)
        r = self.client.patch(self.prefix+f"/channels/{self.channel}", json={"sector_id": str(self.foreign_sector)}, headers=h)
        self.assertEqual(r.status_code, 404, r.text)

    def test_public_bulk_actions_and_participant_grants_still_work(self):
        h = self.headers(self.agent_id)
        for action, fields in [("label", {"label_id": str(self.label)}),
                               ("status", {"status": "pending"}),
                               ("add-participant", {"user_id": str(self.admin_id)})]:
            r = self.client.post(self.prefix+"/conversations/bulk/"+action,
                json={"conversation_ids": [str(self.public)], **fields}, headers=h)
            self.assertEqual(r.status_code, 204, r.text)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Conversation, self.public).status.value, "pending")
            self.assertEqual(db.query(ConversationParticipant).filter_by(conversation_id=self.public).count(), 1)

    def test_notifications_and_mentions_hide_revoked_private_records(self):
        with Session(self.engine) as db:
            for conv in [self.conv, self.public]:
                db.add(MentionInbox(workspace_id=self.ws, user_id=self.agent_id, conversation_id=conv, snippet="sensitive"))
                db.add(NotificationDelivery(workspace_id=self.ws, user_id=self.agent_id, event_type="mention", title="sensitive", payload={"conversation_id": str(conv)}))
            db.commit()
        for suffix in ["/mentions", "/notifications"]:
            with self.subTest(suffix=suffix):
                r = self.client.get(self.prefix+suffix, headers=self.headers(self.agent_id))
                self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual(len(r.json()["items"]), 1)
                self.assertEqual(r.json()["unread_count"], 1)
                self.assertNotIn(str(self.conv), r.text)

    def test_supervisor_csat_and_heatmap_respect_private_visibility(self):
        now = datetime.now(timezone.utc)
        with Session(self.engine) as db:
            db.get(Conversation, self.conv).assignee_id = self.agent_id
            for conv in [self.conv, self.public]:
                db.get(Conversation, conv).sla_status = "violated"
                db.add(CsatSurvey(workspace_id=self.ws, conversation_id=conv, token=str(uuid4()), score=5))
                db.add(ConversationAssignment(workspace_id=self.ws, conversation_id=conv, user_id=self.agent_id,
                    assigned_at=now-timedelta(minutes=60 if conv==self.conv else 30), unassigned_at=now, method="fixture"))
            db.commit()
        h = self.headers(self.admin_id)
        for suffix in ["/sla/supervisor/overview", "/csat"]:
            r = self.client.get(self.prefix+suffix, headers=h)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertNotIn(str(self.conv), r.text)
            self.assertIn(str(self.public), r.text)
        r = self.client.get(self.prefix+"/supervisor/heatmap", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        minutes = sum(c["minutes_assigned"] for c in r.json()["cells"])
        self.assertGreaterEqual(minutes, 29)
        self.assertLessEqual(minutes, 30)

    def test_websocket_subject_user_id_does_not_make_public_event_targeted(self):
        from app.websocket.manager import manager
        with self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(self.admin_id))) as owner, \
             self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(self.agent_id))) as agent:
            for socket in [owner, agent]:
                socket.send_text("ping"); self.assertEqual(socket.receive_text(), "pong")
            event = {"type": "agent.status", "user_id": str(self.admin_id), "status": "online"}
            owner.portal.call(manager.broadcast, str(self.ws), event)
            self.assertEqual(json.loads(owner.receive_text()), event)
            agent.send_text("ping")
            self.assertEqual(agent.receive_text(), json.dumps(event))
            self.assertEqual(agent.receive_text(), "pong")

    def test_websocket_rechecks_participant_access_before_delivery(self):
        from app.websocket.manager import manager
        with Session(self.engine) as db:
            db.add(ConversationParticipant(workspace_id=self.ws, conversation_id=self.conv, user_id=self.agent_id)); db.commit()
        with self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(self.agent_id))) as ws:
            ws.send_text("ping"); self.assertEqual(ws.receive_text(), "pong")
            event = {"type": "message.new", "conversation_id": str(self.conv)}
            ws.portal.call(manager.broadcast, str(self.ws), event)
            self.assertEqual(json.loads(ws.receive_text()), event)
            with Session(self.engine) as db:
                db.query(ConversationParticipant).filter_by(conversation_id=self.conv, user_id=self.agent_id).delete(); db.commit()
            ws.portal.call(manager.broadcast, str(self.ws), event)
            ws.send_text("ping"); self.assertEqual(ws.receive_text(), "pong")

    def test_invalid_signed_subject_is_unauthorized(self):
        for subject in ["invalid", None]:
            r = self.client.get(self.prefix+"/conversations", headers={"Authorization": "Bearer "+create_access_token(subject)})
            self.assertEqual(r.status_code, 401, r.text)

    def test_privacy_change_does_not_broadcast_update_to_now_unauthorized_user(self):
        with self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(self.agent_id))) as ws:
            ws.send_text("ping"); self.assertEqual(ws.receive_text(), "pong")

            r = self.client.patch(self.prefix+f"/conversations/{self.public}", json={"is_private": True}, headers=self.headers(self.admin_id))
            self.assertEqual(r.status_code, 200, r.text)
            ws.send_text("ping"); self.assertEqual(ws.receive_text(), "pong")

    def test_canned_render_cannot_read_a_hidden_conversation_from_body(self):
        canned = uuid4()
        with Session(self.engine) as db:
            db.add(CannedResponse(id=canned, workspace_id=self.ws, title="Fixture", shortcut=str(canned), content="{{conversation.id}}")); db.commit()
        for user, expected in [(self.agent_id, 404), (self.admin_id, 200)]:
            with self.subTest(user=user):
                r = self.client.post(self.prefix+f"/canned-responses/{canned}/render", json={"conversation_id": str(self.conv)}, headers=self.headers(user))
                self.assertEqual(r.status_code, expected, r.text)

    def test_new_conversation_events_are_delivered_only_after_successful_commit(self):
        from app.websocket.manager import manager
        for commit in [False, True]:
            with self.subTest(commit=commit), self.client.websocket_connect(f"/ws/{self.ws}?token="+create_access_token(str(self.agent_id))) as ws:
                ws.send_text("ping"); self.assertEqual(ws.receive_text(), "pong")
                new_id = uuid4()
                async def persist_and_notify():
                    async with self.sessions() as db:
                        try:
                            async with manager.committed_events(db):
                                db.add(Conversation(id=new_id, workspace_id=self.ws, channel_account_id=self.channel, contact_id=self.contact))
                                await db.flush()
                                await manager.broadcast(str(self.ws), {"type": "message.new", "conversation_id": str(new_id)})
                                if not commit:
                                    raise ValueError("force rollback")
                        except ValueError:
                            pass
                ws.portal.call(persist_and_notify)
                if commit:
                    self.assertEqual(json.loads(ws.receive_text())["conversation_id"], str(new_id))
                ws.send_text("ping"); self.assertEqual(ws.receive_text(), "pong")
                with Session(self.engine) as db:
                    self.assertEqual(db.get(Conversation, new_id) is not None, commit)

    def test_webhook_retry_handles_processing_error_after_rollback(self):
        import asyncio
        from app.services.webhook_retry import reprocess_event
        event_id = uuid4()
        with Session(self.engine) as db:
            db.add(WebhookEvent(id=event_id, workspace_id=self.ws, channel_account_id=self.channel,
                provider="evolution", status="failed", raw_payload={"fixture": True}, attempts=0))
            db.commit()
        with patch("app.services.webhook_retry.AsyncSessionLocal", self.sessions), \
             patch("app.channels.whatsapp.evolution.EvolutionAdapter") as adapter, \
             patch("app.services.message_service.persist_normalized_event", new_callable=AsyncMock, side_effect=ValueError("forced processing error")), \
             patch("app.services.webhook_ops_service.record_attempt", new_callable=AsyncMock) as attempt, \
             patch("app.services.webhook_ops_service.record_circuit_failure", new_callable=AsyncMock) as circuit, \
             patch("app.services.webhook_retry.logger.exception"):
            adapter.return_value.parse_webhook.return_value = [SimpleNamespace()]
            result = asyncio.run(reprocess_event(event_id))
            self.assertEqual(result, (False, "forced processing error"))
            circuit.assert_awaited_once_with(self.ws, self.channel, "forced processing error")
            self.assertEqual(attempt.await_args.kwargs["payload"], {"fixture": True})
        with Session(self.engine) as db:
            event = db.get(WebhookEvent, event_id)
            self.assertEqual(event.attempts, 1)
            self.assertEqual(event.status.value, "failed")

