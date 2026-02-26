# OpenClaw Session Format Documentation

This document describes the format and structure of OpenClaw session data, including the session registry and session JSONL files.

## Session Registry

### Location

The session registry is stored in `sessions.json` files at:
- `~/.openclaw/sessions/sessions.json` (global registry)
- `~/.openclaw/agents/{agent_id}/sessions/sessions.json` (agent-specific registry)

### Structure

The registry is a JSON object keyed by session key strings. Each key maps to a session entry object.

### Session Key Format

Session keys follow the pattern: `agent:{agent_id}:{type}`

Examples:
- `agent:main:main`
- `agent:main:telegram:8393274395:direct:8393274395`
- `agent:cos:main`

### Session Entry Fields

| Field | Type | Description |
|-------|------|-------------|
| `sessionId` | string | UUID v4 identifier |
| `updatedAt` | int | Unix timestamp in milliseconds |
| `model` | string \| null | Model identifier (e.g., "claude-opus-4-6") |
| `modelProvider` | string \| null | Provider name (e.g., "anthropic") |
| `sessionFile` | string | Absolute path to JSONL file |
| `inputTokens` | int \| null | Total input tokens used |
| `outputTokens` | int \| null | Total output tokens generated |
| `totalTokens` | int \| null | Sum of input and output tokens |
| `cacheRead` | int \| null | Tokens read from cache |
| `cacheWrite` | int \| null | Tokens written to cache |
| `systemSent` | bool | Whether system prompt was sent |
| `abortedLastRun` | bool | Whether last run was aborted |
| `deliveryContext` | object | Delivery context object |
| `lastChannel` | string | Last used channel |
| `lastTo` | string | Last recipient |
| `lastAccountId` | string | Last account ID |
| `origin` | object | Origin metadata object |
| `skillsSnapshot` | object | System prompt + skill definitions (large) |
| `label` | string \| null | Human-readable label |
| `spawnedBy` | string \| null | Parent session key if spawned |
| `contextTokens` | int \| null | Context tokens |
| `totalTokensFresh` | int \| null | Fresh total tokens |
| `chatType` | string | Type of chat |

#### deliveryContext Object

```json
{
  "channel": "string",
  "to": "string",
  "accountId": "string"
}
```

#### origin Object

```json
{
  "label": "string",
  "provider": "string",
  "surface": "string",
  "chatType": "string",
  "from": "string",
  "to": "string",
  "accountId": "string"
}
```

### Important Notes

- **updatedAt is milliseconds**: The `updatedAt` field contains Unix timestamp in milliseconds (integer), NOT an ISO string.
- **Archived sessions**: Approximately 82% of `sessionFile` paths point to `.deleted.*` renamed files (archived sessions).
- **skillsSnapshot size**: The `skillsSnapshot` field is approximately 62KB per entry, representing 87% of total entry size. This field should be excluded from API responses to reduce payload size.

## Session JSONL Files

### Location

Session JSONL files are stored at the path specified in the `sessionFile` field of the session registry entry. Typically:
- `~/.openclaw/agents/{agent_id}/sessions/{sessionId}.jsonl`

### Format

Session files use JSON Lines format: one JSON object per line, each with a `type` discriminator field.

### Entry Types

#### 1. session

The first entry in the file containing session metadata.

