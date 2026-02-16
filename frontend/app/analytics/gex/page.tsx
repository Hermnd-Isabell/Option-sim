
"use client";

import { useState, useEffect } from 'react';
import GexProfileChart from '@/components/cockpit/charts/GexProfileChart';
import { useSearchParams } from 'next/navigation';
import { RefreshCw, BarChart2 } from 'lucide-react';
import SmartDateInput from '@/components/cockpit/SmartDateInput';

export default function GexProfilePage() {
    const searchParams = useSearchParams();
    // Start with empty date, wait for availableDates
    const [date, setDate] = useState<string>(
        searchParams.get('date') || ''
    );
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<any>(null); // { date, spot_price, profile: [] }
    const [error, setError] = useState<string | null>(null);
    const [availableDates, setAvailableDates] = useState<string[]>([]);

    // 1. Fetch dates first
    useEffect(() => {
        const fetchDates = async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/data/dates?dataset_id=510050_SH`);
                if (res.ok) {
                    const d = await res.json();
                    if (d.dates && d.dates.length > 0) {
                        setAvailableDates(d.dates);
                        // If no date selected (or empty), use the latest one
                        if (!date) {
                            setDate(d.dates[d.dates.length - 1]);
                        }
                    } else {
                        // If no dates, maybe fallback to today but likely error
                        setError("No data available");
                    }
                }
            } catch (e) {
                console.error("Failed to fetch dates", e);
            }
        };
        fetchDates();
    }, []);

    // 2. Fetch data when date is set
    const fetchData = async () => {
        if (!date) return;

        setLoading(true);
        setError(null);
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

            const res = await fetch(`http://localhost:8000/api/data/gex-profile?date=${date}&dataset_id=510050_SH`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!res.ok) {
                const errJson = await res.json().catch(() => ({}));
                throw new Error(errJson.detail || "Failed to fetch GEX data");
            }
            const json = await res.json();
            setData(json);
        } catch (err: any) {
            console.error(err);
            if (err.name === 'AbortError') {
                setError("请求超时 (Timeout) - 计算耗时过长");
            } else {
                setError(err.message || "无法获取数据");
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (date) fetchData();
    }, [date]);

    const spot = data?.spot_price || 0;
    const zeroGamma = data?.zero_gamma || 0;
    const expSummary = data?.expiration_summary || null;
    const profile = data?.profile || [];
    const totalGex = profile.reduce((acc: number, curr: any) => acc + (curr.gex_dollar || 0), 0);

    return (
        <div className="h-full flex flex-col space-y-4 p-4 overflow-y-auto w-full">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-[var(--accent-primary)]/10 rounded-lg">
                        <BarChart2 className="w-6 h-6 text-[var(--accent-primary)]" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-[var(--text-primary)]">Gamma Exposure (GEX)</h1>
                        <p className="text-xs text-[var(--text-muted)]">
                            Market Maker Gamma Exposure Profile
                            {expSummary && (
                                <span className="ml-2 px-2 py-0.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
                                    {expSummary.count} Expirations ({expSummary.min_expiry} ~ {expSummary.max_expiry})
                                </span>
                            )}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <SmartDateInput
                        label="Date"
                        value={date}
                        onChange={setDate}
                        validDates={availableDates}
                    />
                    <button onClick={fetchData} className="p-2 bg-[var(--bg-secondary)] rounded hover:bg-[var(--bg-tertiary)] transition-colors" disabled={loading}>
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-[var(--accent-danger)]/10 text-[var(--accent-danger)] border border-[var(--accent-danger)]/20 rounded-lg flex items-center gap-2">
                    ⚠️ {error}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                {/* Left: Stats */}
                <div className="lg:col-span-1 space-y-4">
                    <StatCard label="Total Net GEX" value={totalGex} isCurrency />
                    <StatCard label="Spot Price" value={spot} />
                    <StatCard
                        label="Zero Gamma Flip"
                        value={zeroGamma ? `¥${zeroGamma.toFixed(4)}` : "-"}
                        subLabel="Net GEX Transition"
                    />

                    <div className="glass-card p-4 space-y-2">
                        <h3 className="text-sm font-bold text-[var(--text-secondary)]">Interpretation</h3>
                        <div className="space-y-2 text-xs text-[var(--text-muted)]">
                            <div className="flex items-start gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500 mt-0.5 shrink-0"></div>
                                <p><strong>Negative Gamma (Red):</strong> Market Makers are "Short Gamma". They convert delta by selling as price falls and buying as price rises, amplifying volatility.</p>
                            </div>
                            <div className="flex items-start gap-2">
                                <div className="w-3 h-3 rounded-full bg-green-500 mt-0.5 shrink-0"></div>
                                <p><strong>Positive Gamma (Green):</strong> Market Makers are "Long Gamma". They trade against the trend (buy low, sell high), suppressing volatility.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Chart */}
                <div className="lg:col-span-3">
                    <GexProfileChart
                        data={profile}
                        spotPrice={spot}
                        zeroGammaPrice={zeroGamma}
                        loading={loading}
                    />
                </div>
            </div>
        </div>
    );
}

const StatCard = ({ label, value, isCurrency = false }: any) => {
    let displayValue = value;

    if (typeof value === 'number') {
        if (isCurrency) {
            const abs = Math.abs(value);
            if (abs >= 100000000) displayValue = `¥${(value / 100000000).toFixed(2)}亿`;
            else if (abs >= 10000) displayValue = `¥${(value / 10000).toFixed(2)}万`;
            else displayValue = `¥${value.toFixed(0)}`;
        } else {
            displayValue = value.toFixed(4);
        }
    }

    // Color for GEX
    let colorClass = "text-[var(--text-primary)]";
    if (isCurrency && typeof value === 'number') {
        colorClass = value >= 0 ? "text-[#10B981]" : "text-[#EF4444]";
    }

    return (
        <div className="glass-card p-4 flex flex-col items-center justify-center border border-[var(--border-primary)]">
            <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">{label}</span>
            <span className={`text-2xl font-sans font-bold ${colorClass}`}>{displayValue}</span>
        </div>
    );
}
