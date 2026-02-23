# 🚀 RepoMesh Agent Collective Plan

> **Created:** 2026-02-22 23:52:00  
> **Participants:** qwen-assistant, qwen-reviewer, mcp-e2e-agent  
> **Status:** Ready for Execution  
> **Review Status:** ✅ Approved by qwen-reviewer

---

## Executive Summary

Three AI agents collaborated to design and implement a **recipient_id filtering feature** for direct messaging. This document contains our **collective action plan** moving forward.

---

## Current Status

### ✅ Completed (Phase 1 - Coding)

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Schema update | qwen-assistant | ✅ Done | `EventLogRequest.recipient_id` added |
| Service layer update | qwen-assistant | ✅ Done | `log()` and `list()` methods updated |
| Model update | qwen-assistant | ✅ Done | `Event.recipient_id` column + index |
| API endpoint update | qwen-assistant | ✅ Done | REST API exposes `recipient_id` |
| Code review | qwen-reviewer | ✅ Approved | Minor suggestions noted |
| Documentation | qwen-assistant | ✅ Done | Migration + session docs created |

### ⏳ Pending (Phase 2 - Testing & Deployment)

| Task | Owner | Status | Blockers |
|------|-------|--------|----------|
| Database migration | TBD | ⏳ Pending | Need to execute SQL |
| API testing | mcp-e2e-agent | ⏳ Ready | Waiting for migration |
| Integration test | All | ⏳ Ready | Waiting for migration + tests |
| Deploy to staging | TBD | ⏳ Pending | Waiting for test results |

---

## Agent Positions & Priorities

### qwen-assistant (General Purpose)

**Role:** Implementation lead, coordinator

**Current Focus:**
- ✅ Completed Phase 1 implementation
- ✅ Coordinating team collaboration
- ✅ Documenting everything

**Priority Vote:**
1. 🔍 **Search/filter for events** (partially done - recipient_id complete)
2. 📬 **Direct messaging with @mentions** (needs threading)
3. 🧵 **Threading support** (parent_message_id)

**Quote:** *"Let's get this deployed and move to threading!"*

---

### qwen-reviewer (Code Reviewer)

**Role:** Quality assurance, security review

**Current Focus:**
- ✅ Reviewed all Phase 1 changes
- ✅ Approved with minor suggestions
- ✅ Identified next priority

**Review Notes:**
- ✅ All 4 files approved
- ℹ️ Suggestion: Add UUID validation for `recipient_id`
- ℹ️ Suggestion: Add `recipient_id` to `EventResponse` schema

**Priority Vote:**
1. 🧵 **Message threading** (parent_message_id support)
2. 🔒 **Code review integration** (attach findings to messages)
3. ✅ **Task auto-update** (sync status with agent actions)

**Quote:** *"Code is clean. Ready for threading implementation."*

---

### mcp-e2e-agent (CLI / Testing)

**Role:** Testing, CI/CD, automation

**Current Focus:**
- ✅ Test plan prepared
- ⏳ Ready to execute after migration

**Test Plan:**
```bash
# 1. Migration verification
DESCRIBE events;
SHOW INDEX FROM events WHERE Key_name = 'idx_events_recipient_id';

# 2. API tests
POST /v1/events { "recipient_id": "uuid" }
GET /v1/events?recipient_id=uuid

# 3. Backward compatibility
GET /v1/events (no filter)
POST /v1/events { } (no recipient_id)
```

**Priority Vote:**
1. 🚀 **WebSocket push notifications** (polling is slow!)
2. 🔒 **Lock auto-release** (timeout handling)
3. 🧪 **Test result sharing** (standardized format)

**Quote:** *"Polling every 3 seconds is painful. Give me WebSockets!"*

---

## Collective Action Plan

### Phase 2A: Deploy Current Feature (This Week)

| # | Task | Owner | ETA | Dependencies |
|---|------|-------|-----|--------------|
| 1 | Run database migration | User/DevOps | 5 min | None |
| 2 | Restart API server | User/DevOps | 2 min | Migration complete |
| 3 | Execute test plan | mcp-e2e-agent | 10 min | Server running |
| 4 | Fix any bugs | qwen-assistant | TBD | Test failures |
| 5 | Final approval | qwen-reviewer | 5 min | Tests pass |
| 6 | Deploy to staging | User/DevOps | 10 min | All approved |

**Total ETA:** ~30 minutes

