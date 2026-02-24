import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="text-center py-20">
      <h1 className="text-4xl font-bold text-navy-900 mb-4">
        Regulatory SOP Generation
      </h1>
      <p className="text-lg text-navy-600 max-w-2xl mx-auto mb-8">
        Generate compliant Standard Operating Procedures for ISO 13485, 21 CFR 820,
        EU MDR, and more. Multi-standard support with intelligent content assembly.
      </p>
      <div className="flex items-center justify-center gap-4">
        <Link
          to="/catalog"
          className="px-6 py-3 bg-primary text-white rounded-lg font-medium hover:bg-primary-light transition-colors"
        >
          Browse Catalog
        </Link>
        <Link
          to="/generate"
          className="px-6 py-3 border border-navy-300 text-navy-700 rounded-lg font-medium hover:bg-navy-100 transition-colors"
        >
          Generate SOP
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-4xl mx-auto">
        <div className="p-6 bg-white rounded-xl border border-navy-200">
          <h3 className="font-semibold text-navy-900 mb-2">Multi-Standard</h3>
          <p className="text-sm text-navy-600">
            Combine requirements from multiple regulatory standards into unified SOPs.
          </p>
        </div>
        <div className="p-6 bg-white rounded-xl border border-navy-200">
          <h3 className="font-semibold text-navy-900 mb-2">Traceability</h3>
          <p className="text-sm text-navy-600">
            Enhanced tier includes full traceability matrices linking requirements to SOP sections.
          </p>
        </div>
        <div className="p-6 bg-white rounded-xl border border-navy-200">
          <h3 className="font-semibold text-navy-900 mb-2">DOCX Export</h3>
          <p className="text-sm text-navy-600">
            Export assembled SOPs as professionally formatted Word documents.
          </p>
        </div>
      </div>
    </div>
  );
}
