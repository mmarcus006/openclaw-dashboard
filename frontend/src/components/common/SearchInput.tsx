/**
 * SearchInput — reusable search input with clear button and result count.
 */

import React from 'react';
import { Search, X } from 'lucide-react';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  resultCount?: number;
  className?: string;
}

export function SearchInput({
  value,
  onChange,
  placeholder = 'Search…',
  resultCount,
  className = '',
}: SearchInputProps): React.ReactElement {
  return (
    <div className={`relative ${className}`}>
      <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" aria-hidden="true" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-bg-secondary border border-border rounded-md py-2 pl-9 pr-16 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded text-text-secondary hover:text-text-primary"
          aria-label="Clear search"
        >
          <X size={14} />
        </button>
      )}
      {resultCount !== undefined && value && (
        <span className="absolute right-8 top-1/2 -translate-y-1/2 text-xs text-text-tertiary">
          {resultCount}
        </span>
      )}
    </div>
  );
}
