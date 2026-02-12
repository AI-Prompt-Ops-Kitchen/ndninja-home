export default function BrowseLoading() {
  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div>
        <div className="h-7 bg-gray-800 rounded w-48" />
        <div className="h-4 bg-gray-800/60 rounded w-72 mt-2" />
      </div>

      {/* Search bar skeleton */}
      <div className="h-11 bg-gray-800/50 rounded-xl border border-gray-800" />

      {/* Category tabs skeleton */}
      <div className="flex gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-8 bg-gray-800/50 rounded-full w-20" />
        ))}
      </div>

      {/* Results count skeleton */}
      <div className="flex items-center justify-between">
        <div className="h-4 bg-gray-800/40 rounded w-32" />
        <div className="h-8 bg-gray-800/40 rounded w-36" />
      </div>

      {/* Grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-3">
            <div className="flex gap-2">
              <div className="h-5 bg-gray-800 rounded-full w-24" />
              <div className="h-5 bg-gray-800 rounded-full w-16" />
            </div>
            <div className="h-5 bg-gray-800 rounded w-3/4" />
            <div className="space-y-2">
              <div className="h-3 bg-gray-800/60 rounded w-full" />
              <div className="h-3 bg-gray-800/60 rounded w-5/6" />
            </div>
            <div className="flex gap-1.5">
              <div className="h-5 bg-gray-800/40 rounded-full w-14" />
              <div className="h-5 bg-gray-800/40 rounded-full w-14" />
            </div>
            <div className="flex items-center gap-4 pt-3 border-t border-gray-800/80">
              <div className="h-3 bg-gray-800/40 rounded w-12" />
              <div className="h-3 bg-gray-800/40 rounded w-8" />
              <div className="h-3 bg-gray-800/40 rounded w-10 ml-auto" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
