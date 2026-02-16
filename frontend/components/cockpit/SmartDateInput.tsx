
import { useState, useEffect, useRef } from 'react';
import { Calendar, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface SmartDateInputProps {
    label: string;
    value: string;
    onChange: (date: string) => void;
    validDates: string[];
    disabled?: boolean;
}

export default function SmartDateInput({
    label,
    value,
    onChange,
    validDates,
    disabled = false
}: SmartDateInputProps) {
    const [status, setStatus] = useState<'valid' | 'invalid' | 'corrected' | 'loading'>('loading');
    const [message, setMessage] = useState('');

    // Update status when value or validDates changes
    useEffect(() => {
        if (!validDates || validDates.length === 0) {
            setStatus('loading');
            return;
        }

        if (validDates.includes(value)) {
            setStatus('valid');
            setMessage('');
        } else {
            setStatus('invalid');
            setMessage('该日期无数据');
        }
    }, [value, validDates]);

    const handleBlur = () => {
        if (!validDates || validDates.length === 0) return;

        if (!validDates.includes(value)) {
            // Find nearest date
            const targetTime = new Date(value).getTime();
            let closest = validDates[0];
            let minDiff = Math.abs(new Date(closest).getTime() - targetTime);

            for (const d of validDates) {
                const diff = Math.abs(new Date(d).getTime() - targetTime);
                if (diff < minDiff) {
                    minDiff = diff;
                    closest = d;
                }
            }

            if (closest !== value) {
                onChange(closest);
                setStatus('corrected');
                setMessage(`已自动调整至最近交易日: ${closest}`);

                // Clear corrected status after 3 seconds
                setTimeout(() => {
                    if (validDates.includes(closest)) { // Double check
                        setStatus('valid');
                        setMessage('');
                    }
                }, 3000);
            }
        }
    };

    const minDate = validDates.length > 0 ? validDates[0] : undefined;
    const maxDate = validDates.length > 0 ? validDates[validDates.length - 1] : undefined;

    return (
        <div className="space-y-1">
            <div className="flex justify-between items-center">
                <label className="label-mono text-xs">{label}</label>
                {status === 'corrected' && (
                    <span className="text-[10px] text-[var(--accent-warning)] animate-pulse">{message}</span>
                )}
                {status === 'invalid' && (
                    <span className="text-[10px] text-[var(--accent-danger)]">无效日期</span>
                )}
            </div>

            <div className="relative group">
                <input
                    type="date"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onBlur={handleBlur}
                    min={minDate}
                    max={maxDate}
                    disabled={disabled}
                    className={`input-field text-sm pr-8 w-full ${status === 'corrected' ? 'border-[var(--accent-warning)] text-[var(--accent-warning)]' :
                            status === 'valid' ? 'border-[var(--accent-success)]/50' :
                                ''
                        }`}
                />

                <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                    {status === 'valid' && <CheckCircle className="w-3.5 h-3.5 text-[var(--accent-success)]" />}
                    {status === 'corrected' && <AlertTriangle className="w-3.5 h-3.5 text-[var(--accent-warning)]" />}
                    {status === 'invalid' && <XCircle className="w-3.5 h-3.5 text-[var(--accent-danger)]" />}
                </div>
            </div>
        </div>
    );
}
