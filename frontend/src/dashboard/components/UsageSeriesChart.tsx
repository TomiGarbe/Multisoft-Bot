import { useMemo, useRef, useState } from 'react';
import type { DashboardSeriesPoint } from '@/dashboard/types';

interface UsageSeriesChartProps {
  data: DashboardSeriesPoint[];
}

const VIEW_WIDTH = 720;
const VIEW_HEIGHT = 280;
const PADDING = { top: 24, right: 20, bottom: 44, left: 56 };

export default function UsageSeriesChart({ data }: UsageSeriesChartProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const plotWidth = VIEW_WIDTH - PADDING.left - PADDING.right;
  const plotHeight = VIEW_HEIGHT - PADDING.top - PADDING.bottom;

  const { points, maxTokens, totalTokens, avgTokens, peakIndex } = useMemo(() => {
    if (data.length === 0) {
      return { points: [] as Array<{ x: number; y: number } & DashboardSeriesPoint>, maxTokens: 0, totalTokens: 0, avgTokens: 0, peakIndex: -1 };
    }
    const max = Math.max(...data.map((item) => item.tokens), 1);
    const total = data.reduce((acc, item) => acc + item.tokens, 0);
    const avg = total / data.length;
    let peak = 0;
    data.forEach((item, idx) => {
      if (item.tokens > data[peak].tokens) peak = idx;
    });
    const mapped = data.map((item, index) => {
      const x = PADDING.left + (index / Math.max(data.length - 1, 1)) * plotWidth;
      const y = PADDING.top + (1 - item.tokens / max) * plotHeight;
      return { x, y, ...item };
    });
    return { points: mapped, maxTokens: max, totalTokens: total, avgTokens: avg, peakIndex: peak };
  }, [data, plotWidth, plotHeight]);

  if (data.length === 0) {
    return <p className="text-sm text-slate-500">Sin datos en el periodo seleccionado.</p>;
  }

  const ticks = 4;
  const linePath = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${PADDING.top + plotHeight} L ${points[0].x} ${PADDING.top + plotHeight} Z`;

  const avgY = PADDING.top + (1 - avgTokens / maxTokens) * plotHeight;

  const handleMove = (event: React.PointerEvent<SVGSVGElement>) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const xRatio = (event.clientX - rect.left) / rect.width;
    const xCoord = xRatio * VIEW_WIDTH;
    if (xCoord < PADDING.left || xCoord > PADDING.left + plotWidth) {
      setHoverIndex(null);
      return;
    }
    const t = (xCoord - PADDING.left) / plotWidth;
    const idx = Math.min(points.length - 1, Math.max(0, Math.round(t * (points.length - 1))));
    setHoverIndex(idx);
  };

  const handleLeave = () => setHoverIndex(null);

  const activePoint = hoverIndex !== null ? points[hoverIndex] : null;

  const tooltipWidth = 144;
  const tooltipHeight = 56;
  const tooltipX = activePoint
    ? Math.min(Math.max(activePoint.x - tooltipWidth / 2, PADDING.left), PADDING.left + plotWidth - tooltipWidth)
    : 0;
  const tooltipY = activePoint ? Math.max(activePoint.y - tooltipHeight - 14, 4) : 0;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-sky-500" />
          <span className="font-medium text-slate-600">Tokens / dia</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="block h-0.5 w-3 rounded bg-emerald-400" />
          <span className="text-slate-500">Promedio: <span className="font-semibold text-slate-700">{Math.round(avgTokens).toLocaleString('es-AR')}</span></span>
        </div>
        <div className="flex items-center gap-2 text-slate-500">
          Total: <span className="font-semibold text-slate-700">{totalTokens.toLocaleString('es-AR')}</span>
        </div>
        <div className="flex items-center gap-2 text-slate-500">
          Pico: <span className="font-semibold text-slate-700">{data[peakIndex]?.tokens.toLocaleString('es-AR') ?? '0'}</span>
          <span className="text-slate-400">({data[peakIndex]?.label})</span>
        </div>
      </div>

      <div className="relative overflow-x-auto">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
          className="h-[280px] min-w-[620px] w-full touch-none"
          role="img"
          aria-label="Consumo por dia"
          onPointerMove={handleMove}
          onPointerLeave={handleLeave}
          onPointerDown={handleMove}
        >
          <defs>
            <linearGradient id="usage-area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.32" />
              <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0.02" />
            </linearGradient>
            <linearGradient id="usage-line" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#0284c7" />
              <stop offset="100%" stopColor="#0ea5e9" />
            </linearGradient>
            <filter id="usage-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {Array.from({ length: ticks + 1 }).map((_, index) => {
            const value = (maxTokens / ticks) * (ticks - index);
            const y = PADDING.top + (index / ticks) * plotHeight;
            return (
              <g key={`tick-${index}`}>
                <line
                  x1={PADDING.left}
                  x2={PADDING.left + plotWidth}
                  y1={y}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeDasharray="3 3"
                />
                <text x={PADDING.left - 10} y={y + 4} textAnchor="end" fontSize="10" fill="#64748b">
                  {Math.round(value).toLocaleString('es-AR')}
                </text>
              </g>
            );
          })}

          {/* Avg reference line */}
          <line
            x1={PADDING.left}
            x2={PADDING.left + plotWidth}
            y1={avgY}
            y2={avgY}
            stroke="#34d399"
            strokeWidth="1.2"
            strokeDasharray="5 4"
            opacity="0.7"
          />

          <path d={areaPath} fill="url(#usage-area)" />
          <path
            d={linePath}
            fill="none"
            stroke="url(#usage-line)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Peak marker */}
          {peakIndex >= 0 && points[peakIndex] ? (
            <g>
              <circle
                cx={points[peakIndex].x}
                cy={points[peakIndex].y}
                r="6"
                fill="#fef3c7"
                stroke="#f59e0b"
                strokeWidth="1.5"
              />
              <circle cx={points[peakIndex].x} cy={points[peakIndex].y} r="2" fill="#f59e0b" />
            </g>
          ) : null}

          {points.map((point, index) => (
            <g key={`label-${index}`}>
              {(index === 0 ||
                index === points.length - 1 ||
                index % Math.max(Math.floor(points.length / 6), 1) === 0) && (
                <text
                  x={point.x}
                  y={VIEW_HEIGHT - 18}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#64748b"
                >
                  {point.label}
                </text>
              )}
            </g>
          ))}

          {/* Invisible hit areas */}
          {points.map((point, index) => (
            <rect
              key={`hit-${index}`}
              x={point.x - plotWidth / Math.max(points.length, 1) / 2}
              y={PADDING.top}
              width={plotWidth / Math.max(points.length, 1)}
              height={plotHeight}
              fill="transparent"
              onPointerEnter={() => setHoverIndex(index)}
            />
          ))}

          {/* Hover indicator */}
          {activePoint ? (
            <g>
              <line
                x1={activePoint.x}
                x2={activePoint.x}
                y1={PADDING.top}
                y2={PADDING.top + plotHeight}
                stroke="#0284c7"
                strokeWidth="1"
                strokeDasharray="3 3"
                opacity="0.6"
              />
              <circle
                cx={activePoint.x}
                cy={activePoint.y}
                r="8"
                fill="#0ea5e9"
                opacity="0.18"
                filter="url(#usage-glow)"
              />
              <circle
                cx={activePoint.x}
                cy={activePoint.y}
                r="5"
                fill="#ffffff"
                stroke="#0284c7"
                strokeWidth="2.5"
              />

              {/* Tooltip */}
              <g transform={`translate(${tooltipX} ${tooltipY})`}>
                <rect
                  width={tooltipWidth}
                  height={tooltipHeight}
                  rx="10"
                  ry="10"
                  fill="#0f172a"
                  opacity="0.96"
                />
                <text x="12" y="20" fontSize="10" fill="#94a3b8" fontWeight="600">
                  {activePoint.label}
                </text>
                <text x="12" y="40" fontSize="14" fill="#ffffff" fontWeight="700">
                  {activePoint.tokens.toLocaleString('es-AR')} tokens
                </text>
                {typeof activePoint.requests === 'number' ? (
                  <text x="12" y="52" fontSize="9" fill="#cbd5f5">
                    {activePoint.requests.toLocaleString('es-AR')} requests
                  </text>
                ) : null}
              </g>
            </g>
          ) : null}
        </svg>
      </div>
    </div>
  );
}
