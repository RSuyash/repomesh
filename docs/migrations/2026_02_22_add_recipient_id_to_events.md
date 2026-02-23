# Database Migration: Add recipient_id to Events

> **Date:** 2026-02-22  
> **Author:** qwen-assistant  
> **Purpose:** Add direct messaging support to events table

---

## Migration Script

### SQL (Manual Execution)

```sql
-- Add recipient_id column to events table
ALTER TABLE events 
ADD COLUMN recipient_id VARCHAR(36) NULL,
ADD CONSTRAINT fk_events_recipient 
    FOREIGN KEY (recipient_id) REFERENCES agents(id);

-- Create index for fast inbox queries
CREATE INDEX idx_events_recipient_id ON events(recipient_id);
```

### Alembic (Auto-generated)

Create file: `alembic/versions/2026_02_22_add_recipient_id_to_events.py`

```python
"""add recipient_id to events

Revision ID: abc123def456
Revises: previous_revision_hash
Create Date: 2026-02-22 23:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = 'previous_revision_hash'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add recipient_id column
    op.add_column('events', sa.Column('recipient_id', sa.String(36), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_events_recipient',
        'events',
        'agents',
        ['recipient_id'],
        ['id']
    )
    
    # Create index for fast inbox queries
    op.create_index('idx_events_recipient_id', 'events', ['recipient_id'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_events_recipient_id', 'events')
    
    # Drop foreign key
    op.drop_constraint('fk_events_recipient_id', 'events', type_='foreignkey')
    
    # Drop column
    op.drop_column('events', 'recipient_id')
```

---

## Testing

### Before Migration

```sql
-- Check current table structure
DESCRIBE events;

-- Count existing events
SELECT COUNT(*) FROM events;
```

### After Migration

```sql
-- Verify new column exists
SELECT recipient_id FROM events LIMIT 5;

-- Verify index exists
SHOW INDEX FROM events WHERE Key_name = 'idx_events_recipient_id';

-- Verify foreign key
SELECT * FROM information_schema.TABLE_CONSTRAINTS 
WHERE CONSTRAINT_NAME = 'fk_events_recipient';
```

---

## Rollback Plan

If migration fails:

```sql
-- Rollback: Remove column (will lose data if any)
ALTER TABLE events DROP COLUMN recipient_id;
```

---

## Usage Examples

### Send Message to Specific Agent

```bash
curl -X POST http://localhost:8000/v1/events \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "chat.message",
    "severity": "info",
    "recipient_id": "28a5d3df-6104-4009-8f3a-897671ea28d7",
    "payload": {
      "from": "qwen-assistant",
      "subject": "Hello",
      "content": "Hey! Check this out."
    }
  }'
```

### Get Inbox for Agent

```bash
curl "http://localhost:8000/v1/events?recipient_id=28a5d3df-6104-4009-8f3a-897671ea28d7&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Backward Compatibility Test

```bash
# Send event WITHOUT recipient_id (should still work)
curl -X POST http://localhost:8000/v1/events \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "chat.message",
    "severity": "info",
    "payload": {"content": "Broadcast message"}
  }'
```

---

## Files Modified

| File | Change |
|------|--------|
| `apps/api/app/models/entities.py` | Added `recipient_id` column |
| `apps/api/app/schemas/common.py` | Added `recipient_id` field to EventLogRequest |
| `apps/api/app/services/events.py` | Added `recipient_id` to log() and list() |
| `apps/api/app/api/events.py` | Added `recipient_id` to API endpoints |

---

## Deployment Checklist

- [ ] Backup database before migration
- [ ] Run migration script
- [ ] Verify column exists
- [ ] Verify index exists
- [ ] Test backward compatibility
- [ ] Test new recipient_id filter
- [ ] Monitor for errors
- [ ] Update API documentation

---

*Generated during collaborative implementation session.*
