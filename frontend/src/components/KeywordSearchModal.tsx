"use client";

import { useState } from "react";
import { X, Search, Loader2 } from "lucide-react";

interface Keyword {
    keyword: string;
    monthly_search: number;
    competition: number;
    priority: number;
}

interface KeywordSearchModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (keywords: string[]) => void;
}

export default function KeywordSearchModal({
    isOpen,
    onClose,
    onSelect,
}: KeywordSearchModalProps) {
    const [seedKeyword, setSeedKeyword] = useState("");
    const [keywords, setKeywords] = useState<Keyword[]>([]);
    const [selectedKeywords, setSelectedKeywords] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://34.64.50.56";

    const handleSearch = async () => {
        if (!seedKeyword.trim()) {
            setError("키워드를 입력해주세요");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const token = localStorage.getItem("token");
            const res = await fetch(
                `${API_BASE_URL}/api/v1/keywords/search?seed=${encodeURIComponent(seedKeyword)}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!res.ok) {
                throw new Error("키워드 검색에 실패했습니다");
            }

            const data = await res.json();
            setKeywords(data);
        } catch (err) {
            setError((err as Error).message);
        } finally {
            setLoading(false);
        }
    };

    const toggleKeyword = (keyword: string) => {
        const newSelected = new Set(selectedKeywords);
        if (newSelected.has(keyword)) {
            newSelected.delete(keyword);
        } else {
            newSelected.add(keyword);
        }
        setSelectedKeywords(newSelected);
    };

    const handleConfirm = () => {
        onSelect(Array.from(selectedKeywords));
        onClose();
        // 초기화
        setSeedKeyword("");
        setKeywords([]);
        setSelectedKeywords(new Set());
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-slate-950 rounded-3xl border border-slate-800 max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <h2 className="text-2xl font-bold text-white">키워드 리서치</h2>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-white transition"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Search */}
                <div className="p-6 border-b border-slate-800">
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={seedKeyword}
                            onChange={(e) => setSeedKeyword(e.target.value)}
                            onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                            placeholder="시드 키워드 입력 (예: AI 마케팅)"
                            className="flex-1 rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                        />
                        <button
                            onClick={handleSearch}
                            disabled={loading}
                            className="rounded-2xl bg-cyan-500 px-6 py-3 font-semibold text-white hover:bg-cyan-600 disabled:opacity-50 flex items-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    검색 중...
                                </>
                            ) : (
                                <>
                                    <Search className="w-5 h-5" />
                                    검색
                                </>
                            )}
                        </button>
                    </div>
                    {error && (
                        <p className="mt-2 text-sm text-red-400">{error}</p>
                    )}
                </div>

                {/* Results */}
                <div className="flex-1 overflow-y-auto p-6">
                    {keywords.length === 0 ? (
                        <div className="text-center text-slate-400 py-12">
                            <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <p>키워드를 검색하여 연관 키워드를 찾아보세요</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            <p className="text-sm text-slate-400 mb-4">
                                {keywords.length}개의 키워드를 찾았습니다 (우선순위 순)
                            </p>
                            {keywords.map((kw, idx) => (
                                <label
                                    key={idx}
                                    className={`flex items-center justify-between p-4 rounded-2xl border cursor-pointer transition ${selectedKeywords.has(kw.keyword)
                                            ? "border-cyan-400 bg-cyan-400/10"
                                            : "border-slate-800 bg-slate-900 hover:border-slate-700"
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="checkbox"
                                            checked={selectedKeywords.has(kw.keyword)}
                                            onChange={() => toggleKeyword(kw.keyword)}
                                            className="w-5 h-5 rounded border-slate-700 text-cyan-500 focus:ring-cyan-500"
                                        />
                                        <div>
                                            <p className="font-semibold text-white">{kw.keyword}</p>
                                            <p className="text-xs text-slate-400">
                                                월간 검색: {kw.monthly_search.toLocaleString()} · 경쟁도: {kw.competition} · 우선순위: {kw.priority.toFixed(2)}
                                            </p>
                                        </div>
                                    </div>
                                </label>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-slate-800 flex items-center justify-between">
                    <p className="text-sm text-slate-400">
                        {selectedKeywords.size}개 선택됨
                    </p>
                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="rounded-2xl border border-slate-700 px-6 py-3 font-semibold text-slate-300 hover:border-slate-600"
                        >
                            취소
                        </button>
                        <button
                            onClick={handleConfirm}
                            disabled={selectedKeywords.size === 0}
                            className="rounded-2xl bg-emerald-500 px-6 py-3 font-semibold text-white hover:bg-emerald-600 disabled:opacity-50"
                        >
                            선택 완료
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
