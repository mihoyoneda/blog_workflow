import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { FinalApproval } from './FinalApproval';
import type { DraftArticle, QACheck, RerunStrategy } from '../../types/workflow';

const mockDraft: DraftArticle = {
  article_title: 'Test Article',
  executive_summary: 'Summary.',
  sections: [{ heading: 'Section 1', content: 'Content here.' }],
  conclusion: 'Final thoughts.',
  metadata: {
    seo_slug: 'test-article',
    meta_description: 'A test article',
    title_tag: 'Test Article | Blog',
    word_count: 800,
  },
};

const mockQAChecks: QACheck[] = [
  { category: 'Structure', check: 'Has title', passed: true, note: '' },
  { category: 'Structure', check: 'Has content', passed: false, note: 'Too short' },
  { category: 'SEO', check: 'Has meta description', passed: true, note: '' },
];

const mockStrategies: RerunStrategy[] = [
  { name: 'strengthen_evidence', label: 'Strengthen Evidence', icon: '🔍', description: 'Add citations' },
  { name: 'improve_structure', label: 'Improve Structure', icon: '🏗️', description: 'Reorganise sections' },
];

function setup(overrides = {}) {
  const props = {
    draft: mockDraft,
    qaChecks: mockQAChecks,
    rubricScores: { Clarity: 7.5, Depth: 6.0 },
    rerunStrategies: mockStrategies,
    heroImageUrl: '',
    onApprove: vi.fn(),
    onRegenerate: vi.fn(),
    ...overrides,
  };
  render(<FinalApproval {...props} />);
  return props;
}

describe('FinalApproval', () => {
  describe('QA display', () => {
    it('renders QA check items', () => {
      setup();
      expect(screen.getByText('Has title')).toBeInTheDocument();
      expect(screen.getByText('Has content')).toBeInTheDocument();
    });

    it('renders rubric score labels', () => {
      setup();
      expect(screen.getByText('Clarity')).toBeInTheDocument();
      expect(screen.getByText('Depth')).toBeInTheDocument();
    });
  });

  describe('Publish action', () => {
    it('calls onApprove when Publish Article clicked', async () => {
      const { onApprove } = setup();
      await userEvent.click(screen.getByRole('button', { name: /publish article/i }));
      expect(onApprove).toHaveBeenCalledOnce();
    });
  });

  describe('Clipboard copy', () => {
    beforeEach(() => {
      Object.assign(navigator, {
        clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
      });
    });

    it('calls clipboard.writeText with markdown on Copy MD click', async () => {
      setup();
      await userEvent.click(screen.getByRole('button', { name: /copy md/i }));
      expect(navigator.clipboard.writeText).toHaveBeenCalledOnce();
      const markdown = (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
      expect(markdown).toContain('# Test Article');
      expect(markdown).toContain('## Executive Summary');
      expect(markdown).toContain('## Section 1');
      expect(markdown).toContain('## Conclusion');
    });

    it('markdown includes YAML frontmatter when metadata present', async () => {
      setup();
      await userEvent.click(screen.getByRole('button', { name: /copy md/i }));
      const markdown = (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
      expect(markdown).toContain('slug: test-article');
    });

    it('shows Copied! text after clicking Copy MD', async () => {
      setup();
      await userEvent.click(screen.getByRole('button', { name: /copy md/i }));
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    });
  });

  describe('Markdown download', () => {
    it('triggers anchor click with correct filename on Download click', async () => {
      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:test');
      global.URL.revokeObjectURL = vi.fn();
      // Spy on HTMLAnchorElement.prototype.click to avoid jsdom navigation
      const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

      setup();
      await userEvent.click(screen.getByRole('button', { name: /download .md/i }));

      expect(global.URL.createObjectURL).toHaveBeenCalledOnce();
      expect(clickSpy).toHaveBeenCalledOnce();
      expect(global.URL.revokeObjectURL).toHaveBeenCalledOnce();

      clickSpy.mockRestore();
    });
  });

  describe('Regeneration', () => {
    it('Regenerate button is hidden when no strategy selected and no feedback', () => {
      setup();
      expect(screen.queryByRole('button', { name: /regenerate/i })).not.toBeInTheDocument();
    });

    it('Regenerate button appears after selecting a strategy', async () => {
      setup();
      await userEvent.click(screen.getByText('Strengthen Evidence'));
      expect(screen.getByRole('button', { name: /regenerate: strengthen evidence/i })).toBeInTheDocument();
    });

    it('Regenerate button appears when feedback is typed', async () => {
      setup();
      const textarea = screen.getByPlaceholderText(/additional direction/i);
      await userEvent.type(textarea, 'Focus on citations');
      expect(screen.getByRole('button', { name: /regenerate with feedback/i })).toBeInTheDocument();
    });

    it('calls onRegenerate with strategy and feedback', async () => {
      const { onRegenerate } = setup();
      await userEvent.click(screen.getByText('Strengthen Evidence'));
      const textarea = screen.getByPlaceholderText(/additional direction/i);
      await userEvent.type(textarea, 'Especially the TCO section');
      await userEvent.click(screen.getByRole('button', { name: /regenerate/i }));
      expect(onRegenerate).toHaveBeenCalledWith(mockStrategies[0], 'Especially the TCO section');
    });

    it('calls onRegenerate with null strategy when feedback-only', async () => {
      const { onRegenerate } = setup();
      const textarea = screen.getByPlaceholderText(/additional direction/i);
      await userEvent.type(textarea, 'Make it shorter');
      await userEvent.click(screen.getByRole('button', { name: /regenerate with feedback/i }));
      expect(onRegenerate).toHaveBeenCalledWith(null, 'Make it shorter');
    });

    it('deselects strategy on second click', async () => {
      setup();
      await userEvent.click(screen.getByText('Strengthen Evidence'));
      await userEvent.click(screen.getByText('Strengthen Evidence'));
      // No strategy selected, no feedback → Regenerate button gone
      expect(screen.queryByRole('button', { name: /regenerate/i })).not.toBeInTheDocument();
    });
  });
});
