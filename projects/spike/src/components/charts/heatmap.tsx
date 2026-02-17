'use client';

import { HeatmapCell, COLORS } from '@/lib/chart-utils';
import { Card, CardContent } from '@/components/ui/card';

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const HOUR_TICKS = [0, 3, 6, 9, 12, 15, 18, 21];
const HOUR_TICK_LABELS: Record<number, string> = {
  0: '12a', 3: '3a', 6: '6a', 9: '9a', 12: '12p', 15: '3p', 18: '6p', 21: '9p',
};

function cellColor(count: number, maxCount: number): string {
  if (count === 0) return 'rgba(255,255,255,0.03)';
  const intensity = Math.min(count / Math.max(maxCount, 1), 1);
  // Violet gradient
  const alpha = 0.15 + intensity * 0.65;
  return `rgba(139, 92, 246, ${alpha})`;
}

export function Heatmap({ data }: { data: HeatmapCell[] }) {
  const maxCount = Math.max(...data.map((c) => c.count), 1);
  const hasData = data.some((c) => c.count > 0);
  if (!hasData) return null;

  const cellSize = 14;
  const gap = 2;
  const labelW = 32;
  const labelH = 20;

  return (
    <Card>
      <CardContent className="py-4">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Day &times; Hour heatmap</h3>
        <div className="overflow-x-auto scrollbar-none">
          <svg
            width={labelW + 24 * (cellSize + gap)}
            height={labelH + 7 * (cellSize + gap) + 4}
            className="block"
          >
            {/* Hour labels */}
            {HOUR_TICKS.map((h) => (
              <text
                key={`h-${h}`}
                x={labelW + h * (cellSize + gap) + cellSize / 2}
                y={12}
                textAnchor="middle"
                fill={COLORS.label}
                fontSize={9}
              >
                {HOUR_TICK_LABELS[h]}
              </text>
            ))}

            {/* Day labels + cells */}
            {DAY_LABELS.map((dayLabel, day) => (
              <g key={dayLabel}>
                <text
                  x={0}
                  y={labelH + day * (cellSize + gap) + cellSize / 2 + 4}
                  fill={COLORS.label}
                  fontSize={10}
                >
                  {dayLabel}
                </text>
                {Array.from({ length: 24 }, (_, hour) => {
                  const cell = data.find((c) => c.day === day && c.hour === hour);
                  const count = cell?.count || 0;
                  return (
                    <rect
                      key={`${day}-${hour}`}
                      x={labelW + hour * (cellSize + gap)}
                      y={labelH + day * (cellSize + gap)}
                      width={cellSize}
                      height={cellSize}
                      rx={3}
                      fill={cellColor(count, maxCount)}
                    >
                      <title>
                        {dayLabel} {cell?.hourLabel}: {count} spike{count !== 1 ? 's' : ''}
                      </title>
                    </rect>
                  );
                })}
              </g>
            ))}
          </svg>
        </div>
      </CardContent>
    </Card>
  );
}
