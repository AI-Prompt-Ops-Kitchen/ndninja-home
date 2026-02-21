import { useState } from 'react';
import { useJobs } from './hooks/useJobs';
import { ScriptWorkshop } from './components/ScriptWorkshop';
import { ReviewQueue } from './components/ReviewQueue';
import { UploadZone } from './components/UploadZone';
import { ThumbnailStudio } from './components/ThumbnailStudio';
import { JobsPanel } from './components/JobsPanel';

function App() {
  const { jobs, loading } = useJobs();
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const activeCount = jobs.filter(
    j => !['approved', 'discarded'].includes(j.status),
  ).length;

  const readyCount = jobs.filter(j => j.status === 'ready_for_review').length;

  return (
    <div className="min-h-screen bg-[#0a0a12]">
      {/* Header */}
      <header className="border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">🥷</span>
          <div>
            <h1 className="text-base font-bold text-gray-100 leading-none">The Dojo</h1>
            <p className="text-xs text-gray-600 mt-0.5">Content Pipeline Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {readyCount > 0 && (
            <span className="flex items-center gap-1.5 text-xs text-green-400">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse-ready" />
              {readyCount} ready to review
            </span>
          )}
          {activeCount > 0 && (
            <span className="text-xs text-gray-600">{activeCount} active</span>
          )}
        </div>
      </header>

      {/* Main layout — 2 col on desktop, stacked on mobile */}
      <main className="max-w-6xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column */}
        <div className="flex flex-col gap-6">
          <ScriptWorkshop jobs={jobs} currentJobId={currentJobId} onCurrentJobChange={setCurrentJobId} />
          <ThumbnailStudio jobs={jobs} />
          <UploadZone />
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-6">
          <ReviewQueue jobs={jobs} />
          <JobsPanel jobs={jobs} loading={loading} currentJobId={currentJobId} onSelectJob={setCurrentJobId} />
        </div>
      </main>
    </div>
  );
}

export default App;
