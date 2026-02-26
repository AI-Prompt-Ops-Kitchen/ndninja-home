import { useState, useEffect, useRef } from 'react';
import { useJobs } from './hooks/useJobs';
import { ScriptWorkshop } from './components/ScriptWorkshop';
import { ReviewQueue } from './components/ReviewQueue';
import { UploadZone } from './components/UploadZone';
import { ThumbnailStudio } from './components/ThumbnailStudio';
import { BrollLibraryPanel } from './components/BrollLibraryPanel';
import { JobsPanel } from './components/JobsPanel';
import { SummonsPanel } from './components/SummonsPanel';

const TERMINAL_STATUSES = new Set(['approved', 'discarded', 'uploaded']);

function App() {
  const { jobs, loading } = useJobs();
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const autoSelectedRef = useRef(false);

  // Auto-select the most recent active job on initial load
  useEffect(() => {
    if (autoSelectedRef.current || loading || jobs.length === 0 || currentJobId !== null) return;
    const active = jobs.find(j => !TERMINAL_STATUSES.has(j.status));
    if (active) {
      setCurrentJobId(active.id);
      autoSelectedRef.current = true;
    }
  }, [jobs, loading, currentJobId]);

  const activeCount = jobs.filter(
    j => !TERMINAL_STATUSES.has(j.status),
  ).length;

  const readyCount = jobs.filter(j => j.status === 'ready_for_review').length;
  const approvedCount = jobs.filter(j =>
    ['approved', 'uploading', 'uploaded'].includes(j.status)
    || (j.status === 'error' && j.youtube_title)
  ).length;
  const hasReviewContent = readyCount > 0 || approvedCount > 0;

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

      {/* Summons — visible when agents are active */}
      <section className="max-w-6xl mx-auto px-4 pt-4">
        <SummonsPanel />
      </section>

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
          {hasReviewContent && <ReviewQueue jobs={jobs} />}
          <JobsPanel jobs={jobs} loading={loading} currentJobId={currentJobId} onSelectJob={setCurrentJobId} />
        </div>
      </main>

      {/* B-Roll Library — full width below main grid */}
      <section className="max-w-6xl mx-auto px-4 pb-6">
        <BrollLibraryPanel />
      </section>
    </div>
  );
}

export default App;
