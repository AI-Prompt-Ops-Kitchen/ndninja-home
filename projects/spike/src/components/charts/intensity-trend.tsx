'use client';

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { IntensityPoint, COLORS, formatShortDate } from '@/lib/chart-utils';
import { Card, CardContent } from '@/components/ui/card';

export function IntensityTrend({ data }: { data: IntensityPoint[] }) {
  if (data.length === 0) return null;

  // Split into two series for color coding
  const withAnxiety = data.map((d) => ({
    ...d,
    anxietyIntensity: d.type === 'anxiety' ? d.intensity : null,
    sadnessIntensity: d.type === 'sadness' ? d.intensity : null,
  }));

  return (
    <Card>
      <CardContent className="py-4">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Intensity over time</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={withAnxiety}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatShortDate}
              tick={{ fill: COLORS.label, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[1, 5]}
              ticks={[1, 2, 3, 4, 5]}
              tick={{ fill: COLORS.label, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={24}
            />
            <Tooltip
              contentStyle={{ background: COLORS.tooltip, border: '1px solid #2a2a4a', borderRadius: 12, fontSize: 13 }}
              labelFormatter={formatShortDate}
            />
            <Line
              type="monotone"
              dataKey="anxietyIntensity"
              stroke={COLORS.anxiety}
              strokeWidth={2}
              dot={{ r: 4, fill: COLORS.anxiety }}
              connectNulls={false}
              name="Anxiety"
            />
            <Line
              type="monotone"
              dataKey="sadnessIntensity"
              stroke={COLORS.sadness}
              strokeWidth={2}
              dot={{ r: 4, fill: COLORS.sadness }}
              connectNulls={false}
              name="Sadness"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
