-- Enable pg_cron extension (requires superuser — run in Supabase dashboard SQL editor)
-- On Supabase hosted, pg_cron is available on Pro plan and above.
-- For local dev, the Edge Function can be triggered manually or via a cron job.

-- Enable pg_net for HTTP calls from within Postgres
create extension if not exists pg_net with schema extensions;

-- Daily digest cron — every day at 8 AM UTC
-- Adjust the schedule or add timezone logic in the Edge Function
select cron.schedule(
  'daily-spike-digest',
  '0 8 * * *', -- 8:00 AM UTC daily
  $$
  select net.http_post(
    url := current_setting('app.settings.supabase_url') || '/functions/v1/send-digest',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
    ),
    body := '{"report_type": "daily"}'::jsonb
  );
  $$
);

-- Weekly digest cron — every Sunday at 9 AM UTC
select cron.schedule(
  'weekly-spike-digest',
  '0 9 * * 0', -- 9:00 AM UTC every Sunday
  $$
  select net.http_post(
    url := current_setting('app.settings.supabase_url') || '/functions/v1/send-digest',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
    ),
    body := '{"report_type": "weekly"}'::jsonb
  );
  $$
);
