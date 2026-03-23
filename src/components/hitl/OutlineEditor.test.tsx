import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { OutlineEditor } from './OutlineEditor';
import type { OutlineData } from '../../types/workflow';

const mockOutline: OutlineData = {
  sections: [
    { heading: 'Introduction', key_points: ['Point A', 'Point B'], estimated_words: 300 },
    { heading: 'Architecture Deep Dive', key_points: ['Point C'], estimated_words: 400 },
  ],
  comparison: { heading: 'Comparison', alternatives: ['Alt A', 'Alt B'] },
  anti_recommendation: { heading: 'When NOT to Use', focus: 'Small teams' },
  tco_analysis: { heading: 'TCO Analysis', cost_categories: ['Licensing', 'Infra'] },
};

function setup(overrides = {}) {
  const props = {
    outline: mockOutline,
    titleText: 'Test Article Title',
    onApprove: vi.fn(),
    onRegenerate: vi.fn(),
    ...overrides,
  };
  render(<OutlineEditor {...props} />);
  return props;
}

describe('OutlineEditor', () => {
  it('renders section headings', () => {
    setup();
    expect(screen.getByDisplayValue('Introduction')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Architecture Deep Dive')).toBeInTheDocument();
  });

  it('renders key points', () => {
    setup();
    expect(screen.getByDisplayValue('Point A')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Point C')).toBeInTheDocument();
  });

  it('calls onApprove with current outline on approve click', async () => {
    const { onApprove } = setup();
    await userEvent.click(screen.getByRole('button', { name: /approve outline/i }));
    expect(onApprove).toHaveBeenCalledOnce();
    const calledWith = onApprove.mock.calls[0][0] as OutlineData;
    expect(calledWith.sections[0].heading).toBe('Introduction');
  });

  it('reflects heading edits in onApprove call', async () => {
    const { onApprove } = setup();
    const headingInput = screen.getByDisplayValue('Introduction');
    await userEvent.clear(headingInput);
    await userEvent.type(headingInput, 'Updated Introduction');
    await userEvent.click(screen.getByRole('button', { name: /approve outline/i }));
    const calledWith = onApprove.mock.calls[0][0] as OutlineData;
    expect(calledWith.sections[0].heading).toBe('Updated Introduction');
  });

  it('reflects key point edits in onApprove call', async () => {
    const { onApprove } = setup();
    const pointInput = screen.getByDisplayValue('Point A');
    await userEvent.clear(pointInput);
    await userEvent.type(pointInput, 'Updated Point A');
    await userEvent.click(screen.getByRole('button', { name: /approve outline/i }));
    const calledWith = onApprove.mock.calls[0][0] as OutlineData;
    expect(calledWith.sections[0].key_points[0]).toBe('Updated Point A');
  });

  it('calls onRegenerate with empty feedback when none entered', async () => {
    const { onRegenerate } = setup();
    await userEvent.click(screen.getByRole('button', { name: /regenerate outline/i }));
    expect(onRegenerate).toHaveBeenCalledWith('');
  });

  it('calls onRegenerate with feedback text', async () => {
    const { onRegenerate } = setup();
    // Use placeholder text to target the FeedbackInput textarea specifically,
    // since section headings and key points are also textbox-role inputs.
    const textarea = screen.getByPlaceholderText(/direction for regeneration/i);
    await userEvent.type(textarea, 'Add a migration section');
    await userEvent.click(screen.getByRole('button', { name: /regenerate outline/i }));
    expect(onRegenerate).toHaveBeenCalledWith('Add a migration section');
  });
});
