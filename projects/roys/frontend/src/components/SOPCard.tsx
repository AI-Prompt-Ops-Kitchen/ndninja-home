import type { SOP } from '../types';

interface Props {
  sop: SOP;
  onSelect?: (sop: SOP) => void;
}

export default function SOPCard({ sop, onSelect }: Props) {
  return (
    <div
      onClick={() => onSelect?.(sop)}
      className="p-4 bg-white rounded-lg border border-navy-200 hover:border-accent hover:shadow-md transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-navy-900">{sop.title}</h3>
          <p className="text-sm text-navy-500 mt-1">{sop.code}</p>
        </div>
        {sop.category && (
          <span className="text-xs px-2 py-1 bg-navy-100 text-navy-600 rounded-full">
            {sop.category}
          </span>
        )}
      </div>
      {sop.description && (
        <p className="text-sm text-navy-600 mt-2 line-clamp-2">{sop.description}</p>
      )}
    </div>
  );
}
