export default function PromptDetailLoading() {
  return (
    <div className="max-w-5xl mx-auto animate-pulse">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-8">
        <div className="space-y-6">
          {/* Back link */}
          <div className="h-4 bg-gray-800/40 rounded w-28" />

          {/* Header */}
          <div className="space-y-4">
            <div className="flex gap-2">
              <div className="h-6 bg-gray-800 rounded-full w-32" />
              <div className="h-6 bg-gray-800 rounded-full w-20" />
            </div>
            <div className="h-8 bg-gray-800 rounded w-2/3" />
            <div className="space-y-2">
              <div className="h-4 bg-gray-800/60 rounded w-full" />
              <div className="h-4 bg-gray-800/60 rounded w-4/5" />
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3">
            <div className="h-10 bg-gray-800 rounded-lg w-32" />
            <div className="h-10 bg-gray-800/60 rounded-lg w-24" />
            <div className="h-10 bg-gray-800/60 rounded-lg w-20" />
          </div>

          {/* Prompt content */}
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
            <div className="h-5 bg-gray-800 rounded w-32 mb-4" />
            <div className="space-y-2 bg-gray-950 rounded-lg p-4 border border-gray-800">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-4 bg-gray-800/40 rounded" style={{ width: `${70 + Math.random() * 30}%` }} />
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
            <div className="h-3 bg-gray-800/40 rounded w-20 mb-3" />
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-gray-800 rounded-full" />
              <div className="space-y-1.5">
                <div className="h-4 bg-gray-800 rounded w-24" />
                <div className="h-3 bg-gray-800/40 rounded w-16" />
              </div>
            </div>
          </div>
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4 space-y-3">
            <div className="h-3 bg-gray-800/40 rounded w-16" />
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex justify-between">
                <div className="h-4 bg-gray-800/40 rounded w-16" />
                <div className="h-4 bg-gray-800/40 rounded w-24" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
