-- Spike Mood Tracker — Run this in Supabase SQL Editor
-- Select all, copy, paste into SQL Editor, hit Run

create extension if not exists "uuid-ossp";

create type spike_type as enum ('anxiety', 'sadness');

create table profiles (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  doctor_email text,
  timezone text not null default 'America/New_York',
  daily_digest boolean not null default false,
  weekly_digest boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id)
);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = ''
as $$ begin insert into public.profiles (user_id) values (new.id); return new; end; $$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

create table spikes (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  type spike_type not null,
  intensity smallint not null check (intensity between 1 and 5),
  duration_seconds integer,
  notes text,
  logged_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index idx_spikes_user_logged on spikes (user_id, logged_at desc);
create index idx_spikes_type on spikes (user_id, type);

create table timer_sessions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  spike_id uuid references spikes(id) on delete set null,
  started_at timestamptz not null default now(),
  stopped_at timestamptz
);

create table email_log (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  report_type text not null check (report_type in ('daily', 'weekly')),
  report_date date not null,
  sent_at timestamptz not null default now(),
  resend_id text,
  unique (user_id, report_type, report_date)
);

alter table profiles enable row level security;
alter table spikes enable row level security;
alter table timer_sessions enable row level security;
alter table email_log enable row level security;

create policy "Users can view own profile" on profiles for select using (auth.uid() = user_id);
create policy "Users can update own profile" on profiles for update using (auth.uid() = user_id);
create policy "Users can view own spikes" on spikes for select using (auth.uid() = user_id);
create policy "Users can insert own spikes" on spikes for insert with check (auth.uid() = user_id);
create policy "Users can update own spikes" on spikes for update using (auth.uid() = user_id);
create policy "Users can delete own spikes" on spikes for delete using (auth.uid() = user_id);
create policy "Users can view own timer sessions" on timer_sessions for select using (auth.uid() = user_id);
create policy "Users can insert own timer sessions" on timer_sessions for insert with check (auth.uid() = user_id);
create policy "Users can update own timer sessions" on timer_sessions for update using (auth.uid() = user_id);
create policy "Users can view own email log" on email_log for select using (auth.uid() = user_id);

create or replace view spike_hourly_distribution as
select user_id, extract(hour from logged_at) as hour, type, count(*) as spike_count, round(avg(intensity), 1) as avg_intensity
from spikes group by user_id, extract(hour from logged_at), type;

create or replace view spike_day_of_week as
select user_id, extract(dow from logged_at) as day_of_week, extract(hour from logged_at) as hour, count(*) as spike_count
from spikes group by user_id, extract(dow from logged_at), extract(hour from logged_at);
