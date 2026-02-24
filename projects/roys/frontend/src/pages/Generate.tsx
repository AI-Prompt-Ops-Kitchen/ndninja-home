import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import StandardSelector from '../components/StandardSelector';
import TierSelector from '../components/TierSelector';
import type { AssembledSOP, SOP } from '../types';

export default function Generate() {
  const [selectedStandards, setSelectedStandards] = useState<string[]>([]);
  const [selectedSOP, setSelectedSOP] = useState<string>('');
  const [tier, setTier] = useState<'standard' | 'enhanced'>('standard');
  const [result, setResult] = useState<AssembledSOP | null>(null);

  const standards = useQuery({ queryKey: ['standards'], queryFn: api.listStandards });
  const sops = useQuery({ queryKey: ['sops'], queryFn: api.listSOPs });

  const generate = useMutation({
    mutationFn: () =>
      api.generate({
        sop_id: selectedSOP,
        standard_ids: selectedStandards,
        content_tier: tier,
      }),
    onSuccess: setResult,
  });

  const downloadDocx = useMutation({
    mutationFn: () =>
      api.generateDocx({
        sop_id: selectedSOP,
        standard_ids: selectedStandards,
        content_tier: tier,
      }),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'sop.docx';
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  const toggleStandard = (id: string) => {
    setSelectedStandards((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  const canGenerate = selectedSOP && selectedStandards.length > 0;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <h2 className="text-2xl font-bold text-navy-900">Generate SOP</h2>

      {standards.data && (
        <StandardSelector
          standards={standards.data}
          selected={selectedStandards}
          onToggle={toggleStandard}
        />
      )}

      <div className="space-y-2">
        <label className="block text-sm font-medium text-navy-700">Select SOP</label>
        <select
          value={selectedSOP}
          onChange={(e) => setSelectedSOP(e.target.value)}
          className="w-full p-2 border border-navy-200 rounded-lg bg-white"
        >
          <option value="">Choose an SOP...</option>
          {sops.data?.map((sop: SOP) => (
            <option key={sop.id} value={sop.id}>
              {sop.code} — {sop.title}
            </option>
          ))}
        </select>
      </div>

      <TierSelector value={tier} onChange={setTier} />

      <div className="flex gap-3">
        <button
          onClick={() => generate.mutate()}
          disabled={!canGenerate || generate.isPending}
          className="px-6 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-light disabled:opacity-50 transition-colors"
        >
          {generate.isPending ? 'Generating...' : 'Generate JSON'}
        </button>
        <button
          onClick={() => downloadDocx.mutate()}
          disabled={!canGenerate || downloadDocx.isPending}
          className="px-6 py-2 border border-navy-300 text-navy-700 rounded-lg font-medium hover:bg-navy-100 disabled:opacity-50 transition-colors"
        >
          {downloadDocx.isPending ? 'Exporting...' : 'Export DOCX'}
        </button>
      </div>

      {generate.isError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {(generate.error as Error).message || 'Generation failed. Check that content blocks exist for this combination.'}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-navy-900">
            {result.sop_code} — {result.sop_title}
          </h3>
          <p className="text-sm text-navy-500">
            Combo: {result.combo_key} &middot; Tier: {result.content_tier}
          </p>
          {result.sections.map((s) => (
            <div key={s.section_number} className="p-4 bg-white rounded-lg border border-navy-200">
              <h4 className="font-medium text-navy-800">
                {s.section_number}. {s.section_title}
              </h4>
              <div className="mt-2 text-sm text-navy-700 whitespace-pre-wrap">{s.body}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
