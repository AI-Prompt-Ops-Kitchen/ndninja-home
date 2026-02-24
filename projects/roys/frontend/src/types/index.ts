export interface Standard {
  id: string;
  code: string;
  name: string;
  description: string | null;
  version: string | null;
  category: string;
  is_active: boolean;
}

export interface Requirement {
  id: string;
  standard_id: string;
  clause_number: string;
  title: string;
  description: string | null;
  is_critical: boolean;
}

export interface StandardDetail extends Standard {
  requirements: Requirement[];
}

export interface StandardCombination {
  id: string;
  combo_key: string;
  name: string;
  description: string | null;
  standard_codes: string[];
  is_active: boolean;
}

export interface SOP {
  id: string;
  code: string;
  title: string;
  description: string | null;
  category: string | null;
  is_active: boolean;
}

export interface ContentBlock {
  id: string;
  section_number: string;
  section_title: string;
  content_tier: string;
  combo_key: string;
  body: string;
  sort_order: number;
  block_metadata: Record<string, unknown> | null;
}

export interface SOPDetail extends SOP {
  content_blocks: ContentBlock[];
}

export interface AssemblyRequest {
  sop_id: string;
  standard_ids: string[];
  content_tier: 'standard' | 'enhanced';
  template_structure_id?: string;
}

export interface AssembledSection {
  section_number: string;
  section_title: string;
  body: string;
  block_metadata: Record<string, unknown> | null;
}

export interface TraceabilityEntry {
  requirement_clause: string;
  requirement_title: string;
  standard_code: string;
  section_number: string;
  coverage_notes: string | null;
}

export interface AssembledSOP {
  sop_id: string;
  sop_code: string;
  sop_title: string;
  combo_key: string;
  content_tier: string;
  template_name: string | null;
  sections: AssembledSection[];
  traceability: TraceabilityEntry[] | null;
  cross_references: Record<string, unknown>[] | null;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  company: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}
