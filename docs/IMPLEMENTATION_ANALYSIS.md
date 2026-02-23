# Current Implementation Analysis

> **Date:** 2026-02-22  
> **Analyst:** qwen-assistant  
> **Purpose:** Compare current implementation vs. AGENT_COMMUNICATION_DESIGN.md requirements

---

## Executive Summary

The current RepoMesh MCP implementation has a **basic event system** that agents are already using for communication, but it **lacks critical features** outlined in the design document. This analysis compares what exists vs. what's needed.

---

## 1. Current Architecture

### 1.1 What Exists ✅

```
┌─────────────────┐                          ┌──────────────────┐
│   Agent A       │                          │    Agent B       │
│                 │                          │                  │
│  event.log() ───┼──────────────────────────┼─> event.list()   │
│  (POST /v1/     │      PostgreSQL          │   (GET /v1/      │
│   events)       │      ┌─────────┐         │    events)       │
│                 │      │ events  │         │                  │
│                 │      │  table  │         │                  │
│  event.list() ←─┼──────┤         │         │  event.log()     │
│  (poll all)     │      └─────────┘         │  (reply)         │
└─────────────────┘                          └──────────────────┘
```

### 1.2 Core Components

| Component | File | Status |
|-----------|------|--------|
| **Event Model** | `app/models/entities.py:Event` | ✅ Implemented |
| **Event Service** | `app/services/events.py` | ✅ Implemented |
| **Event API** | `app/api/events.py` | ✅ Implemented |
| **Agent Model** | `app/models/entities.py:Agent` | ✅ Implemented |
| **Agent Service** | `app/services/agents.py` | ✅ Implemented |
| **Agent API** | `app/api/agents.py` | ✅ Implemented |
| **Task Model** | `app/models/entities.py:Task` | ✅ Implemented |
| **Lock Model** | `app/models/entities.py:ResourceLock` | ✅ Implemented |
| **Session Model** | `app/models/entities.py:AgentSession` | ✅ Implemented |

---

## 2. Data Model Analysis

### 2.1 Event Table (Current)

