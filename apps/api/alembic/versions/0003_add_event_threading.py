"""add event threading support

Revision ID: 0003_add_event_threading
Revises: 0002_add_recipient_filtering
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


revision = "0003_add_event_threading"
down_revision = "0002_add_recipient_filtering"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("parent_message_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_events_parent_message_id_events",
        "events",
        "events",
        ["parent_message_id"],
        ["id"],
    )
    op.create_index("ix_events_parent_message_id", "events", ["parent_message_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_events_parent_message_id", table_name="events")
    op.drop_constraint("fk_events_parent_message_id_events", "events", type_="foreignkey")
    op.drop_column("events", "parent_message_id")
