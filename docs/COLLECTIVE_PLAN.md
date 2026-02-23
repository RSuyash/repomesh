# 🤖 Collective Agent Plan

> **Date:** 2026-02-22  
> **Participants:** qwen-assistant, qwen-reviewer, mcp-e2e-agent  
> **Session:** Collective Planning  
> **Plan Authority:** `docs/COLLECTIVE_PLAN.md` is the canonical source of truth.  
> **Evolution Policy:** Dated plan files (for example `docs/COLLECTIVE_PLAN_2026_02_22.md`) are additive snapshots and decision logs. Their approved decisions should be merged into this file.

---

## Executive Summary

This document presents a unified plan from all RepoMesh agents for improving the system and delivering value to the user. The plan is based on:
- Analysis of current implementation gaps
- Agent capabilities and roles
- Priority tasks identified during collaboration

---

## 1. Agent Roster & Roles

| Agent | ID | Type | Role | Status |
|-------|-----|------|------|--------|
| **qwen-assistant** | `02d91ea8-...` | general-purpose | Implementation lead, coordination | 🟢 active |
| **qwen-reviewer** | `28a5d3df-...` | code-reviewer | Code review, security analysis, quality assurance | 🟢 active |
| **mcp-e2e-agent** | `fe2e622e-...` | cli | End-to-end testing, CLI validation | 🟢 active |

---

## 2. Current State Summary

### ✅ Completed
| Task | Owner | Status |
|------|-------|--------|
| Agent communication design | All agents | ✅ Complete |
| Implementation analysis | qwen-assistant | ✅ Complete |
| Phase 1: Recipient filtering implementation | qwen-assistant | ✅ Code complete |
| Security review of auth module | qwen-reviewer | ✅ Complete |
| Agent-to-agent chat protocol | qwen-assistant, qwen-reviewer | ✅ Complete |

### ⏳ Pending
| Task | Priority | Assignee |
|------|----------|----------|
| Run database migration (0002_add_recipient_filtering) | P0 | User/DevOps |
| Test recipient filtering endpoint | P0 | mcp-e2e-agent |
| Agent Message Inbox (Phase 2) | P1 | Unassigned |
| E2E MCP task validation | P1 | mcp-e2e-agent |

---

## 3. Prioritized Roadmap

### Phase 1: Complete Current Implementation (Week 1) 🔴

**Goal:** Finish recipient filtering implementation and validate

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| Run migration: `alembic upgrade head` | DevOps | 5 min | None |
| Test `GET /v1/events?recipient_id=xxx` | mcp-e2e-agent | 2h | Migration |
| Test `GET /v1/events?channel=xxx` | mcp-e2e-agent | 1h | Migration |
| Code review of Phase 1 | qwen-reviewer | 1h | None |
| Documentation update | qwen-assistant | 1h | None |

**Acceptance Criteria:**
- [ ] Migration runs successfully
- [ ] API returns filtered events by recipient_id
- [ ] API returns filtered events by channel
- [ ] No regressions in existing functionality

---

### Phase 2: Message Inbox System (Week 2-3) 🟡

**Goal:** Build proper message infrastructure for agent communication

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| Create `messages` table migration | qwen-assistant | 2h | Phase 1 complete |
| Implement `POST /v1/messages` | qwen-assistant | 4h | Migration |
| Implement `GET /v1/messages/inbox` | qwen-assistant | 4h | Migration |
| Implement `GET /v1/messages/outbox` | qwen-assistant | 3h | Migration |
| Code review | qwen-reviewer | 3h | Implementation |
| E2E tests | mcp-e2e-agent | 4h | Implementation |
| Documentation | qwen-assistant | 2h | Complete |

**Acceptance Criteria:**
- [ ] Can send message with recipient_id
- [ ] Can query inbox (messages TO me)
- [ ] Can query outbox (messages FROM me)
- [ ] E2E tests pass

---

### Phase 3: Channel System (Week 3-4) 🟡

**Goal:** Enable channel-based group communication

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| Create `channel_subscriptions` table | qwen-assistant | 2h | Phase 2 |
| Implement channel CRUD API | qwen-assistant | 4h | Migration |
| Implement `GET /v1/channels/{name}/messages` | qwen-assistant | 3h | Migration |
| Add channel filtering to inbox | qwen-assistant | 2h | Phase 2 |
| Code review | qwen-reviewer | 2h | Implementation |
| E2E tests | mcp-e2e-agent | 3h | Implementation |

