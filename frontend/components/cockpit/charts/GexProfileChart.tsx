
"use client";

import { useMemo } from 'react';
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
    ReferenceLine,
    Cell,
    Legend
} from 'recharts';

interface GexProfileData {
    strike: number;
    gex_dollar: number;
    gex_raw: number;
}

interface GexProfileChartProps {
    data: GexProfileData[] | null;
    spotPrice: number;
    zeroGammaPrice?: number;
    loading?: boolean;
}

const formatCurrencyWithUnit = (value: number, unitDivisor: number, unitLabel: string) => {
    if (value === 0) return '0';
    return `${(value / unitDivisor).toFixed(unitDivisor === 1 ? 0 : 2)}${unitLabel}`;
};

const FlipLabel = (props: any) => {
    const { viewBox, value } = props;
    // Calculate X position based on value and chart domain if available, 
    // or rely on Recharts positioning if it passes 'x' and 'y'.
    // Recharts ReferenceLine label receives: { x, y, value, viewBox, ... }

    // Fallback if x is missing (sometimes happens in some Recharts versions for custom labels on ReferenceLine)
    // We can try to calculate it from viewBox and domain if implied.
    // But let's trust 'x' first.
    const x = props.x;
    const y = props.viewBox.y; // Top of chart area

    if (typeof x !== 'number') return null;

    return (
        <g transform={`translate(${x}, ${y})`}>
            {/* Glow behind */}
            <rect x="-40" y="-15" width="80" height="24" rx="12" fill="#8B5CF6" filter="url(#neonGlow)" opacity="0.5" />
            {/* Main Capsule */}
            <rect x="-40" y="-15" width="80" height="24" rx="12" fill="#1e1b4b" stroke="#8B5CF6" strokeWidth="1.5" />
            {/* Text */}
            <text x="0" y="2" textAnchor="middle" fill="#FFFFFF" fontSize="10" fontWeight="bold" dy=".3em" style={{ textShadow: '0 0 5px #8B5CF6' }}>
                FLIP LEVEL
            </text>
        </g>
    );
};

export default function GexProfileChart({ data, spotPrice, zeroGammaPrice, loading }: GexProfileChartProps) {
    const { processedData, yAxisConfig } = useMemo(() => {
        if (!data || data.length === 0) return { processedData: [], yAxisConfig: { divisor: 1, unit: '' } };

        const sorted = [...data].sort((a, b) => a.strike - b.strike);

        // Determine global Y-axis unit based on max value
        const maxVal = Math.max(...data.map(d => Math.abs(d.gex_dollar)));
        let divisor = 1;
        let unit = '';

        if (maxVal >= 100000000) {
            divisor = 100000000;
            unit = '亿';
        } else if (maxVal >= 10000) {
            divisor = 10000;
            unit = '万';
        }

        return { processedData: sorted, yAxisConfig: { divisor, unit } };
    }, [data]);

    if (loading) {
        return (
            <div className="h-[400px] w-full flex items-center justify-center text-[var(--text-muted)] animate-pulse">
                Calculating Gamma Exposure...
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="h-[400px] w-full flex items-center justify-center text-[var(--text-muted)]">
                No GEX Data Available
            </div>
        );
    }

    // Calculate domain padding for Spot line visibility
    const minStrike = Math.min(...processedData.map(d => d.strike), spotPrice);
    const maxStrike = Math.max(...processedData.map(d => d.strike), spotPrice);
    const padding = (maxStrike - minStrike) * 0.05;

    return (
        <div className="w-full h-[400px] bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-primary)]">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-[var(--accent-primary)] font-bold flex items-center gap-2">
                    Gamma Exposure Profile (GEX)
                </h3>
                <div className="text-xs text-[var(--text-muted)]">
                    Spot: <span className="text-[var(--accent-info)] font-mono">{spotPrice.toFixed(4)}</span>
                </div>
            </div>

            <ResponsiveContainer width="100%" height={340}>
                <BarChart
                    data={processedData}
                    margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
                >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} vertical={false} />

                    <XAxis
                        dataKey="strike"
                        type="number"
                        domain={[minStrike - padding, maxStrike + padding]}
                        tickCount={12}
                        tickFormatter={(val) => val.toFixed(2)}
                        tick={{ fill: 'var(--text-secondary)', fontSize: 10 }}
                        label={{ value: 'Strike Price', position: 'insideBottom', offset: -10, fill: 'var(--text-muted)', fontSize: 12 }}
                    />

                    <YAxis
                        tickFormatter={(val) => formatCurrencyWithUnit(val, yAxisConfig.divisor, yAxisConfig.unit)}
                        tick={{ fill: 'var(--text-secondary)', fontSize: 10 }}
                        width={80}
                    />

                    <Tooltip
                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                        contentStyle={{
                            backgroundColor: 'var(--bg-primary)',
                            borderColor: 'var(--border-primary)',
                            color: 'var(--text-primary)'
                        }}
                        formatter={(value: any) => [
                            <span key="val" style={{ color: value >= 0 ? '#10B981' : '#EF4444', fontWeight: 'bold' }}>
                                {formatCurrencyWithUnit(Number(value), yAxisConfig.divisor, yAxisConfig.unit)}
                            </span>,
                            "Net GEX"
                        ]}
                        labelFormatter={(label) => `Strike: ${Number(label).toFixed(3)}`}
                    />

                    <defs>
                        <linearGradient id="neonBeam" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#8B5CF6" stopOpacity={0.9} />
                            <stop offset="50%" stopColor="#8B5CF6" stopOpacity={0.5} />
                            <stop offset="100%" stopColor="#06B6D4" stopOpacity={0.1} />
                        </linearGradient>
                        <filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>

                    <ReferenceLine x={spotPrice} stroke="var(--accent-info)" strokeDasharray="3 3" label={{ position: 'top', value: 'Spot', fill: 'var(--accent-info)', fontSize: 10 }} />

                    {zeroGammaPrice && (
                        <ReferenceLine
                            x={zeroGammaPrice}
                            stroke="url(#neonBeam)"
                            strokeWidth={4}
                            strokeLinecap="round"
                            style={{ filter: 'url(#neonGlow)' }}
                            label={<FlipLabel value={zeroGammaPrice} />}
                        />
                    )}

                    <ReferenceLine y={0} stroke="var(--border-primary)" />

                    <Bar dataKey="gex_dollar" name="Net GEX">
                        {processedData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={entry.gex_dollar >= 0 ? '#10B981' : '#EF4444'}
                                fillOpacity={0.8}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
