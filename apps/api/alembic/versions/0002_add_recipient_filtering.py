"""add recipient filtering to events

Revision ID: 0002_add_recipient_filtering
Revises: 0001_mvp_schema
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_recipient_filtering"
down_revision = "0001_mvp_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add recipient_id column for direct message routing
    op.add_column(
        "events",
        sa.Column("recipient_id", sa.String(length=36), nullable=True)
    )
    op.create_foreign_key(
        "fk_events_recipient_id_agents",
        "events",
        "agents",
        ["recipient_id"],
        ["id"],
    )
    
    # Add channel column for conversation grouping
    op.add_column(
        "events",
        sa.Column("channel", sa.String(length=100), nullable=False, server_default="default")
    )
    
    # Add index on recipient_id for faster inbox queries
    op.create_index("ix_events_recipient_id", "events", ["recipient_id"], unique=False)
    
    # Add index on channel for faster channel queries
    op.create_index("ix_events_channel", "events", ["channel"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_events_channel", table_name="events")
    op.drop_index("ix_events_recipient_id", table_name="events")
    op.drop_column("events", "channel")
    op.drop_constraint("fk_events_recipient_id_agents", "events", type_="foreignkey")
    op.drop_column("events", "recipient_id")
