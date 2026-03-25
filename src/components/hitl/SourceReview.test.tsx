import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { SourceReview } from './SourceReview';
import type { SourceItem } from '../../types/workflow';

const mockSources: SourceItem[] = [
  {
    id: 1,
    title: 'eBPF: The Future of Networking',
    url: 'https://example.com/ebpf-networking',
    publisher: 'ACM',
    date: '2024-01',
    tier: 'Tier 1',
    snippet: 'eBPF enables safe kernel-level programming.',
    key_data_point: '60% reduction in latency',
    grounded: true,
  },
  {
    id: 2,
    title: 'Observability with eBPF',
    url: 'https://example.com/ebpf-obs',
    publisher: 'InfoQ',
    date: '2024-03',
    tier: 'Tier 2',
    snippet: 'Zero-instrumentation tracing using eBPF probes.',
    key_data_point: '',
    grounded: false,
  },
  {
    id: 3,
    title: 'eBPF Security Patterns',
    url: 'https://example.com/ebpf-security',
    publisher: 'USENIX',
    date: '2023-11',
    tier: 'Tier 3',
    snippet: 'Runtime security enforcement with eBPF.',
    key_data_point: 'Used by 40% of cloud-native deployments',
    grounded: false,
  },
];

function setup(overrides = {}) {
  const props = {
    sources: mockSources,
    titleText: 'eBPF in Production: A Practical Guide',
    onApprove: vi.fn(),
    onRegenerate: vi.fn(),
    ...overrides,
  };
  render(<SourceReview {...props} />);
  return props;
}

describe('SourceReview', () => {
  it('renders all source titles', () => {
    setup();
    expect(screen.getByText('eBPF: The Future of Networking')).toBeInTheDocument();
    expect(screen.getByText('Observability with eBPF')).toBeInTheDocument();
    expect(screen.getByText('eBPF Security Patterns')).toBeInTheDocument();
  });

  it('all sources are checked by default', () => {
    setup();
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(3);
    checkboxes.forEach((cb) => expect(cb).toBeChecked());
  });

  it('shows correct selected count', () => {
    setup();
    expect(screen.getByText('3 / 3 sources selected as primary')).toBeInTheDocument();
  });

  it('shows GROUNDED badge only for grounded sources', () => {
    setup();
    const groundedBadges = screen.getAllByText(/grounded/i);
    expect(groundedBadges).toHaveLength(1);
  });

  it('shows key_data_point when present', () => {
    setup();
    expect(screen.getByText('📊 60% reduction in latency')).toBeInTheDocument();
    expect(screen.getByText('📊 Used by 40% of cloud-native deployments')).toBeInTheDocument();
  });

  it('unchecking a source updates the count', async () => {
    setup();
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[0]);
    expect(screen.getByText('2 / 3 sources selected as primary')).toBeInTheDocument();
  });

  it('toggling source off then on restores check state', async () => {
    setup();
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[1]);
    expect(checkboxes[1]).not.toBeChecked();
    await userEvent.click(checkboxes[1]);
    expect(checkboxes[1]).toBeChecked();
  });

  it('Confirm Sources button is disabled when all sources are deselected', async () => {
    setup();
    const checkboxes = screen.getAllByRole('checkbox');
    for (const cb of checkboxes) {
      await userEvent.click(cb);
    }
    expect(screen.getByRole('button', { name: /confirm sources/i })).toBeDisabled();
  });

  it('calls onApprove with only checked sources on Confirm click', async () => {
    const { onApprove } = setup();
    const checkboxes = screen.getAllByRole('checkbox');
    await userEvent.click(checkboxes[0]); // uncheck source id=1
    await userEvent.click(screen.getByRole('button', { name: /confirm sources/i }));
    expect(onApprove).toHaveBeenCalledOnce();
    const called = onApprove.mock.calls[0][0] as SourceItem[];
    expect(called.map((s) => s.id)).toEqual([2, 3]);
  });

  it('calls onRegenerate when Re-research is clicked', async () => {
    const { onRegenerate } = setup();
    await userEvent.click(screen.getByRole('button', { name: /re-research/i }));
    expect(onRegenerate).toHaveBeenCalledOnce();
  });

  it('checkboxes are disabled when disabled prop is true', async () => {
    const { onApprove } = setup({ disabled: true });
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach((cb) => expect(cb).toBeDisabled());
    expect(screen.getByRole('button', { name: /re-research/i })).toBeDisabled();
    await userEvent.click(screen.getByRole('button', { name: /confirm sources/i }));
    expect(onApprove).not.toHaveBeenCalled();
  });

  it('renders tier badge for each source', () => {
    setup();
    expect(screen.getByText('Tier 1')).toBeInTheDocument();
    expect(screen.getByText('Tier 2')).toBeInTheDocument();
    expect(screen.getByText('Tier 3')).toBeInTheDocument();
  });

  it('renders publisher and truncated URL', () => {
    setup();
    expect(screen.getByText(/ACM/)).toBeInTheDocument();
    const links = screen.getAllByRole('link');
    expect(links.length).toBeGreaterThanOrEqual(1);
  });
});
