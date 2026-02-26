/**
 * SessionViewer — conversation message viewer with content block rendering.
 */

import React, { useState } from 'react';
import { Copy, Check, ChevronDown } from 'lucide-react';
import { Spinner } from '@/components/common/Spinner';
import { EmptyState } from '@/components/common/EmptyState';
import { Button } from '@/components/common/Button';
import { ContentBlockRenderer } from './ContentBlockRenderer';
import { useSessionStore } from '@/stores/sessionStore';
import type { SessionMessage } from '@/api/sessions';

function CopyButton({ text }: { text: string }): React.ReactElement {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API may fail in some contexts
    }
  };

  return (
    <button
      onClick={() => void handleCopy()}
      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-bg-hover"
      title="Copy message"
    >
      {copied ? <Check size={12} className="text-success" /> : <Copy size={12} className="text-text-secondary" />}
    </button>
  );
}

interface MessageBubbleProps {
  message: SessionMessage;
}

function MessageBubble({ message }: MessageBubbleProps): React.ReactElement {
  const [expanded, setExpanded] = useState(false);
  const isUser = message.role === 'user';
  const isToolResult = message.role === 'toolResult';
  const contentText = message.content_text ?? '';
  const isLong = contentText.length > 500;
  const displayText = !expanded && isLong ? contentText.slice(0, 500) + '...' : contentText;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`group relative max-w-[85%] rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-accent/15 border border-accent/30'
            : isToolResult
              ? 'bg-bg-hover/50 border border-border/50'
              : 'bg-bg-card border border-border'
        }`}
      >
        {/* Role label */}
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className={`text-xs font-medium ${isUser ? 'text-accent' : 'text-text-secondary'}`}>
            {isUser ? 'User' : isToolResult ? 'Tool Result' : 'Assistant'}
          </span>
          <div className="flex items-center gap-1">
            {message.timestamp && (
              <span className="text-[10px] text-text-tertiary">
                {new Date(message.timestamp).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
            <CopyButton text={contentText} />
          </div>
        </div>

        {/* Content blocks (full mode) or content_text (list mode) */}
        {message.content.length > 0 ? (
          <div className="space-y-1">
            {message.content.map((block, i) => (
              <ContentBlockRenderer key={i} block={block} />
            ))}
          </div>
        ) : (
          <div className="text-sm text-text-primary whitespace-pre-wrap">
            {displayText}
          </div>
        )}

        {/* Show more toggle */}
        {isLong && message.content.length === 0 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-xs text-accent hover:text-accent/80"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>
    </div>
  );
}

export function SessionViewer(): React.ReactElement {
  const messages = useSessionStore((s) => s.messages);
  const loading = useSessionStore((s) => s.messagesLoading);
  const error = useSessionStore((s) => s.messagesError);
  const hasMore = useSessionStore((s) => s.messagesHasMore);
  const total = useSessionStore((s) => s.messagesTotal);
  const loadMore = useSessionStore((s) => s.loadMoreMessages);
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId);

  if (!selectedSessionId) {
    return (
      <EmptyState
        title="Select a session"
        description="Click a session from the list to view the conversation."
      />
    );
  }

  if (loading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" label="Loading messages..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-danger text-sm">{error}</p>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <EmptyState
        title="No messages"
        description="This session has no messages or the session file was archived."
      />
    );
  }

  return (
    <div className="space-y-1">
      <div className="text-xs text-text-secondary mb-3">
        {total} messages
      </div>
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {hasMore && (
        <div className="flex justify-center pt-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void loadMore()}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Load more messages'}
            <ChevronDown size={14} />
          </Button>
        </div>
      )}
    </div>
  );
}
