import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

export default function Admin() {
  const stats = useQuery({ queryKey: ['admin-stats'], queryFn: api.adminStats, retry: false });

  if (stats.isError) {
    return (
      <div className="text-center py-16">
        <h2 className="text-2xl font-bold text-navy-900 mb-2">Admin Panel</h2>
        <p className="text-navy-500">Sign in with an admin account to view statistics.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-navy-900">Admin Dashboard</h2>
      {stats.isLoading && <p className="text-navy-500">Loading...</p>}
      {stats.data && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {Object.entries(stats.data).map(([key, value]) => (
            <div key={key} className="p-4 bg-white rounded-lg border border-navy-200 text-center">
              <div className="text-2xl font-bold text-primary">{value}</div>
              <div className="text-sm text-navy-500 mt-1 capitalize">{key.replace(/_/g, ' ')}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
