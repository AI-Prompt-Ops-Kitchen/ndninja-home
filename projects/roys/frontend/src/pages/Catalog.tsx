import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import SOPCard from '../components/SOPCard';
import { formatComboKey } from '../lib/utils';

export default function Catalog() {
  const standards = useQuery({ queryKey: ['standards'], queryFn: api.listStandards });
  const sops = useQuery({ queryKey: ['sops'], queryFn: api.listSOPs });
  const combos = useQuery({ queryKey: ['combinations'], queryFn: api.listCombinations });

  return (
    <div className="space-y-10">
      <section>
        <h2 className="text-2xl font-bold text-navy-900 mb-4">Standards</h2>
        {standards.isLoading && <p className="text-navy-500">Loading...</p>}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {standards.data?.map((std) => (
            <div key={std.id} className="p-4 bg-white rounded-lg border border-navy-200">
              <h3 className="font-semibold text-navy-900">{std.name}</h3>
              <p className="text-xs text-navy-500 mt-1">{std.code} &middot; {std.category}</p>
              {std.description && (
                <p className="text-sm text-navy-600 mt-2 line-clamp-2">{std.description}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold text-navy-900 mb-4">Standard Combinations</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {combos.data?.map((c) => (
            <div key={c.id} className="p-4 bg-white rounded-lg border border-navy-200">
              <h3 className="font-semibold text-navy-900">{c.name}</h3>
              <p className="text-xs text-accent font-mono mt-1">{formatComboKey(c.combo_key)}</p>
              {c.description && (
                <p className="text-sm text-navy-600 mt-2">{c.description}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold text-navy-900 mb-4">SOPs</h2>
        {sops.isLoading && <p className="text-navy-500">Loading...</p>}
        {sops.data?.length === 0 && (
          <p className="text-navy-500">No SOPs imported yet. Content blocks will appear after Excel import.</p>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {sops.data?.map((sop) => <SOPCard key={sop.id} sop={sop} />)}
        </div>
      </section>
    </div>
  );
}
