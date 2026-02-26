from pydantic import BaseModel, Field
from typing import Optional


class ContentBlock(BaseModel):
    """A single content block within a message.

    Verified types from live data:
      - "text": has `text` field
      - "thinking": has `thinking` field (NOT `text`)
      - "toolCall": has `id`, `name`, `arguments` fields
      - "toolResult": appears as text blocks inside toolResult role messages
    """
    type: str = Field(..., description="Block type: text, thinking, toolCall, toolResult")
    text: Optional[str] = Field(None, description="Text content (text blocks)")
    thinking: Optional[str] = Field(None, description="Thinking content (thinking blocks)")
    # toolCall fields
    id: Optional[str] = Field(None, description="Tool call ID")
    name: Optional[str] = Field(None, description="Tool name")
    arguments: Optional[dict] = Field(None, description="Tool call arguments")
    # toolResult fields
    tool_call_id: Optional[str] = Field(None, description="References a toolCall.id")
    content: Optional[str | list] = Field(None, description="Tool result content")

    def extract_text(self) -> str:
        """Extract displayable text from this block."""
        if self.type == "text" and self.text:
            return self.text
        if self.type == "thinking" and self.thinking:
            return self.thinking
        if self.type == "toolCall" and self.name:
            return f"[Tool: {self.name}]"
        if self.type == "toolResult":
            return "[Tool Result]"
        return ""


class SessionMessage(BaseModel):
    """A single message extracted from a JSONL session file."""
    id: str = Field(..., description="Message ID from JSONL")
    role: str = Field(..., description="user, assistant, or toolResult")
    content: list[ContentBlock] = Field(default_factory=list, description="Content blocks")
    content_text: Optional[str] = Field(None, description="Concatenated text for display")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp")
    parent_id: Optional[str] = Field(None, description="Parent message ID")


class SessionSummary(BaseModel):
    """Summary of a session from sessions.json."""
    session_id: str = Field(..., description="Session key (e.g., agent:main:main)")
    updated_at: int = Field(..., description="Unix timestamp (ms)")
    model: Optional[str] = Field(None, description="Model used")
    model_provider: Optional[str] = Field(None, description="Model provider")
    label: Optional[str] = Field(None, description="Human-readable label")
    spawned_by: Optional[str] = Field(None, description="Parent session key")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")
    input_tokens: Optional[int] = Field(None, description="Input tokens")
    output_tokens: Optional[int] = Field(None, description="Output tokens")
    cache_read: Optional[int] = Field(None, description="Cache read tokens")
    message_count: Optional[int] = Field(None, description="Total JSONL lines")
    session_file: Optional[str] = Field(None, description="Path to JSONL file")


class SessionListResponse(BaseModel):
    """Response for session list endpoint."""
    sessions: list[SessionSummary] = Field(default_factory=list, description="Session summaries")
    total: int = Field(..., description="Total sessions matching filter")
    warning: Optional[str] = Field(None, description="Warning message")


class SessionMessageListResponse(BaseModel):
    """Response for session messages endpoint."""
    messages: list[SessionMessage] = Field(default_factory=list, description="Session messages")
    total: int = Field(..., description="Total message count")
    has_more: bool = Field(False, description="Whether more messages exist")
    skipped_lines: int = Field(0, description="Non-message JSONL lines skipped")
    warning: Optional[str] = Field(None, description="Warning message")
