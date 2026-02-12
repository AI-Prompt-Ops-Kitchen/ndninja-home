import { cn } from '@/lib/utils';

const categoryColors: Record<string, string> = {
  // Display names
  'Code & Development': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  'Writing & Content': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  'Business & Strategy': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  'Creative & Design': 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  'Education & Learning': 'bg-green-500/10 text-green-400 border-green-500/20',
  'AI & Meta-Prompting': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  'Marketing & Sales': 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  'Data & Analysis': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  'Research & Analysis': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  'Personal & Productivity': 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  // Raw enum values (from DB)
  code: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  writing: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  business: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  creative: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  education: 'bg-green-500/10 text-green-400 border-green-500/20',
  marketing: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  research: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  personal: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
};

const modelColors: Record<string, string> = {
  'GPT-4': 'bg-green-500/10 text-green-400 border-green-500/20',
  'GPT-4o': 'bg-green-500/10 text-green-400 border-green-500/20',
  'Claude': 'bg-orange-500/10 text-orange-300 border-orange-500/20',
  'Gemini': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  'Llama': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
};

interface TagBadgeProps {
  label: string;
  type?: 'category' | 'model' | 'difficulty' | 'custom';
  className?: string;
}

export function TagBadge({ label, type = 'custom', className }: TagBadgeProps) {
  const getColor = () => {
    if (type === 'category') return categoryColors[label] || 'bg-gray-800 text-gray-300 border-gray-700';
    if (type === 'model') return modelColors[label] || 'bg-gray-800 text-gray-300 border-gray-700';
    if (type === 'difficulty') {
      const map: Record<string, string> = {
        beginner: 'bg-green-500/10 text-green-400 border-green-500/20',
        intermediate: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
        advanced: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
        expert: 'bg-red-500/10 text-red-400 border-red-500/20',
      };
      return map[label.toLowerCase()] || 'bg-gray-800 text-gray-300 border-gray-700';
    }
    return 'bg-gray-800 text-gray-300 border-gray-700';
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border',
        getColor(),
        className
      )}
    >
      {label}
    </span>
  );
}
