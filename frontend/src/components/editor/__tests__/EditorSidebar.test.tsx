import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { EditorSidebar } from '../EditorSidebar';

// Mock data — defined inline in mocks to avoid hoisting issues
vi.mock('@/stores/agentStore', () => ({
  useAgentStore: vi.fn((selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      agents: [
        { id: 'main', name: 'COS', model: 'claude-opus-4-6', status: 'active', last_activity: null },
        { id: 'coder', name: 'Coder', model: 'claude-sonnet-4-6', status: 'idle', last_activity: null },
      ],
      fetchAgents: vi.fn(),
    }),
  ),
}));

const mockLoadFile = vi.fn();

vi.mock('@/stores/editorStore', () => ({
  useEditorStore: vi.fn((selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      currentFile: { agentId: 'main', path: 'SOUL.md', dirty: false, content: '', originalContent: '', etag: '', language: 'markdown' },
      loadFile: mockLoadFile,
    }),
  ),
}));

vi.mock('@/api/agents', () => ({
  agentsApi: {
    listFiles: vi.fn().mockResolvedValue({
      data: {
        files: [
          { name: 'SOUL.md', path: 'SOUL.md', size: 3800, mtime: 1772031239, is_binary: false, is_directory: false },
          { name: 'logo.png', path: 'logo.png', size: 15000, mtime: 1772031239, is_binary: true, is_directory: false },
          { name: 'notes.md', path: 'memory/notes.md', size: 500, mtime: 1772031239, is_binary: false, is_directory: false },
        ],
        total: 3,
        truncated: false,
      },
    }),
  },
}));

function renderSidebar(route = '/editor?agent=main') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <EditorSidebar />
    </MemoryRouter>,
  );
}

describe('EditorSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders agent dropdown with agents', async () => {
    renderSidebar();
    const trigger = screen.getByLabelText('Select agent');
    expect(trigger).toBeInTheDocument();
    // New custom dropdown shows agent name in button; full "Name (id)" in listbox
    await waitFor(() => {
      expect(screen.getByText('COS')).toBeInTheDocument();
    });
    // Open the dropdown and verify option text
    fireEvent.click(trigger);
    await waitFor(() => {
      expect(screen.getByText('COS (main)')).toBeInTheDocument();
    });
  });

  it('blocks binary file clicks', async () => {
    renderSidebar();
    await waitFor(() => {
      const binaryBtn = screen.getByTitle('Binary files cannot be edited');
      expect(binaryBtn).toBeDisabled();
    });
  });

  it('shows confirm dialog when switching files with dirty state', async () => {
    // Override mock to have dirty=true
    const { useEditorStore } = await import('@/stores/editorStore');
    (useEditorStore as unknown as ReturnType<typeof vi.fn>).mockImplementation(
      (selector: (state: Record<string, unknown>) => unknown) =>
        selector({
          currentFile: { agentId: 'main', path: 'SOUL.md', dirty: true, content: '', originalContent: '', etag: '', language: 'markdown' },
          loadFile: mockLoadFile,
        }),
    );

    renderSidebar();
    await waitFor(() => {
      const fileBtn = screen.getByText('notes.md');
      fireEvent.click(fileBtn);
    });
    expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
  });
});