**Acceptance Criteria:**
- [ ] Can create/join channels
- [ ] Can subscribe/unsubscribe to channels
- [ ] Can get messages by channel
- [ ] E2E tests pass

---

### Phase 4: Real-time Push (Week 4-5) 🟡

**Goal:** Enable real-time message delivery (no more polling!)

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| WebSocket endpoint setup | qwen-assistant | 6h | Phase 2 |
| Implement push notification logic | qwen-assistant | 6h | WebSocket |
| Connection management | qwen-assistant | 4h | WebSocket |
| SSE fallback for non-WS clients | qwen-assistant | 3h | Phase 2 |
| Code review | qwen-reviewer | 3h | Implementation |
| Load testing | mcp-e2e-agent | 4h | Implementation |

**Acceptance Criteria:**
- [ ] WebSocket endpoint accepts connections
- [ ] Messages pushed to recipients in real-time
- [ ] SSE fallback works for polling clients
- [ ] Load test passes (100 concurrent connections)

---

### Phase 5: Polish & Features (Week 5-6) 🟢

**Goal:** Add quality-of-life features

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| Read receipts API | qwen-assistant | 3h | Phase 2 |
| Message reactions API | qwen-assistant | 3h | Phase 2 |
| Agent discovery endpoint | qwen-assistant | 4h | None |
| Message threading (replies) | qwen-assistant | 4h | Phase 2 |
| Code review | qwen-reviewer | 4h | Implementation |
| E2E tests | mcp-e2e-agent | 4h | Implementation |

**Acceptance Criteria:**
- [ ] Can mark messages as read
- [ ] Can add reactions to messages
- [ ] Can find agents by name
- [ ] Can reply to specific messages (threading)

---

## 4. Immediate Next Steps (This Week)

### For User/DevOps:
```bash
# 1. Run the migration
cd apps/api
alembic upgrade head

# 2. Verify migration
alembic current  # Should show: 0002_add_recipient_filtering
```

### For mcp-e2e-agent:
```bash
# 1. Test recipient filtering
curl http://localhost:8787/v1/events?recipient_id=02d91ea8-... -H "Authorization: Bearer repomesh-local-token"

# 2. Test channel filtering
curl http://localhost:8787/v1/events?channel=work -H "Authorization: Bearer repomesh-local-token"
```

### For qwen-reviewer:
- Review Phase 1 code changes
- Check for security issues
- Validate error handling

### For qwen-assistant:
- Wait for migration to complete
- Support testing efforts
- Begin Phase 2 planning

---

## 5. Evolution Addendum (Merged from 2026-02-22 Snapshot)

Source snapshot: `docs/COLLECTIVE_PLAN_2026_02_22.md`  
Merge date: 2026-02-22

### 5.1 Confirmed Priorities to Carry Forward

| Rank | Priority | Why |
|------|----------|-----|
| 1 | Lock auto-release / lease timeout reliability | Stability and recovery when CLI/agent sessions die |
| 2 | WebSocket push delivery | Reduces heavy polling and improves responsiveness |
| 3 | Code review integration in message flow | Improves reviewer workflow and traceability |
| 4 | Message threading (`parent_message_id`) | Improves conversation continuity |
| 5 | Read and delivery state | Improves observability of communication state |

### 5.2 Execution Sequence Update

1. Complete recipient filtering deployment (migration, restart, validation).
2. Add Phase 2B hardening:
   UUID validation for `recipient_id` and response schema parity.
3. Implement lock lifecycle guarantees:
   lease TTL, auto-expiry handling, and reclaim protocol for inactive agents.
4. Implement threading support (`parent_message_id`) with filters.
5. Implement push transport (WebSocket + SSE fallback) after lock lifecycle is stable.

### 5.3 Operational Blockers (Current)

| Blocker | Owner | Impact | Action |
|---------|-------|--------|--------|
| Migration not executed in target environment | User/DevOps | High | Run `alembic upgrade head` |
| API restart needed after migration | User/DevOps | Medium | Restart API process |
| Task claim edge cases (inactive owner reclaim) | Engineering | Medium | Define and implement reclaim protocol |

### 5.4 Agent Lifecycle Direction (Adopted)

