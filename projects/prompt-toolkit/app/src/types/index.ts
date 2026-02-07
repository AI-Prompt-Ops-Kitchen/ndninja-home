// ============================================================
// Prompt Toolkit — Core Types
// ============================================================

export type UserRole = 'free' | 'pro' | 'admin';
export type Difficulty = 'beginner' | 'intermediate' | 'advanced' | 'expert';
export type PromptStatus = 'draft' | 'published' | 'archived' | 'pending_review';

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  role: UserRole;
  subscription_status: string;
  created_at: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  parent_id: string | null;
  sort_order: number;
}

export interface Tag {
  id: string;
  name: string;
  slug: string;
  color: string | null;
}

export interface PromptVariable {
  name: string;
  description: string;
  default?: string;
}

export interface Prompt {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  content: string;
  system_prompt: string | null;
  example_output: string | null;
  use_case: string | null;
  variables: PromptVariable[];
  difficulty: Difficulty;
  ai_model_tags: string[];
  category_id: string | null;
  author_id: string | null;
  status: PromptStatus;
  is_public: boolean;
  is_featured: boolean;
  is_pro_only: boolean;
  version: number;
  fork_of: string | null;
  copy_count: number;
  favorite_count: number;
  rating_avg: number;
  rating_count: number;
  view_count: number;
  created_at: string;
  updated_at: string;
  // Joined data
  category?: Category;
  author?: User;
  tags?: Tag[];
}

export interface Favorite {
  user_id: string;
  prompt_id: string;
  folder: string;
  note: string | null;
  created_at: string;
}

export interface Rating {
  user_id: string;
  prompt_id: string;
  score: number;
  review: string | null;
  created_at: string;
}

export interface UsageLog {
  id: string;
  user_id: string | null;
  prompt_id: string | null;
  action: string;
  metadata: Record<string, unknown>;
  created_at: string;
}
