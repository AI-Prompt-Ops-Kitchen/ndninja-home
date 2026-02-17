// Supabase Edge Function: send-digest
// Sends daily or weekly spike digest emails via Resend
// Triggered by pg_cron or manual invocation
//
// Environment variables required:
//   RESEND_API_KEY — Resend API key
//   SUPABASE_URL — auto-injected by Supabase
//   SUPABASE_SERVICE_ROLE_KEY — auto-injected by Supabase

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

interface Spike {
  type: "anxiety" | "sadness";
  intensity: number;
  logged_at: string;
  duration_seconds: number | null;
}

interface Profile {
  user_id: string;
  doctor_email: string;
  timezone: string;
  daily_digest: boolean;
  weekly_digest: boolean;
}

Deno.serve(async (req) => {
  try {
    const { report_type = "daily" } = await req.json().catch(() => ({ report_type: "daily" }));

    if (report_type !== "daily" && report_type !== "weekly") {
      return new Response(JSON.stringify({ error: "Invalid report_type" }), { status: 400 });
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // Get all profiles with the requested digest enabled and a doctor email set
    const digestField = report_type === "daily" ? "daily_digest" : "weekly_digest";
    const { data: profiles, error: profileErr } = await supabase
      .from("profiles")
      .select("user_id, doctor_email, timezone, daily_digest, weekly_digest")
      .eq(digestField, true)
      .not("doctor_email", "is", null);

    if (profileErr) throw profileErr;
    if (!profiles || profiles.length === 0) {
      return new Response(JSON.stringify({ message: "No profiles to send", sent: 0 }));
    }

    // Date range
    const now = new Date();
    const daysBack = report_type === "daily" ? 1 : 7;
    const since = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);

    let sent = 0;

    for (const profile of profiles as Profile[]) {
      // Check dedup
      const reportDate = now.toISOString().split("T")[0];
      const { data: existing } = await supabase
        .from("email_log")
        .select("id")
        .eq("user_id", profile.user_id)
        .eq("report_type", report_type)
        .eq("report_date", reportDate)
        .maybeSingle();

      if (existing) continue; // Already sent today

      // Fetch spikes
      const { data: spikes } = await supabase
        .from("spikes")
        .select("type, intensity, logged_at, duration_seconds")
        .eq("user_id", profile.user_id)
        .gte("logged_at", since.toISOString())
        .order("logged_at", { ascending: true });

      if (!spikes || spikes.length === 0) continue; // No data to report

      const html = buildEmailHtml(spikes as Spike[], report_type, profile.timezone);

      // Send via Resend
      const resendRes = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${RESEND_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: "Spike Tracker <noreply@spike.app>",
          to: [profile.doctor_email],
          subject: `${report_type === "daily" ? "Daily" : "Weekly"} Spike Report — ${reportDate}`,
          html,
        }),
      });

      const resendData = await resendRes.json();

      // Log the send
      await supabase.from("email_log").insert({
        user_id: profile.user_id,
        report_type,
        report_date: reportDate,
        resend_id: resendData.id || null,
      });

      sent++;
    }

    return new Response(JSON.stringify({ message: "Done", sent }));
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), { status: 500 });
  }
});