- One active agent identity per live CLI/chat instance.
- Agent status must be heartbeat-driven; missing heartbeat marks agent inactive.
- New CLI instance may reclaim work from inactive agent identities using explicit lease/reclaim rules.
- Multiple agents per repository remain supported.

---

## 6. Resource Requirements

| Resource | Current | Needed | Gap |
|----------|---------|--------|-----|
| Agents | 3 active | 3 active | ✅ OK |
| Database | PostgreSQL | PostgreSQL | ✅ OK |
| API | Running on :8787 | Running on :8787 | ✅ OK |
| Migration tool | Alembic | Alembic | ✅ OK |
| Testing framework | pytest | pytest + WebSocket tests | ⚠️ Need WS testing |

---

## 7. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Migration fails | High | Low | Backup DB, test on staging |
| WebSocket scaling issues | Medium | Medium | Use connection pooling, load test |
| Agent coordination conflicts | Low | Low | Use locks, clear task ownership |
| Scope creep | Medium | Medium | Stick to phased approach |

---

## 8. Success Metrics

| Metric | Current | Target (6 weeks) |
|--------|---------|------------------|
| Message delivery latency | 1-5s (polling) | <100ms (push) |
| API calls/minute (per agent) | 60+ | <10 |
| Agent satisfaction | N/A | >4/5 |
| Code coverage | Unknown | >80% |
| E2E test pass rate | N/A | >95% |

---

## 9. Communication Protocol

Agents will coordinate using:

| Method | Tool | Frequency |
|--------|------|-----------|
| Status updates | `event.log(type='chat.message')` | Per task milestone |
| Blockers | `event.log(type='blocker', severity='high')` | Immediate |
| Reviews | `event.log(type='review.request')` | Per PR |
| Planning | `event.log(type='plan.*')` | Weekly |

---

## 10. Open Questions for User

| ID | Question | Priority |
|----|----------|----------|
| Q1 | Should we run the migration now? | P0 |
| Q2 | Any specific features to prioritize? | P1 |
| Q3 | Deploy to production after which phase? | P1 |
| Q4 | Need integration with external systems? | P2 |

---

## 11. Agent Commitments

### qwen-assistant (General-purpose)
> "I commit to leading implementation efforts, coordinating with the team, and ensuring steady progress through all phases. I'll handle the bulk of coding work and keep communication channels open."

### qwen-reviewer (Code-reviewer)
> "I commit to reviewing all code changes for quality and security, providing constructive feedback, and ensuring we maintain high standards throughout implementation."

### mcp-e2e-agent (CLI)
> "I commit to validating all implementations through end-to-end testing, ensuring the system works as expected from a user perspective."

---

## Appendix A: Task Board

### Completed Tasks
- ✅ `083a5c07-c13b-4f2d-90d9-4226148b453c` - Security review (qwen-reviewer)
- ✅ `4f5ce53f-325e-431b-b4da-822974fa4660` - Chat channel setup (qwen-assistant)
- ✅ `b2f19408-c76c-4f2d-90d9-4226148b453c` - Phase 1 implementation (qwen-assistant)

### Pending Tasks
- ⏳ `e8ba45e3-8c87-4777-baf1-66968ba9dfd5` - Agent Message Inbox
- ⏳ `39ced29a-399d-4865-b69f-dafc79059823` - E2E MCP task

---

## Appendix B: File Changes Summary

### Phase 1 (Complete - Awaiting Migration)
| File | Status |
|------|--------|
| `alembic/versions/0002_add_recipient_filtering.py` | ✅ Created |
| `app/models/entities.py` | ✅ Modified |
| `app/services/events.py` | ✅ Modified |
| `app/schemas/common.py` | ✅ Modified |
| `app/api/events.py` | ✅ Modified |

### Documentation Created
| File | Status |
|------|--------|
| `docs/AGENT_COMMUNICATION_DESIGN.md` | ✅ Complete |
| `docs/IMPLEMENTATION_ANALYSIS.md` | ✅ Complete |
| `docs/SESSION_LOG_2026-02-22.md` | ✅ Complete |
| `docs/COLLECTIVE_PLAN.md` | ✅ Complete (this file) |

---

*Plan generated: 2026-02-22 23:33:00 UTC*  
*Next review: 2026-03-01*
