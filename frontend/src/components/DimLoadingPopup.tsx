"use client";

import { useEffect, useState } from "react";
import { Loader2, CheckCircle, XCircle } from "lucide-react";

interface DimLoadingPopupProps {
    isOpen: boolean;
    logs: string[];
    status?: "loading" | "success" | "error";
    onClose?: () => void;
}

export default function DimLoadingPopup({
    isOpen,
    logs,
    status = "loading",
    onClose,
}: DimLoadingPopupProps) {
    const [displayedLogs, setDisplayedLogs] = useState<string[]>([]);

    useEffect(() => {
        if (isOpen) {
            setDisplayedLogs(logs);
        }
    }, [logs, isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
            <div className="bg-slate-950 rounded-3xl border border-slate-800 max-w-2xl w-full max-h-[70vh] overflow-hidden flex flex-col shadow-2xl">
                {/* Header */}
                <div className="p-6 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                        {status === "loading" && (
                            <>
                                <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
                                <h2 className="text-xl font-bold text-white">생성 진행 중...</h2>
                            </>
                        )}
                        {status === "success" && (
                            <>
                                <CheckCircle className="w-6 h-6 text-emerald-400" />
                                <h2 className="text-xl font-bold text-white">생성 완료!</h2>
                            </>
                        )}
                        {status === "error" && (
                            <>
                                <XCircle className="w-6 h-6 text-red-400" />
                                <h2 className="text-xl font-bold text-white">오류 발생</h2>
                            </>
                        )}
                    </div>
                </div>

                {/* Logs */}
                <div className="flex-1 overflow-y-auto p-6 bg-slate-900/50">
                    <div className="space-y-2 font-mono text-sm">
                        {displayedLogs.length === 0 ? (
                            <p className="text-slate-500">로그를 기다리는 중...</p>
                        ) : (
                            displayedLogs.map((log, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-start gap-2 text-slate-300 animate-fadeIn"
                                >
                                    <span className="text-slate-600 select-none">
                                        [{new Date().toLocaleTimeString()}]
                                    </span>
                                    <span className="flex-1">{log}</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Footer */}
                {(status === "success" || status === "error") && onClose && (
                    <div className="p-6 border-t border-slate-800">
                        <button
                            onClick={onClose}
                            className="w-full rounded-2xl bg-cyan-500 px-6 py-3 font-semibold text-white hover:bg-cyan-600 transition"
                        >
                            닫기
                        </button>
                    </div>
                )}

                {/* Progress indicator for loading state */}
                {status === "loading" && (
                    <div className="px-6 pb-6">
                        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 animate-pulse" style={{ width: "60%" }} />
                        </div>
                        <p className="text-xs text-slate-400 mt-2 text-center">
                            AI가 콘텐츠를 생성하고 있습니다...
                        </p>
                    </div>
                )}
            </div>

            <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
        </div>
    );
}