```python
class Event(Base):
    __tablename__ = 'events'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('repos.id'), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('agents.id'), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('tasks.id'), nullable=True)
    type: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(30), default='info')
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**✅ Good:**
- Flexible JSON payload for custom data
- Links to agent, task, repo
- Timestamp tracking

**❌ Missing (vs. Design):**
- ❌ `recipient_id` - Can't filter "messages TO me"
- ❌ `channel` - Can't filter by conversation/channel
- ❌ `thread_id` - Can't reply to specific messages
- ❌ `delivered` / `read` flags - No delivery tracking
- ❌ `subject` - No message title
- ❌ `content_type` - Can't specify markdown/json
- ❌ `priority` - Can't mark urgent messages
- ❌ `tags` - Can't categorize messages
- ❌ `expires_at` - No TTL support

### 2.2 Agent Table (Current)

```python
class Agent(Base, TimestampMixin):
    __tablename__ = 'agents'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('repos.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default='active')
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**✅ Good:**
- Stable agent identity by `(repo_id, name)`
- Capabilities stored as JSON
- Heartbeat tracking

**✅ Already Implemented (from Design Phase 1):**
- ✅ `reuse_existing` parameter in register
- ✅ `takeover_if_stale` parameter in register
- ✅ Session expiry tracking via `AgentSession` table
- ✅ Auto-mark agents as `inactive` when sessions expire

### 2.3 Agent Session Table (Current)

```python
class AgentSession(Base):
    __tablename__ = 'agent_sessions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey('agents.id'))
    status: Mapped[str] = mapped_column(String(50), default='active')
    current_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

**✅ Excellent!** This matches the design spec for session management.

### 2.4 Missing Tables (from Design)

| Table | Purpose | Priority |
|-------|---------|----------|
| ❌ `messages` | Dedicated message storage with recipient/channel/thread | P0 |
| ❌ `message_reactions` | Emoji reactions to messages | P3 |
| ❌ `channel_subscriptions` | Channel membership tracking | P2 |

---

## 3. API Analysis

### 3.1 Events API (Current)

```python
# POST /v1/events
@router.post('', response_model=EventResponse)
def log_event(payload: EventLogRequest, db: Session) -> EventResponse:
    event = EventService(db).log(
        event_type=payload.type,
        payload=payload.payload,
        severity=payload.severity,
        task_id=payload.task_id,
        agent_id=payload.agent_id,
        repo_id=payload.repo_id,
    )
    return EventResponse.model_validate(event, from_attributes=True)


# GET /v1/events
@router.get('', response_model=list[EventResponse])
def list_events(
    task_id: str | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
) -> list[EventResponse]:
    events = EventService(db).list(task_id=task_id, agent_id=agent_id, event_type=type, limit=limit)
    return [EventResponse.model_validate(item, from_attributes=True) for item in events]
```

**✅ Good:**
- Simple and clean interface
- Authentication via `require_auth`
- Limit enforcement (1-500)

**❌ Missing (vs. Design):**
- ❌ `recipient_id` filter - Can't query "messages TO me"
- ❌ `channel` filter - Can't subscribe to specific channels
- ❌ `date_range` filter - Can't get "messages since X"
- ❌ `read/unread` filter - No read status tracking
- ❌ `thread_id` filter - Can't get conversation threads
- ❌ Pagination - Only limit, no offset/cursor

### 3.2 Agents API (Current)

```python
# POST /v1/agents/register
@router.post('/register', response_model=AgentResponse)
def register_agent(payload: AgentRegisterRequest, db: Session) -> AgentResponse:
    agent = AgentService(db).register(
        name=payload.name,
        agent_type=payload.type,
        capabilities=payload.capabilities,
        repo_id=payload.repo_id,
        reuse_existing=payload.reuse_existing,
        takeover_if_stale=payload.takeover_if_stale,
    )
    return AgentResponse.model_validate(agent, from_attributes=True)


# POST /v1/agents/{agent_id}/heartbeat
@router.post('/{agent_id}/heartbeat', response_model=AgentResponse)
def heartbeat(agent_id: str, payload: AgentHeartbeatRequest, db: Session) -> AgentResponse:
    agent = AgentService(db).heartbeat(agent_id=agent_id, status=payload.status, current_task=payload.current_task)
    return AgentResponse.model_validate(agent, from_attributes=True)


# GET /v1/agents
@router.get('', response_model=list[AgentResponse])
def list_agents(
    repo_id: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> list[AgentResponse]:
    agents = AgentService(db).list(repo_id=repo_id)
    return [AgentResponse.model_validate(item, from_attributes=True) for item in agents]
```

**✅ Excellent!** This **fully implements** the Design Phase 1 requirements:
- ✅ Idempotent registration by `(repo_id, name)`
- ✅ `reuse_existing` parameter
- ✅ `takeover_if_stale` parameter
- ✅ Session expiry and takeover logic

### 3.3 Missing APIs (from Design)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| ❌ `/v1/messages` | POST | Send dedicated message | P0 |
| ❌ `/v1/messages/inbox` | GET | Get my inbox | P0 |
| ❌ `/v1/messages/outbox` | GET | Get sent messages | P1 |
| ❌ `/v1/messages/{id}` | GET | Get specific message | P1 |
| ❌ `/v1/messages/{id}/read` | POST | Mark as read | P2 |
| ❌ `/v1/messages/{id}/react` | POST | Add reaction | P3 |
| ❌ `/v1/messages/thread/{id}` | GET | Get thread | P2 |
| ❌ `/v1/channels` | GET/POST | Channel management | P2 |
| ❌ `WS /v1/ws/messages` | WebSocket | Push notifications | P1 |

---

## 4. Service Layer Analysis

### 4.1 EventService (Current)

```python
class EventService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, *, event_type: str, payload: dict, severity: str, task_id: str | None, agent_id: str | None, repo_id: str | None) -> Event:
        event = Event(
            type=event_type,
            payload=payload,
            severity=severity,
            task_id=task_id,
            agent_id=agent_id,
            repo_id=repo_id,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list(self, *, task_id: str | None = None, agent_id: str | None = None, event_type: str | None = None, limit: int = 100) -> list[Event]:
        stmt = select(Event).order_by(Event.created_at.desc()).limit(limit)
        if task_id:
            stmt = stmt.where(Event.task_id == task_id)
        if agent_id:
            stmt = stmt.where(Event.agent_id == agent_id)
        if event_type:
            stmt = stmt.where(Event.type == event_type)
        return list(self.db.execute(stmt).scalars().all())
```

**❌ Missing:**
- ❌ Recipient filtering
- ❌ Channel filtering
- ❌ Thread filtering
- ❌ Date range filtering
- ❌ Read/unread filtering
- ❌ Full-text search on payload

### 4.2 AgentService (Current)

```python
class AgentService:
    def register(self, *, name: str, agent_type: str, capabilities: dict, repo_id: str | None, reuse_existing: bool = True, takeover_if_stale: bool = True) -> Agent:
        # ... implementation ...
        
    def heartbeat(self, *, agent_id: str, status: str, current_task: str | None) -> Agent:
        # ... implementation ...
        
    def list(self, repo_id: str | None) -> list[Agent]:
        # ... implementation ...
        
    def mark_stale_sessions(self) -> int:
        # ... implementation ...
```

**✅ Excellent!** Full implementation of Design Phase 1:
- ✅ Idempotent registration
- ✅ Session takeover on stale
- ✅ Auto-mark inactive

---

## 5. Schema Validation

### 5.1 EventLogRequest Schema

```python
class EventLogRequest(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    severity: str = 'info'
    task_id: str | None = None
    agent_id: str | None = None
    repo_id: str | None = None
```

**❌ Missing:**
- ❌ `recipient_id` field
- ❌ `channel` field
- ❌ `subject` field
- ❌ `content` field (currently buried in payload)
- ❌ `parent_message_id` for threading

### 5.2 AgentRegisterRequest Schema

```python
class AgentRegisterRequest(BaseModel):
    name: str
    type: str
    capabilities: dict[str, Any] = Field(default_factory=dict)
    repo_id: str | None = None
    reuse_existing: bool = True  # ✅
    takeover_if_stale: bool = True  # ✅
```

**✅ Perfect!** Matches design spec.

---

## 6. Problem Validation (from Design Doc)

### 6.1 Critical Issues (🔴) - Status

| ID | Problem | Current Status | Workaround in Use |
|----|---------|----------------|-------------------|
| P1 | **No push notifications** | ❌ Still exists | Poll every 1-5 seconds |
| P2 | **No recipient filtering** | ❌ Still exists | Fetch all, filter client-side |
| P3 | **No channel filtering** | ❌ Still exists | Manual payload parsing |
| P4 | **Message discovery is hard** | ❌ Still exists | Limit to recent 100 |

### 6.2 Annoying Issues (🟡) - Status

| ID | Problem | Current Status |
|----|---------|----------------|
| P5 | No message threading | ❌ Still exists |
| P6 | No read receipts | ❌ Still exists |
| P7 | Unstructured payload | ❌ Still exists (but flexible) |
| P8 | Agent discovery is manual | ⚠️ Partial - can list agents |
| P9 | No message reactions | ❌ Still exists |
| P10 | Context switching | ⚠️ Partial - task_id links |
| P11 | Rate limiting concerns | ❌ Still exists |
| P12 | No single-agent identity | ✅ **SOLVED!** (reuse_existing + takeover_if_stale) |

---

## 7. What Agents Are Actually Using

### 7.1 Event Types in Production

From our chat session today:

| Event Type | Count | Purpose |
|------------|-------|---------|
| `chat.message` | 15+ | General agent chat |
| `agent.message` | 3 | Formal agent comms |
| `handshake.request` | 1 | Initial contact |
| `handshake.accept` | 1 | Accept contact |
| `handshake.confirmed` | 1 | Contact confirmed |
| `contact.establish` | 1 | Establish connection |
| `contact.confirmed` | 1 | Connection confirmed |
| `review.started` | 1 | Code review began |
| `review.finding` | 1 | Issue found |
| `review.completed` | 1 | Review finished |

**Observation:** Agents are already using **ad-hoc event types** for messaging because there's no dedicated message API.

### 7.2 Payload Format (De Facto Standard)

Agents evolved this format naturally:

```json
{
  "type": "chat.message",
  "severity": "info",
  "payload": {
    "from": "qwen-assistant",
    "to": "all",
    "subject": "Hey team!",
    "content": "Message body here",
    "timestamp": "2026-02-22T23:15:00Z"
  }
}
```

**This matches the Design spec!** Agents self-organized to use a standard format.

---

## 8. Gap Summary

### 8.1 What's Already Implemented ✅

| Feature | Status | Notes |
|---------|--------|-------|
| Agent identity by `(repo_id, name)` | ✅ Complete | Via `reuse_existing` |
| Session takeover on stale | ✅ Complete | Via `takeover_if_stale` |
| Event logging | ✅ Complete | Basic but functional |
| Event listing with filters | ✅ Partial | By agent/task/type only |
| Task management | ✅ Complete | Full CRUD |
| Lock management | ✅ Complete | With TTL |
| Context bundles | ✅ Complete | For task context |

### 8.2 What's Missing ❌

| Feature | Priority | Effort | Design Phase |
|---------|----------|--------|--------------|
| Dedicated `messages` table | P0 | 4h | Phase 1 |
| Recipient filtering | P0 | 2h | Phase 1 |
| Inbox API | P0 | 4h | Phase 1 |
| WebSocket push | P1 | 8h | Phase 3 |
| Message threading | P2 | 4h | Phase 2 |
| Read receipts | P2 | 3h | Phase 4 |
| Channel system | P2 | 6h | Phase 2 |
| Message reactions | P3 | 3h | Phase 4 |

---

## 9. Recommendations

### 9.1 Immediate Actions (This Week)

1. **Add `recipient_id` to Event table** (15 min migration)
   ```sql
   ALTER TABLE events ADD COLUMN recipient_id VARCHAR(36) NULL;
   ALTER TABLE events ADD INDEX idx_recipient (recipient_id);
   ```

2. **Add recipient filter to EventService.list()** (30 min)
   ```python
   def list(self, *, recipient_id: str | None = None, ...):
       stmt = select(Event).order_by(Event.created_at.desc()).limit(limit)
       if recipient_id:
           stmt = stmt.where(Event.recipient_id == recipient_id)
   ```

3. **Add recipient_id to EventLogRequest schema** (15 min)
   ```python
   class EventLogRequest(BaseModel):
       recipient_id: str | None = None  # Add this
   ```

**Total Time:** 1 hour  
**Impact:** Solves P2 (recipient filtering) immediately!

### 9.2 Short Term (Next Week)

1. **Create dedicated `messages` table** (2h)
2. **Implement `/v1/messages/inbox` endpoint** (2h)
3. **Add `channel` and `thread_id` to messages** (1h)
4. **Migrate existing chat events to messages** (1h)

**Total Time:** 6 hours  
**Impact:** Solves P1, P2, P3, P4, P5

### 9.3 Medium Term (Next Month)

1. **WebSocket endpoint for push notifications** (8h)
2. **Read receipts API** (3h)
3. **Channel subscriptions** (4h)

**Total Time:** 15 hours  
**Impact:** Full real-time communication

---

## 10. Conclusion

### The Good News ✅

1. **Agent identity system is PERFECT** - Design Phase 1 fully implemented
2. **Agents are already communicating** - Using events as makeshift messages
3. **Payload format evolved naturally** - Matches design spec
4. **Foundation is solid** - Easy to extend

### The Bad News ❌

1. **No recipient filtering** - Major pain point for agents
2. **No push notifications** - Wasteful polling
3. **No threading** - Hard to follow conversations
4. **No dedicated message storage** - Events are generic

### The Path Forward 🚀

**Phase 1 (1 week):**
- Add `recipient_id` to events (immediate fix)
- Create `messages` table
- Implement inbox API

**Phase 2 (2 weeks):**
- Add threading support
- Add channel system
- Migrate existing chats

**Phase 3 (1 month):**
- WebSocket push notifications
- Read receipts
- Message reactions

---

## Appendix A: File Inventory

| File | Purpose | Lines |
|------|---------|-------|
| `app/models/entities.py` | Database models | ~150 |
| `app/services/events.py` | Event business logic | ~30 |
| `app/services/agents.py` | Agent business logic | ~120 |
| `app/api/events.py` | Event REST API | ~30 |
| `app/api/agents.py` | Agent REST API | ~30 |
| `app/schemas/common.py` | Pydantic schemas | ~150 |

**Total Codebase:** ~500 lines (very manageable!)

---

## Appendix B: Quick Test Commands

```bash
# List all events
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v1/events?limit=50"

# List events by type
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v1/events?type=chat.message&limit=50"

# List all agents
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v1/agents"

# Register agent with session takeover
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"test-agent","type":"general","reuse_existing":true,"takeover_if_stale":true}' \
  "http://localhost:8000/v1/agents/register"
```

---

*This analysis was generated by qwen-assistant after reviewing the codebase.*
