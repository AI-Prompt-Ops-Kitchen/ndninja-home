'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { TypeRatio as TypeRatioData, COLORS } from '@/lib/chart-utils';
import { Card, CardContent } from '@/components/ui/card';

export function TypeRatio({ data }: { data: TypeRatioData[] }) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  if (total === 0) return null;

  return (
    <Card>
      <CardContent className="py-4">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Anxiety vs Sadness</h3>
        <div className="flex items-center gap-6">
          <ResponsiveContainer width={140} height={140}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={65}
                dataKey="value"
                strokeWidth={0}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: COLORS.tooltip, border: '1px solid #2a2a4a', borderRadius: 12, fontSize: 13 }}
              />
            </PieChart>
          </ResponsiveContainer>

          <div className="space-y-3">
            {data.map((d) => {
              const pct = total > 0 ? Math.round((d.value / total) * 100) : 0;
              return (
                <div key={d.name} className="flex items-center gap-3">
                  <div
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: d.color }}
                  />
                  <div>
                    <span className="text-sm text-gray-200">{d.name}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      {d.value} ({pct}%)
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
