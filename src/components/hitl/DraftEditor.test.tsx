import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { DraftEditor } from './DraftEditor';
import type { DraftArticle } from '../../types/workflow';

// MarkdownPreview uses react-markdown + remark/rehype plugins.
// Mock it to avoid complex plugin setup in jsdom.
vi.mock('../common/MarkdownPreview', () => ({
  MarkdownPreview: ({ content }: { content: string }) => <div data-testid="markdown-preview">{content}</div>,
}));

const mockDraft: DraftArticle = {
  article_title: 'How eBPF Changes Observability',
  executive_summary: 'eBPF enables kernel-level visibility without instrumentation.',
  sections: [
    { heading: 'What is eBPF', content: 'eBPF is a Linux kernel technology...' },
    { heading: 'Use Cases', content: 'Tracing, networking, security...' },
  ],
  conclusion: 'eBPF is transforming the observability landscape.',
  metadata: { seo_slug: 'ebpf-observability', meta_description: 'Guide to eBPF', title_tag: 'eBPF Guide', word_count: 1200 },
};

function setup(overrides = {}) {
  const props = {
    draft: mockDraft,
    actualWriter: 'claude',
    fallbackReason: '',
    onApprove: vi.fn(),
    onRegenerate: vi.fn(),
    ...overrides,
  };
  render(<DraftEditor {...props} />);
  return props;
}

describe('DraftEditor', () => {
  describe('preview mode (default)', () => {
    it('renders the markdown preview', () => {
      setup();
      expect(screen.getByTestId('markdown-preview')).toBeInTheDocument();
    });

    it('shows Approve Draft and Edit buttons', () => {
      setup();
      expect(screen.getByRole('button', { name: /approve draft/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /regenerate/i })).toBeInTheDocument();
    });

    it('calls onApprove with no argument when Approve Draft clicked', async () => {
      const { onApprove } = setup();
      await userEvent.click(screen.getByRole('button', { name: /approve draft/i }));
      expect(onApprove).toHaveBeenCalledOnce();
      // onApprove() is called with no arguments (not explicitly undefined)
      expect(onApprove.mock.calls[0]).toHaveLength(0);
    });

    it('calls onRegenerate with feedback text', async () => {
      const { onRegenerate } = setup();
      const textarea = screen.getByRole('textbox');
      await userEvent.type(textarea, 'Add more citations');
      await userEvent.click(screen.getByRole('button', { name: /regenerate/i }));
      expect(onRegenerate).toHaveBeenCalledWith('Add more citations');
    });

    it('calls onRegenerate with empty string when no feedback', async () => {
      const { onRegenerate } = setup();
      await userEvent.click(screen.getByRole('button', { name: /regenerate/i }));
      expect(onRegenerate).toHaveBeenCalledWith('');
    });

    it('shows fallback warning when fallbackReason is set', () => {
      setup({ fallbackReason: 'Claude credits exhausted' });
      expect(screen.getByText(/claude credits exhausted/i)).toBeInTheDocument();
    });
  });

  describe('edit mode', () => {
    it('enters edit mode on Edit click', async () => {
      setup();
      await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));
      // Article title input should appear
      expect(screen.getByDisplayValue('How eBPF Changes Observability')).toBeInTheDocument();
    });

    it('shows Cancel and Save & Approve buttons in edit mode', async () => {
      setup();
      await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save & approve/i })).toBeInTheDocument();
    });

    it('Cancel returns to preview mode without calling onApprove', async () => {
      const { onApprove } = setup();
      await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));
      await userEvent.click(screen.getByRole('button', { name: /cancel/i }));
      expect(onApprove).not.toHaveBeenCalled();
      expect(screen.getByTestId('markdown-preview')).toBeInTheDocument();
    });

    it('Save & Approve calls onApprove with edited draft', async () => {
      const { onApprove } = setup();
      await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));

      const titleInput = screen.getByDisplayValue('How eBPF Changes Observability');
      await userEvent.clear(titleInput);
      await userEvent.type(titleInput, 'Revised eBPF Title');

      await userEvent.click(screen.getByRole('button', { name: /save & approve/i }));

      expect(onApprove).toHaveBeenCalledOnce();
      const editedDraft = onApprove.mock.calls[0][0] as DraftArticle;
      expect(editedDraft.article_title).toBe('Revised eBPF Title');
    });

    it('Cancel reverts edits (original title restored in next edit session)', async () => {
      setup();
      await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));

      const titleInput = screen.getByDisplayValue('How eBPF Changes Observability');
      await userEvent.clear(titleInput);
      await userEvent.type(titleInput, 'Changed Title');

      await userEvent.click(screen.getByRole('button', { name: /cancel/i }));

      // Re-enter edit mode — should show original title
      await userEvent.click(screen.getByRole('button', { name: /^edit$/i }));
      expect(screen.getByDisplayValue('How eBPF Changes Observability')).toBeInTheDocument();
    });
  });

  describe('optional draft sections', () => {
    it('includes comparison, tco, and anti-recommendation content in preview', () => {
      const draftWithExtras: DraftArticle = {
        ...mockDraft,
        comparison: { heading: 'Comparison', alternatives: [], content: 'Compared to alternatives...' },
        tco_analysis: { heading: 'TCO', content: 'Total cost analysis...' },
        anti_recommendation: { heading: 'When NOT to Use', content: 'Avoid when...' },
      };
      setup({ draft: draftWithExtras });
      const preview = screen.getByTestId('markdown-preview');
      expect(preview.textContent).toContain('Compared to alternatives...');
      expect(preview.textContent).toContain('Total cost analysis...');
      expect(preview.textContent).toContain('Avoid when...');
    });

    it('shows Gemini (fallback) label when actualWriter is gemini_fallback', () => {
      setup({ actualWriter: 'gemini_fallback' });
      expect(screen.getByText(/gemini \(fallback\)/i)).toBeInTheDocument();
    });
  });
});
