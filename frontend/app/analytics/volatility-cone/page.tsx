"use client";

import { useState, useEffect, useMemo } from 'react';
import VolatilityConeChart from '@/components/cockpit/charts/VolatilityConeChart';
import { useSearchParams } from 'next/navigation';
import { Calendar, RefreshCw } from 'lucide-react';
import SmartDateInput from '@/components/cockpit/SmartDateInput';

interface ConeStats {
    window: number;
    min: number;
    q25: number;
    median: number;
    q75: number;
    max: number;
}

interface CurrentPoint {
    days: number;
    iv: number;
    expiry: string;
    strike: number;
}

export default function VolatilityConePage() {
    const searchParams = useSearchParams();
    // Default to today or specific date... usually passed via query, or we pick a default in backend 
    // But here we might want a date picker? For now, hardcode or fetch latest?
    // Backend's get_volatility_cone requires 'date'.
    // Let's assume we want "today".

    const [date, setDate] = useState<string>(
        searchParams.get('date') || new Date().toISOString().split('T')[0]
    );

    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [availableDates, setAvailableDates] = useState<string[]>([]);

    const [progress, setProgress] = useState({ percent: 0, message: "" });

    // Poll for progress when loading
    useEffect(() => {
        if (!loading) return;

        const interval = setInterval(async () => {
            try {
                // Add timestamp to prevent caching. Try 127.0.0.1 to avoid localhost IPv6 issues.
                const res = await fetch(`http://127.0.0.1:8000/api/analytics/progress?t=${Date.now()}`);
                if (res.ok) {
                    const status = await res.json();

                    // Always update message if available
                    let pct = 0;
                    if (status.total > 0) {
                        pct = (status.current / status.total) * 100;
                    }

                    setProgress({
                        percent: Math.min(100, pct),
                        message: status.message || "加载数据中..."
                    });
                } else {
                    setProgress(p => ({ ...p, message: `Error: ${res.statusText}` }));
                }
            } catch (e: any) {
                // Show network error in UI
                setProgress(p => ({ ...p, message: `Connection Failed: ${e.message}` }));
            }
        }, 500);

        return () => clearInterval(interval);
    }, [loading]);

    const fetchData = async () => {
        setLoading(true);
        setProgress({ percent: 0, message: "Starting..." });
        setError(null);
        try {
            const res = await fetch(`http://localhost:8000/api/analytics/vol-cone?date=${date}&symbol=510050_SH`);
            if (!res.ok) throw new Error("Failed to fetch data");
            const json = await res.json();
            setData(json);
        } catch (err) {
            console.error(err);
            setError("无法获取数据，请检查后端服务");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [date]);

    // Fetch available dates
    useEffect(() => {
        const fetchDates = async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/data/dates?dataset_id=510050_SH`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.dates && Array.isArray(data.dates)) {
                        setAvailableDates(data.dates);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch dates", e);
            }
        };
        fetchDates();
    }, []);

    // Transform Data
    const chartData = useMemo(() => {
        if (!data || !data.cone || !data.cone.cone_curves) return [];

        const coneCurves: ConeStats[] = data.cone.cone_curves;
        const currentCurve: CurrentPoint[] = data.current_curve || [];

        // Map cone windows to chart data
        return coneCurves.map((c: any) => {
            // Interpolate Current IV for this window (c.window)
            let currentIV = 0;

            // Priority 1: Use Backend Provided IV (Precise Interpolation)
            if (c.current_iv && c.current_iv > 0) {
                currentIV = c.current_iv;
            }
            // Priority 2: Frontend Interpolation (Fallback)
            else if (currentCurve.length > 1) {
                // Find surrounding points
                let prev = currentCurve[0];
                let next = currentCurve[currentCurve.length - 1];

                for (let i = 0; i < currentCurve.length; i++) {
                    if (currentCurve[i].days <= c.window) prev = currentCurve[i];
                    else {
                        next = currentCurve[i];
                        break;
                    }
                }

                if (prev.days === next.days) {
                    currentIV = prev.iv;
                } else {
                    // Linear Interp
                    const ratio = (c.window - prev.days) / (next.days - prev.days);
                    currentIV = prev.iv + (next.iv - prev.iv) * ratio;
                }
            } else if (currentCurve.length === 1) {
                currentIV = currentCurve[0].iv;
            }

            // Calculate Percentile Rank for Today
            // (Current - Min) / (Max - Min)
            let rank = 50;
            if (currentIV !== null && c.max > c.min) {
                rank = ((currentIV - c.min) / (c.max - c.min)) * 100;
            }
            rank = Math.max(0, Math.min(100, rank));

            return {
                dte: c.window,
                current_iv: currentIV, // Can be null
                percentile_rank: rank,
                min: c.min,
                p25: c.q25,
                median: c.median,
                p75: c.q75,
                max: c.max
            };
        });
    }, [data]);

    return (
        <div className="w-full h-screen bg-[#0e1116] text-white p-6 overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
                        波动率锥分析 (Volatility Cone)
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">
                        对比当前隐含波动率(IV)与历史实现波动率(HV)的分位水平
                    </p>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 bg-[#161920] px-3 py-1.5 rounded-lg border border-gray-800 min-w-[220px]">
                        <Calendar className="w-4 h-4 text-gray-400 shrink-0" />
                        <div className="flex-1">
                            <SmartDateInput
                                label=""
                                value={date}
                                onChange={setDate}
                                validDates={availableDates}
                            />
                        </div>
                    </div>
                    <button
                        onClick={fetchData}
                        className="p-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 bg-[#13161d] rounded-xl border border-gray-800 p-4 shadow-xl overflow-hidden">
                {error ? (
                    <div className="h-full flex items-center justify-center text-red-400">
                        {error}
                    </div>
                ) : (
                    loading ? (
                        <div className="flex flex-col items-center justify-center h-full max-w-md mx-auto">
                            <div className="w-full bg-gray-800 rounded-full h-2 mb-4 overflow-hidden">
                                <div
                                    className="bg-indigo-500 h-2 rounded-full transition-all duration-300 ease-out"
                                    style={{ width: `${progress.percent}%` }}
                                />
                            </div>
                            <div className="flex items-center justify-between w-full text-xs text-gray-400">
                                <span>{progress.message || "加载数据中..."}</span>
                                <span>{Math.round(progress.percent)}%</span>
                            </div>
                        </div>
                    ) : (
                        <VolatilityConeChart data={chartData} loading={loading} />
                    )
                )}
            </div>

            {/* Context Info */}
            <div className="mt-4 grid grid-cols-4 gap-4">
                <div className="bg-[#161920] p-3 rounded-lg border border-gray-800">
                    <div className="text-xs text-gray-500">标的数据</div>
                    <div className="font-mono text-indigo-400">510050.SH</div>
                </div>
                <div className="bg-[#161920] p-3 rounded-lg border border-gray-800">
                    <div className="text-xs text-gray-500">参考标的价格</div>
                    <div className="font-mono text-white">
                        {data?.spot_ref ? data.spot_ref.toFixed(4) : '-'}
                    </div>
                </div>
                <div className="bg-[#161920] p-3 rounded-lg border border-gray-800">
                    <div className="text-xs text-gray-500">回看周期</div>
                    <div className="font-mono text-white">5 Years</div>
                </div>
                <div className="bg-[#161920] p-3 rounded-lg border border-gray-800">
                    <div className="text-xs text-gray-500">最新收盘价</div>
                    <div className="font-mono text-white">
                        {data?.cone?.latest_price ? data.cone.latest_price.toFixed(4) : '-'}
                    </div>
                </div>
            </div>
        </div >
    );
}