function buildEmailHtml(spikes: Spike[], reportType: string, timezone: string): string {
  const total = spikes.length;
  const anxietyCount = spikes.filter((s) => s.type === "anxiety").length;
  const sadnessCount = spikes.filter((s) => s.type === "sadness").length;
  const avgIntensity = (spikes.reduce((sum, s) => sum + s.intensity, 0) / total).toFixed(1);
  const maxIntensity = Math.max(...spikes.map((s) => s.intensity));

  // Peak hours
  const hourCounts = new Map<number, number>();
  for (const s of spikes) {
    const h = new Date(s.logged_at).getHours();
    hourCounts.set(h, (hourCounts.get(h) || 0) + 1);
  }
  const peakHour = [...hourCounts.entries()].sort((a, b) => b[1] - a[1])[0];
  const peakTimeStr = peakHour
    ? `${peakHour[0] % 12 || 12}${peakHour[0] < 12 ? "AM" : "PM"} (${peakHour[1]} spikes)`
    : "N/A";

  const period = reportType === "daily" ? "past 24 hours" : "past 7 days";

  const spikeRows = spikes
    .map((s) => {
      const time = new Date(s.logged_at).toLocaleString("en-US", {
        timeZone: timezone,
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
      const typeColor = s.type === "anxiety" ? "#8b5cf6" : "#0ea5e9";
      const typeLabel = s.type === "anxiety" ? "Anxiety" : "Sadness";
      const duration = s.duration_seconds ? `${Math.floor(s.duration_seconds / 60)}m ${s.duration_seconds % 60}s` : "—";

      return `
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #2a2a4a;color:#c0c0d8;font-size:13px">${time}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #2a2a4a"><span style="color:${typeColor};font-weight:600;font-size:13px">${typeLabel}</span></td>
          <td style="padding:8px 12px;border-bottom:1px solid #2a2a4a;text-align:center;color:#c0c0d8;font-size:13px;font-weight:700">${s.intensity}/5</td>
          <td style="padding:8px 12px;border-bottom:1px solid #2a2a4a;color:#8080a0;font-size:13px">${duration}</td>
        </tr>`;
    })
    .join("");

  return `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:#0f0f1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
  <div style="max-width:600px;margin:0 auto;padding:32px 20px">

    <div style="text-align:center;margin-bottom:32px">
      <div style="display:inline-block;width:48px;height:48px;border-radius:12px;background:linear-gradient(135deg,#7c3aed,#0ea5e9);line-height:48px;font-size:24px;color:white">⚡</div>
      <h1 style="color:#e0e0f0;font-size:20px;margin:12px 0 4px">${reportType === "daily" ? "Daily" : "Weekly"} Spike Report</h1>
      <p style="color:#8080a0;font-size:14px;margin:0">${period}</p>
    </div>

    <!-- Summary cards -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px">
      <tr>
        <td style="padding:4px">
          <div style="background:#16162a;border:1px solid #2a2a4a;border-radius:12px;padding:16px;text-align:center">
            <div style="color:#e0e0f0;font-size:28px;font-weight:700">${total}</div>
            <div style="color:#8080a0;font-size:11px;text-transform:uppercase;letter-spacing:1px">Total</div>
          </div>
        </td>
        <td style="padding:4px">
          <div style="background:#16162a;border:1px solid #2a2a4a;border-radius:12px;padding:16px;text-align:center">
            <div style="color:#e0e0f0;font-size:28px;font-weight:700">${avgIntensity}</div>
            <div style="color:#8080a0;font-size:11px;text-transform:uppercase;letter-spacing:1px">Avg Intensity</div>
          </div>
        </td>
        <td style="padding:4px">
          <div style="background:#16162a;border:1px solid #2a2a4a;border-radius:12px;padding:16px;text-align:center">
            <div style="color:#e0e0f0;font-size:28px;font-weight:700">${maxIntensity}</div>
            <div style="color:#8080a0;font-size:11px;text-transform:uppercase;letter-spacing:1px">Peak</div>
          </div>
        </td>
      </tr>
    </table>

    <!-- Type breakdown -->
    <div style="background:#16162a;border:1px solid #2a2a4a;border-radius:12px;padding:16px;margin-bottom:24px">
      <div style="display:flex;justify-content:space-around">
        <div style="text-align:center">
          <span style="color:#8b5cf6;font-size:24px;font-weight:700">${anxietyCount}</span>
          <div style="color:#8080a0;font-size:12px;margin-top:4px">Anxiety</div>
        </div>
        <div style="text-align:center">
          <span style="color:#0ea5e9;font-size:24px;font-weight:700">${sadnessCount}</span>
          <div style="color:#8080a0;font-size:12px;margin-top:4px">Sadness</div>
        </div>
        <div style="text-align:center">
          <span style="color:#c0c0d8;font-size:14px;font-weight:500">${peakTimeStr}</span>
          <div style="color:#8080a0;font-size:12px;margin-top:4px">Peak Time</div>
        </div>
      </div>
    </div>

    <!-- Individual entries -->
    <div style="background:#16162a;border:1px solid #2a2a4a;border-radius:12px;overflow:hidden;margin-bottom:24px">
      <table width="100%" cellpadding="0" cellspacing="0">
        <thead>
          <tr style="background:#1e1e38">
            <th style="padding:10px 12px;text-align:left;color:#8080a0;font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:500">Time</th>
            <th style="padding:10px 12px;text-align:left;color:#8080a0;font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:500">Type</th>
            <th style="padding:10px 12px;text-align:center;color:#8080a0;font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:500">Level</th>
            <th style="padding:10px 12px;text-align:left;color:#8080a0;font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:500">Duration</th>
          </tr>
        </thead>
        <tbody>${spikeRows}</tbody>
      </table>
    </div>

    <p style="color:#5a5a7a;font-size:12px;text-align:center;margin-top:32px">
      Generated by Spike Mood Tracker<br>
      This report is sent automatically based on patient preferences.
    </p>
  </div>
</body>
</html>`;
}
