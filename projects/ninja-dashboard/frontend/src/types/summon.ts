export type SummonStatus = 'active' | 'thinking' | 'done' | 'error';
export type SummonAnimal = 'toad' | 'snake' | 'slug' | 'scroll';

export interface Summon {
  summon_id: string;
  name: string;
  animal: SummonAnimal;
  color: string;
  specialty: string;
  status: SummonStatus;
  agent_type: string;
  session_id: string;
  summoned_at: number;
}
