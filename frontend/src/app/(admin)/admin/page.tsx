"use client";

import { useEffect, useState } from "react";
import { 
    Users, 
    Layout, 
    FileText, 
    Send, 
    CreditCard, 
    Settings, 
    Save, 
    RefreshCcw,
    DollarSign,
    AlertCircle,
    Check,
    X
} from "lucide-react";
import { 
    buildHeaders, 
    fetchPendingPayments, 
    confirmPayment 
} from "@/lib/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://34.64.50.56";

interface AdminStats {
    total_users: number;
    total_blogs: number;
    total_posts: number;
    published_posts: number;
    total_credits_used: number;
    pending_deposits: number;
}

interface SystemPolicy {
    signup_bonus: number;
    referral_bonus: number;
    cost_short: number;
    cost_medium: number;
    cost_long: number;
    cost_image: number;
}

export default function AdminDashboard() {
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [policy, setPolicy] = useState<SystemPolicy | null>(null);
    const [pendingPayments, setPendingPayments] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // 수동 지급 폼 상태
    const [grantForm, setGrantForm] = useState({
        user_email: "",
        amount: 0,
        reason: "입금 확인 (수동)"
    });
    const [grantLoading, setGrantLoading] = useState(false);
    const [grantMessage, setGrantMessage] = useState("");

    const fetchData = async () => {
        setLoading(true);
        try {
            const [statsRes, policyRes, pendingRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/v1/admin/stats`, { headers: buildHeaders() }),
                fetch(`${API_BASE_URL}/api/v1/admin/policy`, { headers: buildHeaders() }),
                fetchPendingPayments()
            ]);

            if (statsRes.ok) setStats(await statsRes.json());
            if (policyRes.ok) setPolicy(await policyRes.json());
            setPendingPayments(pendingRes || []);
        } catch (err) {
            setError("데이터를 불러오는데 실패했습니다.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleGrantCredit = async (e: React.FormEvent) => {
        e.preventDefault();
        setGrantLoading(true);
        setGrantMessage("");
        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/admin/credits/manual-grant`, {
                method: "POST",
                headers: buildHeaders(),
                body: JSON.stringify(grantForm)
            });
            if (res.ok) {
                setGrantMessage("크레딧이 성공적으로 지급되었습니다.");
                setGrantForm({ user_email: "", amount: 0, reason: "입금 확인 (수동)" });
                fetchData(); // 스탯 갱신
            } else {
                const data = await res.json();
                setGrantMessage(`실패: ${data.detail || "알 수 없는 오류"}`);
            }
        } catch (err) {
            setGrantMessage("지급 중 오류가 발생했습니다.");
        } finally {
            setGrantLoading(false);
        }
    };

    const handleUpdatePolicy = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!policy) return;
        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/admin/policy`, {
                method: "PUT",
                headers: buildHeaders(),
                body: JSON.stringify(policy)
            });
            if (res.ok) {
                alert("정책이 업데이트되었습니다.");
            } else {
                alert("정책 업데이트에 실패했습니다.");
            }
        } catch (err) {
            alert("오류가 발생했습니다.");
        }
    };

    const handleConfirmPayment = async (requestId: number, approve: boolean) => {
        if (!confirm(approve ? "입금을 승인하고 크레딧을 지급하시겠습니까?" : "요청을 거절하시겠습니까?")) return;
        try {
            await confirmPayment(requestId, approve);
            alert(approve ? "승인되었습니다." : "거절되었습니다.");
            fetchData();
        } catch (err) {
            alert("처리에 실패했습니다.");
        }
    };

    if (loading && !stats) {
        return <div className="p-8 flex justify-center items-center h-screen bg-slate-50">
            <RefreshCcw className="w-8 h-8 animate-spin text-slate-400" />
        </div>;
    }

    return (
        <div className="p-8 bg-slate-50 min-h-screen text-slate-900">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">관리자 백오피스</h1>
                    <p className="text-slate-500">시스템 현황 및 정책 관리</p>
                </div>
                <button 
                    onClick={fetchData}
                    className="p-2 rounded-full hover:bg-slate-200 transition"
                >
                    <RefreshCcw className="w-5 h-5 text-slate-600" />
                </button>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard icon={<Users className="w-6 h-6" />} label="전체 사용자" value={stats?.total_users || 0} color="blue" />
                <StatCard icon={<Layout className="w-6 h-6" />} label="전체 블로그" value={stats?.total_blogs || 0} color="emerald" />
                <StatCard icon={<FileText className="w-6 h-6" />} label="발행된 포스트" value={stats?.published_posts || 0} color="cyan" />
                <StatCard icon={<CreditCard className="w-6 h-6" />} label="전체 사용 크레딧" value={stats?.total_credits_used || 0} color="amber" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Manual Credit Grant */}
                <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                    <div className="flex items-center gap-2 mb-6">
                        <DollarSign className="w-5 h-5 text-emerald-500" />
                        <h2 className="text-xl font-bold">수동 크레딧 지급</h2>
                    </div>
                    <form onSubmit={handleGrantCredit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">사용자 이메일</label>
                            <input 
                                type="email" 
                                required
                                value={grantForm.user_email}
                                onChange={e => setGrantForm({...grantForm, user_email: e.target.value})}
                                className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition"
                                placeholder="user@example.com"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">지급 수량</label>
                                <input 
                                    type="number" 
                                    required
                                    value={grantForm.amount}
                                    onChange={e => setGrantForm({...grantForm, amount: Number(e.target.value)})}
                                    className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">사유</label>
                                <input 
                                    type="text" 
                                    required
                                    value={grantForm.reason}
                                    onChange={e => setGrantForm({...grantForm, reason: e.target.value})}
                                    className="w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition"
                                />
                            </div>
                        </div>
                        <button 
                            type="submit"
                            disabled={grantLoading}
                            className="w-full bg-slate-900 text-white font-bold py-3 rounded-2xl hover:bg-slate-800 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {grantLoading ? <RefreshCcw className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                            크레딧 지급하기
                        </button>
                        {grantMessage && (
                            <p className={`text-sm text-center ${grantMessage.includes("성공") ? "text-emerald-600" : "text-rose-600"}`}>
                                {grantMessage}
                            </p>
                        )}
                    </form>
                </div>

                {/* System Policy */}
                <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                    <div className="flex items-center gap-2 mb-6">
                        <Settings className="w-5 h-5 text-slate-500" />
                        <h2 className="text-xl font-bold">시스템 정책 관리</h2>
                    </div>
                    {policy && (
                        <form onSubmit={handleUpdatePolicy} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <PolicyInput label="가입 보너스" value={policy.signup_bonus} onChange={v => setPolicy({...policy, signup_bonus: v})} />
                                <PolicyInput label="추천인 보너스" value={policy.referral_bonus} onChange={v => setPolicy({...policy, referral_bonus: v})} />
                                <PolicyInput label="짧은 글 소모" value={policy.cost_short} onChange={v => setPolicy({...policy, cost_short: v})} />
                                <PolicyInput label="중간 글 소모" value={policy.cost_medium} onChange={v => setPolicy({...policy, cost_medium: v})} />
                                <PolicyInput label="긴 글 소모" value={policy.cost_long} onChange={v => setPolicy({...policy, cost_long: v})} />
                                <PolicyInput label="이미지 장당 소모" value={policy.cost_image} onChange={v => setPolicy({...policy, cost_image: v})} />
                            </div>
                            <button 
                                type="submit"
                                className="w-full bg-emerald-500 text-white font-bold py-3 rounded-2xl hover:bg-emerald-600 flex items-center justify-center gap-2"
                            >
                                <Save className="w-5 h-5" />
                                정책 저장하기
                            </button>
                        </form>
                    )}
                </div>
            </div>

            {/* Pending Deposits List */}
            <div className="mt-8 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-amber-500" />
                        <h2 className="text-xl font-bold">입금 대기 목록</h2>
                    </div>
                    <span className="bg-amber-100 text-amber-700 px-3 py-1 rounded-full text-xs font-bold">
                        {pendingPayments.length}건 대기 중
                    </span>
                </div>
                
                {pendingPayments.length === 0 ? (
                    <div className="text-center py-12 text-slate-400">
                        <p>현재 대기 중인 입금 확인 요청이 없습니다.</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead>
                                <tr className="text-slate-500 border-b border-slate-100">
                                    <th className="pb-3">일시</th>
                                    <th className="pb-3">입금자명</th>
                                    <th className="pb-3">금액</th>
                                    <th className="pb-3">요청 크레딧</th>
                                    <th className="pb-3 text-right">관리</th>
                                </tr>
                            </thead>
                            <tbody>
                                {pendingPayments.map((req) => (
                                    <tr key={req.id} className="border-b border-slate-50 last:border-0">
                                        <td className="py-4 text-slate-500">{new Date(req.created_at).toLocaleString()}</td>
                                        <td className="py-4 font-bold">{req.depositor_name}</td>
                                        <td className="py-4 font-mono text-emerald-600">₩{req.amount.toLocaleString()}</td>
                                        <td className="py-4 font-mono text-blue-600">{req.requested_credits.toLocaleString()} C</td>
                                        <td className="py-4 text-right">
                                            <div className="flex justify-end gap-2">
                                                <button 
                                                    onClick={() => handleConfirmPayment(req.id, true)}
                                                    className="p-2 bg-emerald-50 text-emerald-600 rounded-xl hover:bg-emerald-100 transition"
                                                    title="승인"
                                                >
                                                    <Check className="w-5 h-5" />
                                                </button>
                                                <button 
                                                    onClick={() => handleConfirmPayment(req.id, false)}
                                                    className="p-2 bg-rose-50 text-rose-600 rounded-xl hover:bg-rose-100 transition"
                                                    title="거절"
                                                >
                                                    <X className="w-5 h-5" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

function StatCard({ icon, label, value, color }: { icon: any, label: string, value: number, color: string }) {
    const colors: any = {
        blue: "bg-blue-50 text-blue-600",
        emerald: "bg-emerald-50 text-emerald-600",
        cyan: "bg-cyan-50 text-cyan-600",
        amber: "bg-amber-50 text-amber-600",
    };
    return (
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className={`p-3 rounded-2xl ${colors[color]}`}>{icon}</div>
            <div>
                <p className="text-sm font-medium text-slate-500">{label}</p>
                <p className="text-2xl font-bold text-slate-900">{value.toLocaleString()}</p>
            </div>
        </div>
    );
}

function PolicyInput({ label, value, onChange }: { label: string, value: number, onChange: (v: number) => void }) {
    return (
        <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">{label}</label>
            <input 
                type="number" 
                value={value}
                onChange={e => onChange(Number(e.target.value))}
                className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-cyan-500 outline-none transition text-sm"
            />
        </div>
    );
}
