// UI-facing types for prompt toolkit components
// These map from DB schema (enums, single fields) to component props

export interface PromptCardData {
  slug: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  models: string[];
  copies: number;
  favorites: number;
  rating: number;
  isPro?: boolean;
  author?: string;
}

export interface PromptVariable {
  name: string;
  label: string;
  description: string;
  placeholder: string;
  default_value: string | null;
  suggestions: string[] | null;
  required: boolean;
  variable_type: string;
}

export interface PromptDnaComponent {
  component_type: string;
  highlight_start: number;
  highlight_end: number;
  explanation: string;
  why_it_works: string | null;
  label?: string;
  color?: string;
}

export interface PromptDetailData {
  title: string;
  slug: string;
  description: string;
  content: string;
  system_prompt: string | null;
  example_output: string | null;
  use_case: string | null;
  variables: PromptVariable[];
  difficulty: string;
  category: string;
  ai_model_tags: string[];
  author: {
    display_name: string;
    avatar: string;
  };
  copy_count: number;
  favorite_count: number;
  rating_avg: number;
  rating_count: number;
  view_count: number;
  version: number;
  created_at: string;
  updated_at: string;
  dna: PromptDnaComponent[];
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}