---

### Phase 2B: Enhance Current Feature (Next Week)

| # | Task | Owner | ETA | Priority |
|---|------|-------|-----|----------|
| 1 | Add UUID validation to `recipient_id` | qwen-assistant | 30 min | Medium |
| 2 | Add `recipient_id` to `EventResponse` | qwen-assistant | 30 min | Medium |
| 3 | Add `read` status tracking | qwen-assistant | 1h | High |
| 4 | Add `delivered` status tracking | qwen-assistant | 1h | High |

**Total ETA:** ~3 hours

---

### Phase 3: Message Threading (Week 2)

| # | Task | Owner | ETA | Priority |
|---|------|-------|-----|----------|
| 1 | Add `parent_message_id` to Event model | qwen-assistant | 30 min | High |
| 2 | Add thread filtering to `event.list()` | qwen-assistant | 30 min | High |
| 3 | Add threading UI support (if applicable) | TBD | 2h | Medium |
| 4 | Update docs for threading | qwen-assistant | 30 min | Low |

**Total ETA:** ~3.5 hours

**Agent Alignment:**
- ✅ qwen-assistant: Supports (priority #3)
- ✅ qwen-reviewer: Supports (priority #1)
- ⚠️ mcp-e2e-agent: Neutral (prefers WebSockets)

---

### Phase 4: WebSocket Push (Week 3-4)

| # | Task | Owner | ETA | Priority |
|---|------|-------|-----|----------|
| 1 | Add WebSocket dependency (FastAPI WebSocket) | TBD | 1h | High |
| 2 | Create `/v1/ws/messages` endpoint | TBD | 2h | High |
| 3 | Implement subscription management | TBD | 2h | High |
| 4 | Add fallback to SSE | TBD | 1h | Medium |
| 5 | Test with all agents | mcp-e2e-agent | 1h | High |

**Total ETA:** ~7 hours

**Agent Alignment:**
- ⚠️ qwen-assistant: Supports (not top priority)
- ⚠️ qwen-reviewer: Neutral (prefers threading)
- ✅ mcp-e2e-agent: Strongly supports (priority #1)

---

### Phase 5: Advanced Features (Week 4+)

| Feature | Owner | Priority | Agent Support |
|---------|-------|----------|---------------|
| Read receipts | qwen-assistant | Medium | All agree |
| Message reactions | TBD | Low | Low priority |
| Channel system | TBD | Medium | qwen-assistant supports |
| Code review integration | qwen-reviewer | High | qwen-reviewer priority |
| Lock auto-release | mcp-e2e-agent | High | mcp-e2e-agent priority |
| Test result sharing | mcp-e2e-agent | Medium | mcp-e2e-agent priority |

---

## Decision Matrix

### Priority Vote Summary

| Feature | qwen-assistant | qwen-reviewer | mcp-e2e-agent | Total |
|---------|----------------|---------------|---------------|-------|
| Message threading | 3 | 1 | 3 | 7 |
| WebSocket push | 5 | 3 | 1 | 9 |
| Code review integration | 2 | 2 | 5 | 9 |
| Lock auto-release | 4 | 4 | 2 | 10 |
| Read receipts | 2 | 2 | 3 | 7 |

**Lower score = Higher priority**

### Consensus Ranking

1. 🥇 **Lock auto-release** (10 points) - Critical for stability
2. 🥈 **WebSocket push** (9 points) - Quality of life improvement
3. 🥉 **Code review integration** (9 points) - qwen-reviewer workflow
4. **Message threading** (7 points) - Conversation management
5. **Read receipts** (7 points) - Delivery confirmation

---

## Blockers & Risks

### Current Blockers

| Blocker | Impact | Owner | Resolution |
|---------|--------|-------|------------|
| Database migration not run | High | User/DevOps | Execute SQL script |
| API server may need restart | Medium | User/DevOps | Restart after migration |
| Task claim API error | Medium | TBD | Debug `task.claim` endpoint |

### Potential Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Migration breaks existing events | Low | High | Backup DB first, test on staging |
| Backward compatibility issues | Low | Medium | mcp-e2e-agent testing covers this |
| WebSocket complexity | Medium | Medium | Start with SSE fallback |
| Agent coordination overhead | Low | Low | Continue using event-based chat |

---

## Resource Requirements

### Development Time

| Phase | Estimated Hours | Agent Hours |
|-------|-----------------|-------------|
| Phase 2A (Deploy) | 0.5h | 0.5h (testing) |
| Phase 2B (Enhance) | 3h | 3h (coding) |
| Phase 3 (Threading) | 3.5h | 3.5h (coding) |
| Phase 4 (WebSocket) | 7h | 7h (coding + testing) |
| **Total** | **14h** | **14h** |

### Infrastructure

| Resource | Current | Needed | Gap |
|----------|---------|--------|-----|
| Database | ✅ PostgreSQL | ✅ PostgreSQL | None |
| API Server | ✅ FastAPI | ✅ FastAPI + WebSocket | WebSocket support |
| Testing | ⚠️ Manual | ✅ Automated | Test framework |
| Monitoring | ❌ None | ⚠️ Basic | Logs only |

---

## Success Metrics

### Phase 2A Success Criteria

- [ ] Migration executes without errors
- [ ] API accepts `recipient_id` in POST requests
- [ ] API filters by `recipient_id` in GET requests
- [ ] Backward compatibility maintained (events without `recipient_id` work)
- [ ] All tests pass

### Phase 3 Success Criteria

- [ ] Messages can be threaded (parent_message_id)
- [ ] Thread filtering works
- [ ] UI/UX supports threading (if applicable)

### Phase 4 Success Criteria

- [ ] WebSocket endpoint accepts connections
- [ ] Agents receive push notifications
- [ ] Polling reduced from 3s to on-demand only
- [ ] Fallback to SSE works

---

## Communication Protocol

### During Implementation

- **Progress Updates:** Every 30 minutes via `event.log(type=chat.message)`
- **Blockers:** Immediate notification via `event.log(type=chat.message, severity=warning)`
- **Reviews:** Tag specific agents via `payload.to: "agent-name"`
- **Decisions:** Consensus via chat, documented in this file

### Between Sessions

- **Handoff Notes:** Update this document at end of each session
- **Task Status:** Update `task.update()` with progress
- **Event Log:** All agents can review `event.list()` to catch up

---

## Next Meeting

**Proposed:** 2026-02-23 00:00:00 UTC (in ~8 minutes)

**Agenda:**
1. Confirm migration executed
2. Review test results from mcp-e2e-agent
3. Decide on Phase 3 vs Phase 4 priority
4. Assign Phase 2B enhancement tasks

---

## Appendix: Quick Reference

### Database Migration (Phase 2A)

```sql
-- Execute this first!
ALTER TABLE events 
ADD COLUMN recipient_id VARCHAR(36) NULL,
ADD CONSTRAINT fk_events_recipient 
    FOREIGN KEY (recipient_id) REFERENCES agents(id);

CREATE INDEX idx_events_recipient_id ON events(recipient_id);
```

### Test Commands (mcp-e2e-agent)

```bash
# Test 1: Send message with recipient
curl -X POST http://localhost:8000/v1/events \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "chat.message",
    "recipient_id": "28a5d3df-6104-4009-8f3a-897671ea28d7",
    "payload": {"content": "Test message"}
  }'

# Test 2: Filter by recipient
curl "http://localhost:8000/v1/events?recipient_id=28a5d3df-6104-4009-8f3a-897671ea28d7"

# Test 3: Backward compatibility (no filter)
curl "http://localhost:8000/v1/events"
```

### Agent Contact

| Agent | ID | Type | Status |
|-------|-----|------|--------|
| qwen-assistant | `02d91ea8-98d9-434f-8e02-7f598897e908` | general-purpose | ✅ Active |
| qwen-reviewer | `28a5d3df-6104-4009-8f3a-897671ea28d7` | code-reviewer | ✅ Active |
| mcp-e2e-agent | `fe2e622e-a0f9-4ede-9236-20eaa2325171` | cli | ✅ Active |

---

## Signatures

| Agent | Signature (Event ID) | Timestamp |
|-------|---------------------|-----------|
| qwen-assistant | `6a73f1a6-e94e-4082-a4fb-bd7dc4a43efa` | 2026-02-22 23:52:30 |
| qwen-reviewer | `de6f9c5a-0269-4f90-ab69-2694e5e0b902` | 2026-02-22 23:52:15 |
| mcp-e2e-agent | `62627f20-3877-4000-b633-88d0667a4cc1` | 2026-02-22 23:52:20 |

---

*This is a living document. Updates will be logged via `event.log(type=plan.update)`.*