```json
{
  "type": "session",
  "version": 3,
  "id": "uuid-string",
  "timestamp": "2026-01-01T00:00:00.000Z",
  "cwd": "/path/to/working/directory"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | "session" | Entry type discriminator |
| `version` | number | Session format version |
| `id` | string | Session UUID |
| `timestamp` | string | ISO 8601 timestamp |
| `cwd` | string | Working directory path |

#### 2. message

Conversation messages (primary data).

```json
{
  "type": "message",
  "id": "message-uuid",
  "parentId": "parent-uuid | null",
  "timestamp": "2026-01-01T00:00:00.000Z",
  "message": {
    "role": "user | assistant | toolResult",
    "content": [...]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | "message" | Entry type discriminator |
| `id` | string | Message UUID |
| `parentId` | string \| null | Parent message ID (creates linked chain) |
| `timestamp` | string | ISO 8601 timestamp |
| `message.role` | string | Message role: "user", "assistant", or "toolResult" |
| `message.content` | ContentBlock[] | Array of content blocks (ALWAYS an array) |

##### Additional Fields for Assistant Messages

```json
{
  "message": {
    "role": "assistant",
    "content": [...],
    "model": "claude-opus-4-6",
    "provider": "anthropic",
    "usage": {
      "input": 1000,
      "output": 500,
      "cacheRead": 200,
      "cacheWrite": 100,
      "totalTokens": 1500
    },
    "stopReason": "end_turn | tool_use | max_tokens"
  }
}
```

##### Additional Fields for toolResult Messages

```json
{
  "message": {
    "role": "toolResult",
    "content": [...],
    "toolCallId": "tool-call-uuid",
    "toolName": "ToolName",
    "isError": false,
    "details": {
      "status": "success",
      "exitCode": 0,
      "durationMs": 123
    }
  }
}
```

#### 3. model_change

Model switch events.

```json
{
  "type": "model_change",
  "provider": "anthropic",
  "modelId": "claude-opus-4-6"
}
```

#### 4. thinking_level_change

Thinking level adjustments.

```json
{
  "type": "thinking_level_change",
  "thinkingLevel": "high | medium | low"
}
```

#### 5. custom

Extension events for custom data.

```json
{
  "type": "custom",
  "customType": "model-snapshot",
  "data": {}
}
```

#### 6. compaction

Context compaction markers.

```json
{
  "type": "compaction"
}
```

### ContentBlock Types

Content blocks appear in the `message.content` arrays. All messages have content as an array of blocks, never as a plain string.

#### text Block

```json
{
  "type": "text",
  "text": "string content"
}
```

#### thinking Block

```json
{
  "type": "thinking",
  "thinking": "string content",
  "thinkingSignature": "optional-signature"
}
```

Note: The content field is called `thinking`, not `text`.

#### toolCall Block

```json
{
  "type": "toolCall",
  "id": "tool-call-uuid",
  "name": "ToolName",
  "arguments": {}
}
```

Note: Tool parameters are in the `arguments` field, not `input`.

#### toolResult Block

toolResult content appears as text blocks inside messages with role "toolResult".

### Statistics from Live Data

Based on analysis of production session data:
- 463 messages across sample sessions
- Content block distribution:
  - text: 377 blocks
  - thinking: 72 blocks
  - toolCall: 194 blocks
- 53 custom entries
- Various model_change and thinking_level_change entries

## Implementation Guidelines

### Parsing Sessions

1. **Filter by type**: When building conversation views, filter for `type == "message"` entries only.
2. **Content is always array**: The `message.content` field is ALWAYS an array of ContentBlock objects, never a plain string.
3. **Threading support**: Use `parentId` to create linked list structure for conversation threading.
4. **Handle missing files**: 82% of session files are archived (.deleted.* files). Return 200 with warning instead of 404.

### Content Block Handling

- **thinking blocks**: Use the `thinking` field (not `text`) for content.
- **toolCall blocks**: Use the `arguments` field (not `input`) for parameters.
- **Role-based rendering**: Different roles may contain different content block types.

### API Response Optimization

- **Exclude skillsSnapshot**: Always exclude the `skillsSnapshot` field from session registry responses. This field is approximately 62KB per entry and represents 87% of entry size.
- **Timestamp format**: Be aware that `updatedAt` in the registry is an integer (milliseconds), while timestamps in JSONL files are ISO 8601 strings.

### Session File Lifecycle

- Active sessions: Write to `{sessionId}.jsonl`
- Archived sessions: Rename to `.deleted.{sessionId}.jsonl`
- When accessing session files, check for both patterns
- Missing files are common and should not be treated as errors

## Example Usage

### Reading a Session

```python
import json

# Read registry
with open('sessions.json') as f:
    registry = json.load(f)

# Get session entry
session_entry = registry['agent:main:main']
session_file = session_entry['sessionFile']

# Read JSONL
messages = []
with open(session_file) as f:
    for line in f:
        entry = json.loads(line)
        if entry['type'] == 'message':
            messages.append(entry)
```

### Filtering Content Blocks

```python
# Extract text from message
def get_message_text(message_entry):
    texts = []
    for block in message_entry['message']['content']:
        if block['type'] == 'text':
            texts.append(block['text'])
        elif block['type'] == 'thinking':
            texts.append(block['thinking'])
    return '\n'.join(texts)
```

### Building Conversation Thread

```python
# Build parent-child relationships
def build_thread(messages):
    by_id = {msg['id']: msg for msg in messages}
    for msg in messages:
        parent_id = msg.get('parentId')
        if parent_id and parent_id in by_id:
            msg['parent'] = by_id[parent_id]
    return messages
```

## Version History

- **Version 3**: Current format as documented
- Earlier versions may have different field names or structures

## Related Documentation

- Agent Configuration: See agent-specific documentation for session creation and management
- API Endpoints: See API documentation for session retrieval endpoints
- Archival Policy: See operations documentation for session cleanup procedures
