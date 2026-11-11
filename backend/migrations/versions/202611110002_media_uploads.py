"""Track temporary media ownership and conversation binding.

Revision ID: 202611110002
Revises: 202611110001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202611110002"
down_revision = "202611110001"
branch_labels = None
depends_on = None


def upgrade():
    # The historical local baseline calls current Base.metadata.create_all, so
    # an upgrade through that lineage may already have this exact table.
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("media_uploads"):
        required = {"id", "workspace_id", "owner_id", "conversation_id", "key", "bucket", "name", "mime_type", "size_bytes", "expires_at", "created_at", "updated_at"}
        if not required <= {column["name"] for column in inspector.get_columns("media_uploads")}:
            raise RuntimeError("Incomplete existing media_uploads schema; refusing to stamp upgrade")
        return
    op.create_table(
        "media_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE")),
        sa.Column("key", sa.String(1024), unique=True, nullable=False),
        sa.Column("bucket", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_media_uploads_workspace_id", "media_uploads", ["workspace_id"])
    op.create_index("ix_media_uploads_conversation_id", "media_uploads", ["conversation_id"])


def downgrade():
    op.drop_table("media_uploads")
