import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { TitleSelect } from './TitleSelect';
import type { TitleItem } from '../../types/workflow';

const mockTitles: TitleItem[] = [
  {
    title: 'eBPF in Production: A Practical Guide',
    angle: 'Engineering deep-dive',
    primary_keyword: 'eBPF production',
    seo_rationale: 'High intent keyword with growing search volume',
  },
  {
    title: 'Why eBPF Is Rewriting Observability',
    angle: 'Thought leadership',
    primary_keyword: 'eBPF observability',
    seo_rationale: 'Broad awareness keyword for top-of-funnel',
  },
];

function setup(overrides = {}) {
  const props = {
    titles: mockTitles,
    topicName: 'eBPF Observability',
    onApprove: vi.fn(),
    onRegenerate: vi.fn(),
    ...overrides,
  };
  render(<TitleSelect {...props} />);
  return props;
}

describe('TitleSelect', () => {
  it('renders all title options', () => {
    setup();
    expect(screen.getByText('eBPF in Production: A Practical Guide')).toBeInTheDocument();
    expect(screen.getByText('Why eBPF Is Rewriting Observability')).toBeInTheDocument();
  });

  it('renders angle, keyword, and seo_rationale for each title', () => {
    setup();
    expect(screen.getByText('Engineering deep-dive')).toBeInTheDocument();
    expect(screen.getByText('eBPF production')).toBeInTheDocument();
    expect(screen.getByText('High intent keyword with growing search volume')).toBeInTheDocument();
  });

  it('Confirm Title button is disabled before selection', () => {
    setup();
    expect(screen.getByRole('button', { name: /confirm title/i })).toBeDisabled();
  });

  it('clicking a title enables Confirm Title button', async () => {
    setup();
    await userEvent.click(screen.getByText('eBPF in Production: A Practical Guide'));
    expect(screen.getByRole('button', { name: /confirm title/i })).not.toBeDisabled();
  });

  it('calls onApprove with the selected title on Confirm click', async () => {
    const { onApprove } = setup();
    await userEvent.click(screen.getByText('eBPF in Production: A Practical Guide'));
    await userEvent.click(screen.getByRole('button', { name: /confirm title/i }));
    expect(onApprove).toHaveBeenCalledOnce();
    expect(onApprove).toHaveBeenCalledWith(mockTitles[0]);
  });

  it('switching selection updates which title is passed to onApprove', async () => {
    const { onApprove } = setup();
    await userEvent.click(screen.getByText('eBPF in Production: A Practical Guide'));
    await userEvent.click(screen.getByText('Why eBPF Is Rewriting Observability'));
    await userEvent.click(screen.getByRole('button', { name: /confirm title/i }));
    expect(onApprove).toHaveBeenCalledWith(mockTitles[1]);
  });

  it('calls onRegenerate with empty string when no feedback entered', async () => {
    const { onRegenerate } = setup();
    await userEvent.click(screen.getByRole('button', { name: /regenerate/i }));
    expect(onRegenerate).toHaveBeenCalledWith('');
  });

  it('calls onRegenerate with feedback text when provided', async () => {
    const { onRegenerate } = setup();
    await userEvent.type(screen.getByRole('textbox'), 'More technical angle');
    await userEvent.click(screen.getByRole('button', { name: /regenerate/i }));
    expect(onRegenerate).toHaveBeenCalledWith('More technical angle');
  });

  it('all buttons are disabled when disabled prop is true', async () => {
    const { onApprove, onRegenerate } = setup({ disabled: true });
    expect(screen.getByRole('button', { name: /confirm title/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /regenerate/i })).toBeDisabled();
    await userEvent.click(screen.getByRole('button', { name: /regenerate/i }));
    expect(onRegenerate).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: /confirm title/i }));
    expect(onApprove).not.toHaveBeenCalled();
  });
});
