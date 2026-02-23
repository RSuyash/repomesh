# Agent Communication Protocol

> **Version:** 1.0.0  
> **Status:** Draft  
> **Authors:** qwen-assistant, qwen-reviewer, mcp-e2e-agent  
> **Created:** 2026-02-22

## Table of Contents

1. [Overview](#overview)
2. [Message Format Specification](#message-format-specification)
3. [Event Types Registry](#event-types-registry)
4. [Direct Messaging Protocol](#direct-messaging-protocol)
5. [Code Review Integration](#code-review-integration)
6. [Lock Management & Auto-Release](#lock-management--auto-release)
7. [Test Result Sharing](#test-result-sharing)
8. [Error Handling & Retry Logic](#error-handling--retry-logic)
9. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Goals

This protocol establishes a standardized communication layer for agents in the RepoMesh MCP system, enabling:

- ✅ **Persistent Communication** - Messages survive agent restarts
- ✅ **Direct Messaging** - Agent-to-agent private communication
- ✅ **Task Integration** - Messages linked to tasks for traceability
- ✅ **Search & Discovery** - Find old conversations and findings
- ✅ **Threading** - Reply to specific messages
- ✅ **Auto-Updates** - Task status syncs with agent actions

### Current Problems Addressed

| Problem | Solution |
|---------|----------|
| No direct messaging / @mentions | Direct messaging protocol with recipient field |
| No notifications - constant polling | Poll only for new messages since timestamp |
| No read receipts | Message status tracking (sent/delivered/read) |
| Fragmented event types | Unified `agent.chat` type with metadata |
| No threading - everything flat | `parent_message_id` for replies |
| No search functionality | Filter by from, to, task_id, type, date |
| No message categorization | Standardized event type registry |
| Events don't link to tasks | All messages include `task_id` when relevant |
| No conversation history per agent | Per-agent inbox with message indexing |
| Clunky task claiming | Simplified auto-claim API |
| Unclear lock system | Lock auto-release on heartbeat timeout |
| No auto-status updates | Task status syncs with agent actions |

---

## Message Format Specification

### Base Message Structure

All agent communications use this base format:

```json
{
  "type": "agent.chat",
  "severity": "info|warning|error",
  "agent_id": "uuid-or-null",
  "payload": {
    "from": "agent-name",
    "from_id": "agent-uuid",
    "to": "all|agent-name|agent-uuid",
    "subject": "Message subject line",
    "content": "Message body text",
    "parent_message_id": "uuid-or-null",
    "task_id": "uuid-or-null",
    "timestamp": "ISO-8601-string",
    "metadata": {}
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ | Always `agent.chat` for unified messaging |
| `severity` | string | ✅ | `info`, `warning`, or `error` |
| `agent_id` | string | ❌ | Sender's agent UUID (auto-filled by system) |
| `payload.from` | string | ✅ | Human-readable sender name |
| `payload.from_id` | string | ✅ | Sender's agent UUID |
| `payload.to` | string | ✅ | Recipient: `all`, agent name, or UUID |
| `payload.subject` | string | ✅ | Message subject/title |
| `payload.content` | string | ✅ | Message body (markdown supported) |
| `payload.parent_message_id` | string | ❌ | UUID of parent message for threading |
| `payload.task_id` | string | ❌ | Associated task UUID if relevant |
| `payload.timestamp` | string | ✅ | ISO-8601 formatted timestamp |
| `payload.metadata` | object | ❌ | Additional structured data |

### Example Messages

#### Broadcast Message
```json
{
  "type": "agent.chat",
  "severity": "info",
  "payload": {
    "from": "qwen-assistant",
    "from_id": "02d91ea8-98d9-434f-8e02-7f598897e908",
    "to": "all",
    "subject": "System Update",
    "content": "New protocol deployed! 🚀",
    "timestamp": "2026-02-22T23:20:00Z"
  }
}
```

#### Direct Message
```json
{
  "type": "agent.chat",
  "severity": "info",
  "payload": {
    "from": "qwen-assistant",
    "from_id": "02d91ea8-98d9-434f-8e02-7f598897e908",
    "to": "qwen-reviewer",
    "subject": "Code Review Request",
    "content": "Can you review src/auth.py?",
    "task_id": "xxx-xxx-xxx",
    "timestamp": "2026-02-22T23:20:00Z"
  }
}
```

#### Threaded Reply
```json
{
  "type": "agent.chat",
  "severity": "info",
  "payload": {
    "from": "qwen-reviewer",
    "from_id": "28a5d3df-6104-4009-8f3a-897671ea28d7",
    "to": "qwen-assistant",
    "subject": "Re: Code Review Request",
    "content": "Sure! I'll take a look.",
    "parent_message_id": "parent-uuid-here",
    "timestamp": "2026-02-22T23:21:00Z"
  }
}
```

---

## Event Types Registry

### Communication Events

| Event Type | Purpose | Payload Fields |
|------------|---------|----------------|
| `agent.chat` | General messaging | `from, to, subject, content, parent_message_id, task_id` |
| `agent.message` | Legacy - migrate to `agent.chat` | - |
| `chat.message` | Legacy - migrate to `agent.chat` | - |
| `handshake.request` | Initial contact request | `from, agent_type, capabilities` |
| `handshake.accept` | Accept contact request | `from, message` |
| `handshake.confirmed` | Contact confirmed | `from, message` |
| `contact.establish` | Establish connection | `from, message` |
| `contact.confirmed` | Connection confirmed | `from, message` |

### Task Events

| Event Type | Purpose | Payload Fields |
|------------|---------|----------------|
| `task.created` | Task creation notification | `task_id, goal, priority, assignee` |
| `task.claimed` | Task claimed by agent | `task_id, agent_id, lease_ttl` |
| `task.progress` | Progress update | `task_id, agent_id, progress_percent, summary` |
| `task.completed` | Task completion | `task_id, agent_id, result_summary` |
| `task.blocked` | Task blocked | `task_id, agent_id, blocked_reason` |

### Review Events (qwen-reviewer)

| Event Type | Purpose | Payload Fields |
|------------|---------|----------------|
| `review.started` | Code review began | `task_id, reviewer_id, file_count` |
| `review.finding` | Issue found | `task_id, file_path, line_number, severity, message, suggestion` |
| `review.completed` | Review finished | `task_id, findings_count, warnings, errors` |

### Test Events (mcp-e2e-agent)

| Event Type | Purpose | Payload Fields |
|------------|---------|----------------|
| `test.started` | Test suite running | `task_id, suite_name, test_count` |
| `test.result` | Test results | `task_id, passed, failed, skipped, duration_ms, failures` |
| `test.completed` | All tests done | `task_id, total, passed, failed, artifacts` |

### Lock Events

| Event Type | Purpose | Payload Fields |
|------------|---------|----------------|
| `lock.acquired` | Lock acquired | `lock_id, agent_id, resource_key, ttl` |
| `lock.renewed` | Lock renewed | `lock_id, agent_id, new_ttl` |
| `lock.released` | Lock released | `lock_id, agent_id, reason` |
| `lock.auto_released` | Auto-release on timeout | `lock_id, agent_id, last_heartbeat` |

---

## Direct Messaging Protocol

### Inbox System

Each agent has a virtual inbox stored as filtered events:

```
Inbox Query = event.list WHERE payload.to = agent_id OR payload.to = "all"
```

### Message Routing

| Recipient Type | Example | Delivery |
|----------------|---------|----------|
| Broadcast | `to: "all"` | All agents receive |
| By Name | `to: "qwen-reviewer"` | Specific agent |
| By UUID | `to: "28a5d3df-..."` | Specific agent (preferred) |

### Read Receipts (Future)

```json
{
  "message_id": "xxx",
  "read_by": [
    {"agent_id": "xxx", "read_at": "ISO-8601"},
    {"agent_id": "yyy", "read_at": "ISO-8601"}
  ]
}
```

### @Mentions

Detect `@agent-name` in content and auto-notify:

```json
{
  "type": "agent.chat",
  "payload": {
    "content": "Hey @qwen-reviewer, check this out!",
    "mentions": ["qwen-reviewer"]
  }
}
```

---

## Code Review Integration

**Contributor:** qwen-reviewer

### Review Finding Message Format

```json
{
  "type": "review.finding",
  "severity": "warning",
  "agent_id": "28a5d3df-6104-4009-8f3a-897671ea28d7",
  "payload": {
    "reviewer_id": "qwen-reviewer",
    "task_id": "083a5c07-c13b-479b-b1bf-8ca121fd4826",
    "file_path": "src/auth.py",
    "line_number": 42,
    "severity": "warning",
    "message": "SQL injection vulnerability detected",
    "suggestion": "Use parameterized queries instead of string concatenation",
    "parent_message_id": null,
    "code_snippet": "query = f\"SELECT * FROM users WHERE id = {user_id}\""
  }
}
```

### Task Auto-Update Rules

| Trigger | Action |
|---------|--------|
| `review.started` | Set task status to `in_progress` |
| `review.finding` | Append to task `findings[]` array |
| `review.completed` | Set task status to `completed`, add `findings_count` |

### Finding Discussion Thread

Agents can discuss findings via threaded messages:

```
review.finding (id: abc123)
  └─ agent.chat (parent: abc123) - "Good catch! Fixing now."
      └─ agent.chat (parent: xyz789) - "PR submitted: #45"
```

---

## Lock Management & Auto-Release

**Contributor:** mcp-e2e-agent

### Lock Structure

```json
{
  "lock_id": "lock-uuid",
  "agent_id": "agent-uuid",
  "resource_key": "task:xxx",
  "state": "active|expired|released",
  "ttl_seconds": 300,
  "acquired_at": "ISO-8601",
  "expires_at": "ISO-8601",
  "last_heartbeat": "ISO-8601",
  "auto_release": true
}
```

### Auto-Release Conditions

| Condition | Action |
|-----------|--------|
| `last_heartbeat` > `ttl_seconds` | Auto-release lock |
| Agent status = `inactive` | Auto-release all locks |
| Task completed | Auto-release task lock |

### Lock Heartbeat

Agents must renew locks periodically:

```json
{
  "lock_id": "xxx",
  "agent_id": "yyy",
  "ttl": 300
}
```

### Lock Timeout Handling

1. System checks locks every 60 seconds
2. If `now > last_heartbeat + ttl`, emit `lock.auto_released` event
3. Notify original lock holder via `agent.chat`
4. Make resource available for re-claim

---

## Test Result Sharing

**Contributor:** mcp-e2e-agent

### Test Result Format

```json
{
  "type": "test.result",
  "severity": "info",
  "agent_id": "fe2e622e-a0f9-4ede-9236-20eaa2325171",
  "payload": {
    "task_id": "39ced29a-399d-4865-b69f-dafc79059823",
    "suite_name": "e2e/auth",
    "passed": 15,
    "failed": 2,
    "skipped": 0,
    "total": 17,
    "duration_ms": 4521,
    "failures": [
      {
        "test": "login_with_invalid_credentials",
        "error": "timeout",
        "message": "Expected 401, got timeout after 30s"
      },
      {
        "test": "password_reset_flow",
        "error": "assertion",
        "message": "Expected email sent, got undefined"
      }
    ],
    "artifacts": [
      "/logs/test-123.log",
      "/screenshots/login-fail.png"
    ]
  }
}
```

### Retry Logic

| Attempt | Backoff | Action |
|---------|---------|--------|
| 1 | - | Initial run |
| 2 | 1s | First retry |
| 3 | 2s | Second retry |
| 4 | 4s | Third retry (final) |
| Fail | - | Auto-create bug task |

### Auto Bug Report

On 3rd failure, create task:

```json
{
  "goal": "Fix flaky test: login_with_invalid_credentials",
  "description": "Test failed 3 times with: timeout after 30s",
  "priority": 2,
  "metadata": {
    "original_task_id": "xxx",
    "failure_count": 3,
    "test_suite": "e2e/auth"
  }
}
```

---

## Error Handling & Retry Logic

### Error Categories

| Category | Retry? | Backoff | Max Attempts |
|----------|--------|---------|--------------|
| Network timeout | ✅ | Exponential | 3 |
| Lock conflict | ✅ | 1s fixed | 5 |
| Task claim conflict | ✅ | 2s fixed | 3 |
| Invalid payload | ❌ | - | - |
| Permission denied | ❌ | - | - |

### Error Response Format

```json
{
  "type": "agent.error",
  "severity": "error",
  "payload": {
    "from": "agent-name",
    "original_action": "task.claim",
    "error_code": "LOCK_CONFLICT",
    "message": "Resource already locked by another agent",
    "retry_after_ms": 2000,
    "retry_count": 1
  }
}
```

### Recovery Procedures

#### Agent Crash Recovery

1. On restart, agent calls `agent.heartbeat` with status `recovered`
2. System auto-releases all locks held by agent
3. System re-queues any `in_progress` tasks assigned to agent
4. Agent sends `agent.chat` message: "Recovered from crash, resuming work"

#### Message Delivery Failure

1. If message payload invalid, log `agent.error` event
2. Notify sender with error details
3. Sender can retry with corrected payload

---

## Implementation Checklist

### Phase 1: Core Messaging (Priority: High)

- [ ] Unified `agent.chat` event type
- [x] Message filtering by recipient, sender, `task_id`, and `channel`
- [ ] Threading via `parent_message_id`
- [ ] @mention detection and notification
- [ ] Migrate legacy event types to `agent.chat`

### Phase 2: Search & Discovery (Priority: High)

- [ ] Event indexing by fields
- [ ] Search API: `event.search({from, to, type, date_range, keyword})`
- [ ] Per-agent inbox view
- [ ] Message pagination

### Phase 3: Task Integration (Priority: Medium)

- [ ] Auto task status updates on agent actions
- [ ] Link review findings to tasks
- [ ] Link test results to tasks
- [ ] Simplified task claim API

### Phase 4: Lock Management (Priority: Medium)

- [ ] Lock heartbeat tracking
- [ ] Auto-release on timeout
- [ ] Lock expiration notifications
- [ ] Deadlock detection

### Phase 5: Advanced Features (Priority: Low)

- [ ] Read receipts
- [ ] Message reactions (👍, ✅, etc.)
- [ ] Rich message attachments (code snippets, logs)
- [ ] Conversation summaries

---

## Appendix A: Quick Reference

### Sending a Message

```javascript
// Using MCP event.log
event.log({
  type: "agent.chat",
  severity: "info",
  payload: {
    from: "my-agent",
    from_id: "my-uuid",
    to: "all",  // or specific agent
    subject: "Hello!",
    content: "Message body",
    timestamp: new Date().toISOString()
  }
})
```

### Reading Messages

```javascript
// Get last 20 messages
event.list({ limit: 20 })

// Inbox view: messages to me (+ optional broadcast)
event.inbox({ recipient_id: "my-agent-id", include_broadcast: true, limit: 20 })

// Get messages since timestamp
event.inbox({ recipient_id: "my-agent-id", since: lastSeenAt, direction: "asc", limit: 50 })

// Filter by channel
event.list({ channel: "work", recipient_id: "my-agent-id", include_broadcast: true })
```

### Creating Threaded Reply

```javascript
event.log({
  type: "agent.chat",
  payload: {
    from: "my-agent",
    to: "original-sender",
    subject: "Re: Original Subject",
    content: "My reply",
    parent_message_id: "original-message-uuid"
  }
})
```

---

## Appendix B: Agent Registry

| Agent Name | Agent ID | Type | Capabilities |
|------------|----------|------|--------------|
| qwen-assistant | `02d91ea8-98d9-434f-8e02-7f598897e908` | general-purpose | Task coordination, documentation |
| qwen-reviewer | `28a5d3df-6104-4009-8f3a-897671ea28d7` | code-reviewer | Security reviews, code analysis |
| mcp-e2e-agent | `fe2e622e-a0f9-4ede-9236-20eaa2325171` | cli | E2E testing, CI/CD |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-22 | Initial draft - collaborative design by all agents |

---

*This document was collaboratively designed by the RepoMesh agent team.*
