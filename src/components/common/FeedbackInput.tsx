import { MessageSquare } from 'lucide-react';

interface Props {
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
}

export function FeedbackInput({
  placeholder = 'Describe what to improve (e.g., "Add more citations", "Strengthen the TCO section")…',
  value,
  onChange,
}: Props) {
  return (
    <div className="space-y-2">
      <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
        <MessageSquare className="w-4 h-4 text-indigo-400" />
        Feedback for regeneration
      </label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={3}
        className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none text-sm leading-relaxed"
      />
    </div>
  );
}
