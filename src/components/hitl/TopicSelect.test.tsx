import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { TopicSelect } from './TopicSelect';
import type { TopicItem } from '../../types/workflow';

const mockTopics: TopicItem[] = [
  { title: 'eBPF Observability', description: 'Deep kernel visibility', trend_signal: 'Growing fast' },
  { title: 'Wasm on the Edge', description: 'WebAssembly runtimes', trend_signal: 'Emerging' },
];

function setup(overrides = {}) {
  const props = {
    topics: mockTopics,
    category: 'AI Infrastructure',
    onApprove: vi.fn(),
    onRegenerate: vi.fn(),
    ...overrides,
  };
  render(<TopicSelect {...props} />);
  return props;
}

describe('TopicSelect', () => {
  it('renders all topic titles', () => {
    setup();
    expect(screen.getByText('eBPF Observability')).toBeInTheDocument();
    expect(screen.getByText('Wasm on the Edge')).toBeInTheDocument();
  });

  it('Confirm button is disabled before topic selection', () => {
    setup();
    const confirmBtn = screen.getByRole('button', { name: /confirm topic/i });
    expect(confirmBtn).toBeDisabled();
  });

  it('clicking a topic enables Confirm button', async () => {
    setup();
    await userEvent.click(screen.getByText('eBPF Observability'));
    const confirmBtn = screen.getByRole('button', { name: /confirm topic/i });
    expect(confirmBtn).not.toBeDisabled();
  });

  it('calls onApprove with selected topic on Confirm click', async () => {
    const { onApprove } = setup();
    await userEvent.click(screen.getByText('eBPF Observability'));
    await userEvent.click(screen.getByRole('button', { name: /confirm topic/i }));
    expect(onApprove).toHaveBeenCalledOnce();
    expect(onApprove).toHaveBeenCalledWith(mockTopics[0]);
  });

  it('clicking already-selected topic does not change Confirm disabled state', async () => {
    setup();
    await userEvent.click(screen.getByText('eBPF Observability'));
    await userEvent.click(screen.getByText('Wasm on the Edge'));
    const confirmBtn = screen.getByRole('button', { name: /confirm topic/i });
    expect(confirmBtn).not.toBeDisabled();
  });

  it('calls onRegenerate with empty string when no feedback entered', async () => {
    const { onRegenerate } = setup();
    await userEvent.click(screen.getByRole('button', { name: /regenerate/i }));
    expect(onRegenerate).toHaveBeenCalledWith('');
  });

  it('calls onRegenerate with feedback text when provided', async () => {
    const { onRegenerate } = setup();
    const textarea = screen.getByRole('textbox');
    await userEvent.type(textarea, 'Focus on enterprise cases');
    await userEvent.click(screen.getByRole('button', { name: /regenerate/i }));
    expect(onRegenerate).toHaveBeenCalledWith('Focus on enterprise cases');
  });

  it('does nothing on Confirm click when disabled', async () => {
    const { onApprove } = setup({ disabled: true });
    const confirmBtn = screen.getByRole('button', { name: /confirm topic/i });
    expect(confirmBtn).toBeDisabled();
    await userEvent.click(confirmBtn);
    expect(onApprove).not.toHaveBeenCalled();
  });
});
