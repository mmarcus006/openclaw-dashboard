/**
 * ContentBlockRenderer — renders individual content blocks with type-specific styling.
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench } from 'lucide-react';
import type { ContentBlock } from '@/api/sessions';

interface ContentBlockRendererProps {
  block: ContentBlock;
}

function ThinkingBlock({ text }: { text: string }): React.ReactElement {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-border rounded-md my-1">
      <button
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary w-full text-left"
        onClick={() => setOpen(!open)}
      >
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        Thinking...
      </button>
      {open && (
        <div className="px-3 pb-2 text-xs text-text-secondary whitespace-pre-wrap border-t border-border">
          {text}
        </div>
      )}
    </div>
  );
}

function ToolCallBlock({ block }: { block: ContentBlock }): React.ReactElement {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-border rounded-md my-1 bg-bg-hover/30">
      <button
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs w-full text-left"
        onClick={() => setOpen(!open)}
      >
        <Wrench size={12} className="text-accent flex-shrink-0" />
        <span className="text-text-primary font-mono">{block.name}</span>
        {open ? <ChevronDown size={12} className="ml-auto text-text-secondary" /> : <ChevronRight size={12} className="ml-auto text-text-secondary" />}
      </button>
      {open && block.arguments && (
        <pre className="px-3 pb-2 text-xs text-text-secondary overflow-x-auto border-t border-border">
          {JSON.stringify(block.arguments, null, 2)}
        </pre>
      )}
    </div>
  );
}

function ToolResultBlock({ block }: { block: ContentBlock }): React.ReactElement {
  const [open, setOpen] = useState(false);
  const resultText = typeof block.content === 'string'
    ? block.content
    : Array.isArray(block.content)
      ? block.content.map((c: unknown) => (typeof c === 'object' && c !== null && 'text' in c ? (c as { text: string }).text : String(c))).join('\n')
      : '';

  if (!resultText) return <></>;

  return (
    <div className="border border-border/50 rounded-md my-1 ml-4">
      <button
        className="flex items-center gap-1.5 px-3 py-1 text-xs text-text-secondary hover:text-text-primary w-full text-left"
        onClick={() => setOpen(!open)}
      >
        {open ? <ChevronDown size={10} /> : <ChevronRight size={10} />}
        Tool Result
      </button>
      {open && (
        <pre className="px-3 pb-2 text-xs text-text-secondary overflow-x-auto border-t border-border/50 max-h-60 overflow-y-auto">
          {resultText.length > 2000 ? resultText.slice(0, 2000) + '...' : resultText}
        </pre>
      )}
    </div>
  );
}

export function ContentBlockRenderer({ block }: ContentBlockRendererProps): React.ReactElement {
  switch (block.type) {
    case 'text':
      return (
        <div className="text-sm text-text-primary whitespace-pre-wrap">
          {block.text}
        </div>
      );
    case 'thinking':
      return <ThinkingBlock text={block.thinking ?? ''} />;
    case 'toolCall':
      return <ToolCallBlock block={block} />;
    case 'toolResult':
      return <ToolResultBlock block={block} />;
    default:
      return <div className="text-xs text-text-secondary">[{block.type}]</div>;
  }
}
