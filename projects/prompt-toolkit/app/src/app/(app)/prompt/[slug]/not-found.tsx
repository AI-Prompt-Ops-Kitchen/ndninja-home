import Link from 'next/link';

export default function PromptNotFound() {
  return (
    <div className="max-w-md mx-auto text-center py-20">
      <h1 className="text-6xl font-bold text-gray-700 mb-4">404</h1>
      <h2 className="text-xl font-semibold text-white mb-2">Prompt Not Found</h2>
      <p className="text-gray-400 mb-8">
        This prompt may have been removed or the URL might be incorrect.
      </p>
      <Link
        href="/browse"
        className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
      >
        Browse Prompts
      </Link>
    </div>
  );
}
