'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { DailyCount, COLORS, formatShortDate } from '@/lib/chart-utils';
import { Card, CardContent } from '@/components/ui/card';

export function SpikesPerDay({ data }: { data: DailyCount[] }) {
  if (data.length === 0) return null;

  return (
    <Card>
      <CardContent className="py-4">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Spikes per day</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} barGap={2}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatShortDate}
              tick={{ fill: COLORS.label, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: COLORS.label, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={24}
            />
            <Tooltip
              contentStyle={{ background: COLORS.tooltip, border: '1px solid #2a2a4a', borderRadius: 12, fontSize: 13 }}
              labelFormatter={formatShortDate}
            />
            <Bar dataKey="anxiety" stackId="a" fill={COLORS.anxiety} radius={[0, 0, 0, 0]} name="Anxiety" />
            <Bar dataKey="sadness" stackId="a" fill={COLORS.sadness} radius={[4, 4, 0, 0]} name="Sadness" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
