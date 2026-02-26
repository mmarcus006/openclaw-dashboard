import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// We test the exported default EditorPage
// Need to mock Monaco, stores, and API

vi.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <textarea
      data-testid="mock-monaco"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

vi.mock('@/themes/monacoTheme', () => ({
  openclawDarkTheme: { base: 'vs-dark', inherit: true, rules: [], colors: {} },
  OPENCLAW_THEME_NAME: 'openclaw-dark',
}));

const mockLoadFile = vi.fn();
let mockCurrentFile: Record<string, unknown> | null = null;

vi.mock('@/stores/editorStore', () => ({
  useEditorStore: vi.fn((selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      currentFile: mockCurrentFile,
      loading: false,
      saving: false,
      error: null,
      conflictEtag: null,
      loadFile: mockLoadFile,
      updateContent: vi.fn(),
      saveFile: vi.fn(),
      discardChanges: vi.fn(),
      keepMyChanges: vi.fn(),
      clearConflict: vi.fn(),
    }),
  ),
}));

vi.mock('@/stores/agentStore', () => ({
  useAgentStore: vi.fn((selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      agents: [{ id: 'main', name: 'COS', model: 'claude-opus-4-6', status: 'active', last_activity: null }],
      fetchAgents: vi.fn(),
    }),
  ),
}));

vi.mock('@/api/agents', () => ({
  agentsApi: {
    listFiles: vi.fn().mockResolvedValue({
      data: {
        files: [
          { name: 'SOUL.md', path: 'SOUL.md', size: 3800, mtime: 1772031239, is_binary: false, is_directory: false },
        ],
        total: 1,
        truncated: false,
      },
    }),
  },
}));

vi.mock('@/stores/toastStore', () => ({
  useToastStore: vi.fn((selector: (state: Record<string, unknown>) => unknown) =>
    selector({ addToast: vi.fn() }),
  ),
}));

// Mock EditorSidebar (being created by another agent)
vi.mock('@/components/editor/EditorSidebar', () => ({
  EditorSidebar: () => <div data-testid="editor-sidebar">Sidebar</div>,
}));

// Need to import after mocks
import EditorPage from '../EditorPage';

function renderEditor(route = '/editor?agent=main&path=SOUL.md') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <EditorPage />
    </MemoryRouter>,
  );
}

describe('EditorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCurrentFile = null;
  });

  it('shows empty state when no file is selected', () => {
    render(
      <MemoryRouter initialEntries={['/editor?agent=main']}>
        <EditorPage />
      </MemoryRouter>,
    );
    expect(screen.getByText('Select a file to edit')).toBeInTheDocument();
  });

  it('loads file from URL params', () => {
    mockCurrentFile = {
      agentId: 'main',
      path: 'SOUL.md',
      content: '# Soul',
      originalContent: '# Soul',
      dirty: false,
      etag: 'abc123',
      language: 'markdown',
    };
    renderEditor();
    // Breadcrumb should show file path (use getAllByText since it appears in breadcrumb and toolbar)
    const soulMdElements = screen.getAllByText('SOUL.md');
    expect(soulMdElements.length).toBeGreaterThan(0);
  });

  it('shows confirm dialog on breadcrumb navigation when dirty', () => {
    mockCurrentFile = {
      agentId: 'main',
      path: 'SOUL.md',
      content: '# Modified',
      originalContent: '# Soul',
      dirty: true,
      etag: 'abc123',
      language: 'markdown',
    };
    renderEditor();
    // Click "Agents" breadcrumb (there are multiple "Agents" text, get the one in breadcrumb)
    const agentsLinks = screen.getAllByText('Agents');
    const breadcrumbAgentsLink = agentsLinks.find(el => el.tagName === 'BUTTON');
    if (breadcrumbAgentsLink) {
      fireEvent.click(breadcrumbAgentsLink);
    }
    expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
  });
});
